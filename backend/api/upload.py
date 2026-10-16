"""
Upload API endpoints for Family Finance Tracker
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
import os
import shutil
import hashlib
import tempfile
import uuid
from datetime import datetime
import sys

# Add the SRC directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'SRC')
project_dir = os.path.dirname(parent_dir)
inputs_dir = os.path.join(project_dir, 'inputs')

sys.path.insert(0, src_dir)

# Import backend modules
# Import them individually to handle relative import issues in analysis.py
try:
    from data_extraction import (
        SUPPORTED_STATEMENT_EXTENSIONS,
        extract_data_from_file,
        process_csv,
        get_all_transaction_data,
        get_account_name,
        replace_processed_data,
        set_active_statement_files,
        clear_processed_data,
    )
    print(f"✓ Imported data_extraction from {src_dir}")
except ImportError as e:
    print(f"⚠️ Could not import data_extraction: {e}")
    SUPPORTED_STATEMENT_EXTENSIONS = {'.csv', '.xls', '.xlsx'}
    def extract_data_from_file(file_path):
        return pd.DataFrame()
    def process_csv(file_path):
        return pd.DataFrame()
    def get_all_transaction_data():
        return pd.DataFrame()
    def get_account_name(file_path):
        return os.path.splitext(os.path.basename(file_path))[0]
    def replace_processed_data(transactions):
        raise RuntimeError("Statement data extraction is unavailable.")
    def set_active_statement_files(file_names):
        raise RuntimeError("Statement data extraction is unavailable.")
    def clear_processed_data():
        raise RuntimeError("Statement data extraction is unavailable.")

try:
    from categories import categorize_transaction
    print(f"✓ Imported categories")
except ImportError as e:
    print(f"⚠️ Could not import categories: {e}")
    def categorize_transaction(desc):
        return "Other"

from refined_categories import get_category_group

# Define a simple calculate_summary_statistics since analysis.py has relative imports
def calculate_summary_statistics(df: pd.DataFrame) -> dict:
    """Calculate basic summary statistics for transactions."""
    if df is None or df.empty:
        return {
            'total_transactions': 0,
            'total_income': 0,
            'total_expenses': 0,
            'net_amount': 0,
            'date_range': None,
            'months_covered': 0
        }
    
    total = len(df)
    if 'Category' not in df.columns:
        df['Category'] = ''
    if 'Description' in df.columns and 'Amount' in df.columns:
        missing_categories = (
            df['Category'].isna()
            | df['Category'].astype(str).str.strip().eq('')
        )
        for index in df.index[missing_categories]:
            result = categorize_transaction(
                str(df.at[index, 'Description']),
                float(df.at[index, 'Amount'])
            )
            df.at[index, 'Category'] = (
                result.get('category', 'Other')
                if isinstance(result, dict)
                else str(result or 'Other')
            )

    if 'Amount' in df.columns:
        category_groups = df['Category'].map(get_category_group)
        income = df.loc[
            df['Amount'].gt(0) & category_groups.eq('Income'),
            'Amount'
        ].sum()
        expenses = abs(df.loc[
            df['Amount'].lt(0) & category_groups.eq('Expense'),
            'Amount'
        ].sum())
        investments = abs(df.loc[
            df['Amount'].lt(0) & category_groups.eq('Investment'),
            'Amount'
        ].sum())
        planned = abs(df.loc[
            df['Amount'].lt(0) & category_groups.eq('Planned'),
            'Amount'
        ].sum())
        transfers = abs(df.loc[
            df['Amount'].lt(0) & category_groups.eq('Transfer'),
            'Amount'
        ].sum())
    else:
        income = expenses = investments = planned = transfers = 0
    
    # Calculate date range
    date_range = None
    months_covered = 0
    date_col = None
    
    # Find the date column
    for col in ['Transaction Date', 'Date', 'date', 'transaction_date']:
        if col in df.columns:
            date_col = col
            break
    
    if date_col:
        try:
            dates = pd.to_datetime(df[date_col], errors='coerce')
            valid_dates = dates.dropna()
            if len(valid_dates) > 0:
                min_date = valid_dates.min()
                max_date = valid_dates.max()
                date_range = {
                    'from': min_date.strftime('%Y-%m-%d'),
                    'to': max_date.strftime('%Y-%m-%d')
                }
                # Calculate months covered
                months_covered = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month) + 1
        except Exception as e:
            print(f"Warning: Could not calculate date range: {e}")
    
    return {
        'total_transactions': total,
        'total_income': float(income),
        'total_expenses': float(expenses),
        'total_investments': float(investments),
        'total_planned': float(planned),
        'total_transfers': float(transfers),
        'net_amount': float(income - expenses),
        'date_range': date_range,
        'months_covered': months_covered
    }

print(f"✓ Backend modules loaded successfully")

router = APIRouter(prefix="/upload", tags=["upload"])

# Pydantic models for API responses
class FileProcessingResult(BaseModel):
    filename: str
    success: bool
    message: str
    records_processed: int
    file_size: int
    preview_data: Optional[List[dict]] = None
    summary: Optional[dict] = None
    errors: Optional[List[str]] = None

class BatchUploadResult(BaseModel):
    total_files: int
    successful_uploads: int
    failed_uploads: int
    dataset_replaced: bool
    results: List[FileProcessingResult]
    overall_summary: Optional[dict] = None

class AccountSummary(BaseModel):
    account_name: str
    transactions_count: int
    total_amount: float
    date_range: dict

def ensure_inputs_directory():
    """Ensure the inputs directory exists"""
    if not os.path.exists(inputs_dir):
        os.makedirs(inputs_dir)
    return inputs_dir

def validate_statement_file(file: UploadFile) -> bool:
    """Validate supported bank statement file formats."""
    if not file.filename:
        return False

    extension = os.path.splitext(file.filename)[1].lower()
    return extension in SUPPORTED_STATEMENT_EXTENSIONS

def _file_content_digest(file_object) -> str:
    digest = hashlib.sha256()
    file_object.seek(0)
    while True:
        chunk = file_object.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
    file_object.seek(0)
    return digest.hexdigest()


def _find_existing_file_by_digest(digest: str, inputs_dir_path: str) -> Optional[str]:
    for filename in sorted(os.listdir(inputs_dir_path)):
        if os.path.splitext(filename)[1].lower() not in SUPPORTED_STATEMENT_EXTENSIONS:
            continue
        existing_path = os.path.join(inputs_dir_path, filename)
        try:
            with open(existing_path, 'rb') as existing_file:
                if _file_content_digest(existing_file) == digest:
                    return existing_path
        except PermissionError:
            print(f"Warning: Could not inspect locked statement file for duplicates: {filename}")
    return None


def save_uploaded_file(
    file: UploadFile,
    reserved_file_names: Optional[set[str]] = None,
) -> tuple[str, bool]:
    """Save by original name, reusing identical content already in the input folder."""
    inputs_dir_path = ensure_inputs_directory()
    original_name = os.path.basename(file.filename or "unknown.csv")
    name_without_ext, extension = os.path.splitext(original_name)
    normalized_name = f"{name_without_ext}{extension.lower()}"
    digest = _file_content_digest(file.file)

    existing_content_path = _find_existing_file_by_digest(digest, inputs_dir_path)
    if existing_content_path:
        return existing_content_path, True

    if reserved_file_names is None:
        reserved_file_names = set()
    target_name = normalized_name
    if target_name in reserved_file_names:
        suffix = 2
        while True:
            target_name = f"{name_without_ext}_{suffix}{extension.lower()}"
            target_path = os.path.join(inputs_dir_path, target_name)
            if target_name not in reserved_file_names and not os.path.exists(target_path):
                break
            suffix += 1

    file_path = os.path.join(inputs_dir_path, target_name)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='wb',
            dir=inputs_dir_path,
            prefix='.upload-',
            suffix='.tmp',
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            shutil.copyfileobj(file.file, temporary_file)
        os.replace(temporary_path, file_path)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)

    reserved_file_names.add(target_name)
    return file_path, False

def process_uploaded_file(
    file_path: str,
    original_filename: str,
    account_name: Optional[str] = None,
) -> tuple[FileProcessingResult, Optional[pd.DataFrame]]:
    """Process uploaded file and return results"""
    try:
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Debug logging
        print(f"[DEBUG] Processing file: {file_path}")
        print(f"[DEBUG] File exists: {os.path.exists(file_path)}")
        print(f"[DEBUG] File size: {file_size}")
        
        # Process the CSV file
        df = extract_data_from_file(file_path)
        
        print(f"[DEBUG] DataFrame result: {df is not None}, empty: {df.empty if df is not None else 'N/A'}")
        
        if df is None or df.empty:
            return FileProcessingResult(
                filename=original_filename,
                success=False,
                message="Failed to process file or file contains no valid data",
                records_processed=0,
                file_size=file_size,
                errors=["File processing failed or no valid data found"]
            ), None

        if account_name:
            df['Account'] = account_name
        
        categories = df.apply(
            lambda row: categorize_transaction(
                str(row['Description']),
                float(row['Amount']),
            ),
            axis=1,
        )
        df['Category'] = categories.map(lambda result: result.get('category', 'Other'))
        df['Subcategory'] = categories.map(lambda result: result.get('subcategory', 'Uncategorized'))
        
        # Calculate summary statistics
        summary = calculate_summary_statistics(df)
        
        # Create preview data (first 5 rows)
        preview_data = []
        for _, row in df.head(5).iterrows():
            preview_data.append({
                'date': str(row.get('Transaction Date', '')),
                'description': str(row.get('Description', '')),
                'amount': float(row.get('Amount', 0)),
                'category': str(row.get('Category', 'Other')),
                'account': str(row.get('Account', 'Default Account')),
                'balance': float(row.get('Balance', 0))
            })
        
        return FileProcessingResult(
            filename=original_filename,
            success=True,
            message=f"Successfully processed {len(df)} transactions",
            records_processed=len(df),
            file_size=file_size,
            preview_data=preview_data,
            summary=summary
        ), df
        
    except Exception as e:
        return FileProcessingResult(
            filename=original_filename,
            success=False,
            message=f"Error processing file: {str(e)}",
            records_processed=0,
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            errors=[str(e)]
        ), None

@router.post("/single", response_model=FileProcessingResult)
async def upload_single_file(file: UploadFile = File(...)):
    """Replace the generated dataset with this statement's transactions."""
    
    # Validate file
    if not validate_statement_file(file):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Please upload a CSV, XLS, or XLSX file."
        )
    
    try:
        # Save file
        file_path, duplicate_file = save_uploaded_file(file)
        
        # Process file
        result, transactions = process_uploaded_file(
            file_path,
            file.filename or "unknown.csv",
            get_account_name(file_path if duplicate_file else file.filename or "unknown.csv"),
        )
        
        if result.success and transactions is not None:
            try:
                transactions['Source_File'] = os.path.basename(file_path)
                processed_data = replace_processed_data(transactions)
                set_active_statement_files([os.path.basename(file_path)])
                result.summary = result.summary or {}
                result.summary['dataset_replaced'] = True
                result.summary['processed_transactions'] = len(processed_data)
                if duplicate_file:
                    result.message = (
                        f"Identical file content already exists as {os.path.basename(file_path)}. "
                        "The processed dataset was replaced using its transactions."
                    )
                print(f"✓ Replaced generated dataset with {len(processed_data)} transactions")
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Could not replace the processed dataset: {e}"
                ) from e
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process upload: {str(e)}"
        )

