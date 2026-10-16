"""
Data extraction module for Personal Finance Tracker.
This module handles extracting and normalizing data from CSV files only.
Specifically designed for HDFC Bank statement CSV format.
"""

import os
import pandas as pd
import re
import json
import tempfile
from datetime import datetime
import numpy as np
from typing import Optional, List


SUPPORTED_STATEMENT_EXTENSIONS = {'.csv', '.xls', '.xlsx'}
SAMPLE_STATEMENT_PREFIXES = ('synthetic_', 'test_')
ACTIVE_STATEMENTS_MANIFEST = 'active_statements.json'

DATE_COLUMNS = ('transactiondate', 'trandate', 'transdate', 'txndate', 'date', 'postingdate', 'valuedate')
DESCRIPTION_COLUMNS = ('narration', 'particulars', 'description', 'transactiondetails', 'details', 'remarks', 'merchant')
DEBIT_COLUMNS = ('withdrawalamt', 'withdrawal', 'debitamount', 'debitamt', 'debit', 'dramount', 'dramt', 'dr')
CREDIT_COLUMNS = ('depositamt', 'deposit', 'creditamount', 'creditamt', 'credit', 'cramount', 'cramt', 'cr')
AMOUNT_COLUMNS = ('transactionamount', 'txnamount', 'amount')
BALANCE_COLUMNS = ('closingbalance', 'availablebalance', 'balance', 'bal')
TYPE_COLUMNS = ('transactiontype', 'type', 'drcr', 'debitcredit')


def parse_date(date_str: str) -> Optional[pd.Timestamp]:
    """
    Parse date string in various formats, prioritizing DD-MM-YYYY format.
    
    Args:
        date_str (str): Date string to parse
    
    Returns:
        Optional[pd.Timestamp]: Parsed date or None if parsing fails
    """
    if pd.isna(date_str) or not date_str:
        return None
    
    # Convert to string and strip whitespace
    date_str = str(date_str).strip()
    
    # List of date formats to try, prioritizing DD-MM-YYYY
    date_formats = [
        '%d-%m-%Y',    # DD-MM-YYYY (primary format for HDFC Bank)
        '%d/%m/%Y',    # DD/MM/YYYY
        '%d.%m.%Y',    # DD.MM.YYYY
        '%Y-%m-%d',    # YYYY-MM-DD
        '%m-%d-%Y',    # MM-DD-YYYY
        '%m/%d/%Y',    # MM/DD/YYYY
        '%d-%m-%y',    # DD-MM-YY
        '%d/%m/%y',    # DD/MM/YY
        '%m-%d-%y',    # MM-DD-YY
        '%m/%d/%y',    # MM/DD/YY
    ]
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, date_format)
            return pd.Timestamp(parsed_date)
        except ValueError:
            continue
    
    # Try pandas built-in parsing as last resort
    try:
        parsed = pd.to_datetime(date_str, dayfirst=True, errors='coerce')
        if pd.isna(parsed):
            return None
        return parsed
    except:
        return None