@router.post("/batch", response_model=BatchUploadResult)
async def upload_batch_files(files: List[UploadFile] = File(...)):
    """Process a complete batch and replace the generated dataset."""
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    successful_file_names = []
    new_transaction_frames = []
    reserved_file_names = set()
    successful_uploads = 0
    failed_uploads = 0
    
    for file in files:
        # Validate each file
        if not validate_statement_file(file):
            result = FileProcessingResult(
                filename=file.filename or "unknown",
                success=False,
            message="Invalid file type. Supported formats are CSV, XLS, and XLSX.",
                records_processed=0,
                file_size=0,
                errors=["Invalid file type"]
            )
            results.append(result)
            failed_uploads += 1
            continue
        
        try:
            # Save and process file
            file_path, duplicate_file = save_uploaded_file(file, reserved_file_names)
            result, transactions = process_uploaded_file(
                file_path,
                file.filename or "unknown.csv",
                get_account_name(file_path if duplicate_file else file.filename or "unknown.csv"),
            )
            results.append(result)
            
            if result.success and transactions is not None:
                successful_uploads += 1
                successful_file_names.append(os.path.basename(file_path))
                transactions['Source_File'] = os.path.basename(file_path)
                new_transaction_frames.append(transactions)
                if duplicate_file:
                    result.message = (
                        f"Identical file content already exists as {os.path.basename(file_path)}. "
                        "No extra file was saved; duplicate transactions will be skipped."
                    )
            else:
                failed_uploads += 1
                
        except Exception as e:
            result = FileProcessingResult(
                filename=file.filename or "unknown",
                success=False,
                message=f"Failed to process file: {str(e)}",
                records_processed=0,
                file_size=0,
                errors=[str(e)]
            )
            results.append(result)
            failed_uploads += 1
      # Calculate overall summary
    total_records = sum(r.records_processed for r in results if r.success)
    overall_summary = {
        "total_records_processed": total_records,
        "successful_files": successful_uploads,
        "failed_files": failed_uploads
    }
    
    if successful_uploads > 0 and failed_uploads == 0:
        try:
            uploaded_transactions = pd.concat(new_transaction_frames, ignore_index=True, sort=False)
            processed_data = replace_processed_data(uploaded_transactions)
            set_active_statement_files(successful_file_names)
            overall_summary["dataset_replaced"] = True
            overall_summary["processed_transactions"] = len(processed_data)
            print(f"✓ Replaced generated dataset with {len(processed_data)} transactions")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Could not replace the processed dataset: {e}"
            ) from e
    else:
        overall_summary["dataset_replaced"] = False
        overall_summary["dataset_replacement_message"] = (
            "The processed dataset was not replaced because one or more files failed. "
            "Fix the failed files and upload the complete batch again."
        )
    
    return BatchUploadResult(
        total_files=len(files),
        successful_uploads=successful_uploads,
        failed_uploads=failed_uploads,
        dataset_replaced=overall_summary["dataset_replaced"],
        results=results,
        overall_summary=overall_summary
    )