def extract_data_from_file(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract and normalize a supported CSV or Excel bank statement.
    
    Args:
        file_path (str): Path to the CSV file
    
    Returns:
        Optional[pd.DataFrame]: Processed DataFrame or None if extraction fails
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = os.path.splitext(file_path)[1].lower()
        if extension not in SUPPORTED_STATEMENT_EXTENSIONS:
            raise ValueError("Supported statement formats are CSV, XLS, and XLSX.")

        if extension == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        else:
            df = _read_excel_statement(file_path)

        return _standardize_statement(df, file_path)
        
    except Exception as e:
        print(f"Error extracting data from {file_path}: {str(e)}")
        return None


def _normalize_header(value) -> str:
    return re.sub(r'[^a-z0-9]', '', str(value).lower())


def _find_column(columns, aliases):
    normalized = {column: _normalize_header(column) for column in columns}
    for alias in aliases:
        for column, key in normalized.items():
            if key == alias:
                return column
    return None


def _has_statement_header(columns) -> bool:
    return (
        _find_column(columns, DATE_COLUMNS) is not None
        and _find_column(columns, DESCRIPTION_COLUMNS) is not None
        and (
            _find_column(columns, DEBIT_COLUMNS) is not None
            or _find_column(columns, CREDIT_COLUMNS) is not None
            or _find_column(columns, AMOUNT_COLUMNS) is not None
        )
    )


def _read_excel_statement(file_path: str) -> pd.DataFrame:
    workbook = pd.ExcelFile(file_path)
    try:
        best_sheet = None
        best_header = None
        best_score = 0

        for sheet_name in workbook.sheet_names:
            preview = pd.read_excel(workbook, sheet_name=sheet_name, header=None, nrows=50)
            for row_index, row in preview.iterrows():
                columns = row.tolist()
                if not _has_statement_header(columns):
                    continue
                score = sum(
                    _find_column(columns, aliases) is not None
                    for aliases in (DATE_COLUMNS, DESCRIPTION_COLUMNS, DEBIT_COLUMNS, CREDIT_COLUMNS, AMOUNT_COLUMNS, BALANCE_COLUMNS)
                )
                if score > best_score:
                    best_sheet = sheet_name
                    best_header = row_index
                    best_score = score

        if best_sheet is None:
            raise ValueError("Could not find a transaction header row in the workbook.")

        return pd.read_excel(workbook, sheet_name=best_sheet, header=best_header)
    finally:
        workbook.close()


def _to_amounts(values: pd.Series) -> pd.Series:
    cleaned = values.astype(str).str.strip()
    cleaned = cleaned.str.replace(r'[₹,$\s]', '', regex=True)
    cleaned = cleaned.str.replace(r'^\((.*)\)$', r'-\1', regex=True)
    return pd.to_numeric(cleaned, errors='coerce').fillna(0)


def _account_name_from_path(file_path: str) -> str:
    filename = os.path.splitext(os.path.basename(file_path))[0]
    filename = re.sub(r'_\d{8}_\d{6}(?:_\d+)?$', '', filename)
    masked_account = re.search(r'(?i)x{2,}(\d{4,})', filename)
    if masked_account:
        return f"Account XX{masked_account.group(1)}"
    return filename or 'Primary Account'


def get_account_name(file_path: str) -> str:
    """Return the normalized account name represented by a statement filename."""
    return _account_name_from_path(file_path)


def _is_sample_statement(filename: str) -> bool:
    raw_name = os.path.splitext(os.path.basename(filename))[0].lower()
    account_name = _account_name_from_path(filename).lower()
    return (
        raw_name.startswith(SAMPLE_STATEMENT_PREFIXES)
        or account_name.startswith(SAMPLE_STATEMENT_PREFIXES)
    )


def _statement_fingerprint(df: pd.DataFrame) -> Optional[bytes]:
    identity_columns = ['Transaction Date', 'Description', 'Amount', 'Balance']
    if 'Account' in df.columns:
        identity_columns.append('Account')
    if df.empty or not all(column in df.columns for column in identity_columns):
        return None

    statement = (
        df[identity_columns]
        .sort_values(identity_columns, kind='mergesort')
        .reset_index(drop=True)
    )
    return pd.util.hash_pandas_object(statement, index=False).values.tobytes()


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_inputs_directory() -> str:
    return os.path.join(get_project_root(), 'inputs')


def get_processed_data_path() -> str:
    return os.path.join(get_project_root(), 'processed_data.csv')


def set_active_statement_files(file_names: List[str], inputs_dir: Optional[str] = None) -> None:
    """Persist the statement files represented in the generated dataset."""
    inputs_dir = inputs_dir or get_inputs_directory()
    os.makedirs(inputs_dir, exist_ok=True)

    normalized_names = []
    for file_name in file_names:
        if (
            not isinstance(file_name, str)
            or os.path.basename(file_name) != file_name
            or os.path.splitext(file_name)[1].lower() not in SUPPORTED_STATEMENT_EXTENSIONS
            or _is_sample_statement(file_name)
        ):
            raise ValueError(f"Invalid active statement filename: {file_name}")
        normalized_names.append(file_name)

    manifest_path = os.path.join(inputs_dir, ACTIVE_STATEMENTS_MANIFEST)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=inputs_dir,
            prefix='.active-statements-',
            suffix='.tmp',
            delete=False,
        ) as manifest_file:
            temporary_path = manifest_file.name
            json.dump({'files': sorted(set(normalized_names))}, manifest_file)
            manifest_file.write('\n')
        os.replace(temporary_path, manifest_path)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


def _get_active_statement_files(inputs_dir: str) -> Optional[List[str]]:
    manifest_path = os.path.join(inputs_dir, ACTIVE_STATEMENTS_MANIFEST)
    if not os.path.exists(manifest_path):
        return None

    with open(manifest_path, 'r', encoding='utf-8') as manifest_file:
        manifest = json.load(manifest_file)
    file_names = manifest.get('files') if isinstance(manifest, dict) else None
    if not isinstance(file_names, list) or not all(isinstance(name, str) for name in file_names):
        raise ValueError(f"Invalid active statement manifest: {manifest_path}")

    for file_name in file_names:
        if (
            os.path.basename(file_name) != file_name
            or os.path.splitext(file_name)[1].lower() not in SUPPORTED_STATEMENT_EXTENSIONS
            or _is_sample_statement(file_name)
        ):
            raise ValueError(f"Invalid active statement filename in manifest: {file_name}")
    return sorted(set(file_names))


def clear_processed_data() -> None:
    """Remove the generated dataset so APIs cannot continue serving stale totals."""
    processed_file = get_processed_data_path()
    if os.path.exists(processed_file):
        os.remove(processed_file)


def _standardize_statement(df: pd.DataFrame, file_path: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.rename(columns=lambda column: str(column).strip())
    date_col = _find_column(df.columns, DATE_COLUMNS)
    description_col = _find_column(df.columns, DESCRIPTION_COLUMNS)
    debit_col = _find_column(df.columns, DEBIT_COLUMNS)
    credit_col = _find_column(df.columns, CREDIT_COLUMNS)
    amount_col = _find_column(df.columns, AMOUNT_COLUMNS)

    if date_col is None or description_col is None:
        raise ValueError("Statement must include transaction date and description columns.")
    if debit_col is None and credit_col is None and amount_col is None:
        raise ValueError("Statement must include debit/credit columns or a transaction amount column.")

    dates = df[date_col].apply(parse_date)
    descriptions = df[description_col].fillna('').astype(str).str.strip()

    if debit_col is not None or credit_col is not None:
        debits = _to_amounts(df[debit_col]) if debit_col is not None else pd.Series(0, index=df.index)
        credits = _to_amounts(df[credit_col]) if credit_col is not None else pd.Series(0, index=df.index)
        amounts = credits - debits
    else:
        amounts = _to_amounts(df[amount_col])
        type_col = _find_column(df.columns, TYPE_COLUMNS)
        if type_col is not None:
            transaction_types = df[type_col].fillna('').astype(str).str.strip().str.lower()
            debit_mask = transaction_types.str.startswith(('d', 'dr')) | transaction_types.str.contains('debit|withdraw', regex=True)
            amounts = amounts.where(~debit_mask, -amounts.abs())
            credit_mask = transaction_types.str.startswith(('c', 'cr')) | transaction_types.str.contains('credit|deposit', regex=True)
            amounts = amounts.where(~credit_mask, amounts.abs())

    balance_col = _find_column(df.columns, BALANCE_COLUMNS)
    balances = _to_amounts(df[balance_col]) if balance_col is not None else pd.Series(0, index=df.index)

    standardized = pd.DataFrame({
        'Transaction Date': dates,
        'Description': descriptions,
        'Amount': amounts,
        'Balance': balances,
        'Account': _account_name_from_path(file_path)
    })
    standardized = standardized[standardized['Transaction Date'].notna() & standardized['Description'].ne('')]
    return standardized.reset_index(drop=True)


def process_csv(file_path: str) -> pd.DataFrame:
    """Normalize a CSV bank statement into the shared transaction schema."""
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        return _standardize_statement(df, file_path)
    except Exception as e:
        print(f"Error processing CSV file: {str(e)}")
        return pd.DataFrame()


def get_transaction_data() -> pd.DataFrame:
    """
    Get transaction data from the latest uploaded file or return empty DataFrame.
    This function is for API integration.
    
    Returns:
        pd.DataFrame: Transaction data or empty DataFrame
    """
    try:
        # First try to load processed data (persistent data)
        processed_file = get_processed_data_path()
        
        if os.path.exists(processed_file):
            try:
                df = pd.read_csv(processed_file)
                if not df.empty:
                    # Ensure Transaction Date is properly formatted
                    if 'Transaction Date' in df.columns:
                        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
                    return df
            except Exception as e:
                print(f"Error loading processed data: {e}")
        
        # If no processed data, try to get fresh data from all files
        return get_all_transaction_data()
    
    except Exception as e:
        print(f"Error in get_transaction_data: {e}")
        return pd.DataFrame()


def load_processed_data() -> pd.DataFrame:
    """
    Load previously processed transaction data.
    This function is for API integration.
    
    Returns:
        pd.DataFrame: Processed transaction data or empty DataFrame
    """
    try:
        # Check if there's a processed data file
        processed_file = get_processed_data_path()
        
        if os.path.exists(processed_file):
            df = pd.read_csv(processed_file)
            # Ensure Transaction Date is properly formatted
            if 'Transaction Date' in df.columns:
                df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
            return df
        
        # If no processed file, try to get fresh data
        return get_transaction_data()
    
    except Exception as e:
        print(f"Error in load_processed_data: {e}")
        return pd.DataFrame()


def save_processed_data(df: pd.DataFrame) -> bool:
    """
    Save processed transaction data for persistence between sessions.
    
    Args:
        df (pd.DataFrame): Processed transaction data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if df is None or df.empty:
            return False
            
        if df is None or df.empty:
            return False

        processed_file = get_processed_data_path()
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                newline='',
                dir=os.path.dirname(processed_file),
                prefix='.processed-data-',
                suffix='.tmp',
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                df.to_csv(temporary_file, index=False)
            os.replace(temporary_path, processed_file)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.remove(temporary_path)

        print(f"Saved {len(df)} transactions to {processed_file}")
        return True
        
    except Exception as e:
        raise RuntimeError(f"Error saving processed data: {e}") from e


def _prepare_processed_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions is None or transactions.empty:
        raise ValueError("No transactions were provided.")

    prepared = transactions.copy()
    duplicate_columns = ['Account', 'Transaction Date', 'Description', 'Amount']
    missing_columns = [column for column in duplicate_columns if column not in prepared.columns]
    if missing_columns:
        raise ValueError(
            f"Transactions are missing required deduplication columns: {', '.join(missing_columns)}"
        )

    prepared['Transaction Date'] = pd.to_datetime(
        prepared['Transaction Date'],
        errors='coerce',
    )
    prepared['Amount'] = pd.to_numeric(prepared['Amount'], errors='coerce')
    prepared = prepared.dropna(subset=['Transaction Date', 'Amount'])
    prepared = prepared.drop_duplicates(subset=duplicate_columns, keep='first')
    prepared = prepared.sort_values('Transaction Date', ascending=False)
    if prepared.empty:
        raise ValueError("No valid transactions remain after date and amount validation.")
    return prepared


def replace_processed_data(transactions: pd.DataFrame) -> pd.DataFrame:
    """Replace the generated dataset with only the supplied normalized transactions."""
    prepared = _prepare_processed_transactions(transactions)
    if not save_processed_data(prepared):
        raise RuntimeError("The replacement transaction dataset could not be saved.")
    return prepared


def get_all_transaction_data() -> pd.DataFrame:
    """
    Load the current generated dataset.

    If no dataset exists yet, bootstrap it once from legacy statement files.
    If an active statement manifest exists, it limits legacy bootstrap to those
    source files. Without a manifest, all legacy statement files are considered.
    
    Returns:
        pd.DataFrame: Current combined transaction data
    """
    processed_file = get_processed_data_path()
    if os.path.exists(processed_file):
        return load_processed_data()

    inputs_dir = get_inputs_directory()
    if not os.path.isdir(inputs_dir):
        return pd.DataFrame()

    active_files = _get_active_statement_files(inputs_dir)
    if active_files is None:
        statement_files = [
            filename
            for filename in sorted(os.listdir(inputs_dir))
            if os.path.splitext(filename)[1].lower() in SUPPORTED_STATEMENT_EXTENSIONS
            and not _is_sample_statement(filename)
        ]
    else:
        statement_files = [
            filename
            for filename in active_files
            if os.path.isfile(os.path.join(inputs_dir, filename))
        ]
    all_dataframes = []
    for statement_file in statement_files:
        df = extract_data_from_file(os.path.join(inputs_dir, statement_file))
        if df is None or df.empty:
            print(f"Skipping unreadable legacy statement: {statement_file}")
            continue
        df['Source_File'] = statement_file
        all_dataframes.append(df)

    if not all_dataframes:
        return pd.DataFrame()

    combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
    combined_df = combined_df.drop_duplicates(
        subset=['Account', 'Transaction Date', 'Description', 'Amount'],
        keep='first',
    )
    combined_df = combined_df.sort_values('Transaction Date', ascending=False)
    if not save_processed_data(combined_df):
        raise RuntimeError("Legacy statements could not be saved as the generated dataset.")
    set_active_statement_files(
        [df['Source_File'].iloc[0] for df in all_dataframes],
        inputs_dir,
    )
    return combined_df


def filter_transactions_by_date(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """
    Filter transactions by date range.
    
    Args:
        df (pd.DataFrame): Transaction DataFrame
        start_date: Start date for filtering
        end_date: End date for filtering
    
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    try:
        if df.empty or 'Transaction Date' not in df.columns:
            return df
        
        # Convert to datetime if not already
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
        
        # Filter by date range
        mask = (df['Transaction Date'] >= pd.to_datetime(start_date)) & \
               (df['Transaction Date'] <= pd.to_datetime(end_date))
        
        return df[mask]
    
    except Exception as e:
        print(f"Error filtering by date: {e}")
        return df


def filter_transactions_by_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """
    Filter transactions by category.
    
    Args:
        df (pd.DataFrame): Transaction DataFrame
        category (str): Category to filter by
    
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    try:
        if df.empty or 'Category' not in df.columns:
            return df
        
        return df[df['Category'] == category]
    
    except Exception as e:
        print(f"Error filtering by category: {e}")
        return df