@router.get("/accounts", response_model=List[AccountSummary])
async def get_account_summaries():
    """Get summary of all uploaded accounts"""
    try:
        df = get_all_transaction_data()
        if df.empty:
            return []

        summaries = []
        for account_name, account_df in df.groupby('Account', dropna=False):
            dates = pd.to_datetime(
                account_df['Transaction Date'],
                errors='coerce'
            ).dropna()
            date_range = {"start": "", "end": ""}
            if not dates.empty:
                date_range = {
                    "start": dates.min().strftime("%Y-%m-%d"),
                    "end": dates.max().strftime("%Y-%m-%d")
                }

            summaries.append(AccountSummary(
                account_name=str(account_name),
                transactions_count=len(account_df),
                total_amount=float(account_df['Amount'].sum()),
                date_range=date_range
            ))
        
        return summaries
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get account summaries: {str(e)}"
        )

@router.delete("/clear")
async def clear_uploaded_files():
    """Clear all uploaded files"""
    try:
        set_active_statement_files([])
        clear_processed_data()
        inputs_dir_path = ensure_inputs_directory()
        
        statement_files = [
            filename for filename in os.listdir(inputs_dir_path)
            if os.path.splitext(filename)[1].lower() in SUPPORTED_STATEMENT_EXTENSIONS
        ]
        removed_count = 0
        
        removal_errors = []
        for statement_file in statement_files:
            file_path = os.path.join(inputs_dir_path, statement_file)
            try:
                os.remove(file_path)
                removed_count += 1
            except Exception as e:
                print(f"Error removing {statement_file}: {e}")
                removal_errors.append(statement_file)

        if removal_errors:
            raise HTTPException(
                status_code=500,
                detail=f"Cleared the active dataset but could not remove: {', '.join(removal_errors)}"
            )
        
        return {
            "message": f"Removed {removed_count} files",
            "removed_count": removed_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear files: {str(e)}"
        )
