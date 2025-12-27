"""
Data extraction module for Personal Finance Tracker.
This module handles extracting and normalizing data from CSV files only.
Specifically designed for HDFC Bank statement CSV format.
"""

import os
import pandas as pd
import re
from datetime import datetime
import numpy as np
from typing import Optional, List


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
    Extract transaction data from CSV files only.
    Supports only HDFC Bank CSV statement format.
    
    Args:
        file_path (str): Path to the CSV file
    
    Returns:
        Optional[pd.DataFrame]: Processed DataFrame or None if extraction fails
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Only support CSV files
        if not file_path.lower().endswith('.csv'):
            raise ValueError("Only CSV files are supported. Please upload a CSV file in HDFC Bank format.")
        
        return process_csv(file_path)
        
    except Exception as e:
        print(f"Error extracting data from {file_path}: {str(e)}")
        return None


def process_csv(file_path: str) -> pd.DataFrame:
    """
    Process HDFC Bank CSV statement format specifically.
    Expected format: Date, Narration, Chq./Ref.No, Value Dt, Withdrawal Amt, Deposit Amt, Closing Balance
    
    Args:
        file_path (str): Path to the CSV file
    
    Returns:
        pd.DataFrame: Standardized DataFrame with Transaction Date, Description, Amount columns
    """
    try:
        # Read the CSV file with UTF-8-SIG encoding to handle BOM
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        
        # Check if the file is empty
        if df.empty:
            print(f"Warning: CSV file {file_path} is empty")
            return pd.DataFrame()
        
        # Print column names for debugging
        print(f"CSV columns: {list(df.columns)}")
        
        # Try to find the date column
        date_col = None
        for col in df.columns:
            if any(term in str(col).lower() for term in ['date', 'dt']):
                date_col = col
                break
        
        if not date_col:
            # Use first column as date if no date column found
            date_col = df.columns[0]
        
        # Find description/narration column
        desc_col = None
        for col in df.columns:
            if any(term in str(col).lower() for term in ['narration', 'description', 'details']):
                desc_col = col
                break
        
        if not desc_col:
            # Use second column as description if no description column found
            if len(df.columns) > 1:
                desc_col = df.columns[1]
            else:
                desc_col = date_col
        
        # Rename columns for easier processing
        df = df.rename(columns={date_col: 'Date', desc_col: 'Narration'})
        
        # Remove empty rows
        df = df.dropna(subset=['Date'])
        
        # Parse dates using the enhanced parse_date function
        df['Date'] = df['Date'].apply(parse_date)
        
        # Filter out rows where date parsing failed
        df = df[df['Date'].notna()]
        
        # Handle withdrawal and deposit amounts
        withdrawal_col = None
        deposit_col = None
        
        # Find withdrawal and deposit columns (flexible column name matching)
        for col in df.columns:
            if any(term in str(col).lower() for term in ['withdrawal', 'debit', 'dr']):
                withdrawal_col = col
            elif any(term in str(col).lower() for term in ['deposit', 'credit', 'cr']):
                deposit_col = col
        
        # If we can't find withdrawal/deposit columns, look for amount column
        if not withdrawal_col and not deposit_col:
            amount_cols = [col for col in df.columns if 'amount' in str(col).lower()]
            if amount_cols:
                # Use the first amount column found
                df['Amount'] = pd.to_numeric(df[amount_cols[0]], errors='coerce').fillna(0)
            else:
                # Create a default amount column with zeros
                df['Amount'] = 0
        else:
            # Clean and convert amount columns
            if withdrawal_col:
                df[withdrawal_col] = df[withdrawal_col].astype(str).str.replace('₹', '').str.replace(',', '').str.strip()
                df[withdrawal_col] = pd.to_numeric(df[withdrawal_col], errors='coerce').fillna(0)
            else:
                withdrawal_col = 'temp_withdrawal'
                df[withdrawal_col] = 0
                
            if deposit_col:
                df[deposit_col] = df[deposit_col].astype(str).str.replace('₹', '').str.replace(',', '').str.strip()
                df[deposit_col] = pd.to_numeric(df[deposit_col], errors='coerce').fillna(0)
            else:
                deposit_col = 'temp_deposit'
                df[deposit_col] = 0
            
            # Calculate net amount (deposits are positive, withdrawals are negative)
            df['Amount'] = df[deposit_col].fillna(0) - df[withdrawal_col].fillna(0)
        
        # Handle balance column
        balance_col = None
        for col in df.columns:
            if any(term in str(col).lower() for term in ['balance', 'closing']):
                balance_col = col
                break
        
        if balance_col:
            df[balance_col] = df[balance_col].astype(str).str.replace('₹', '').str.replace(',', '').str.strip()
            df['Balance'] = pd.to_numeric(df[balance_col], errors='coerce').fillna(0)
        else:
            df['Balance'] = 0
        
        # Create standardized DataFrame
        standardized = pd.DataFrame({
            'Transaction Date': df['Date'],
            'Description': df['Narration'].astype(str),
            'Amount': df['Amount'],
            'Balance': df.get('Balance', 0)
        })
        
        # Add default Account column
        standardized['Account'] = 'Primary Account'
        
        # Remove rows with invalid data
        standardized = standardized[standardized['Transaction Date'].notna()]
        standardized = standardized[standardized['Description'].str.strip() != '']
        
        print(f"Successfully processed {len(standardized)} transactions from {file_path}")
        return standardized

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
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        processed_file = os.path.join(project_root, 'processed_data.csv')
        
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
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        processed_file = os.path.join(project_root, 'processed_data.csv')
        
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
            
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        processed_file = os.path.join(project_root, 'processed_data.csv')
        
        # Save the DataFrame
        df.to_csv(processed_file, index=False)
        print(f"✓ Saved {len(df)} transactions to {processed_file}")
        return True
        
    except Exception as e:
        print(f"Error saving processed data: {e}")
        return False


def get_all_transaction_data() -> pd.DataFrame:
    """
    Get all transaction data from all uploaded files combined.
    This function combines data from all CSV files in the inputs directory.
    
    Returns:
        pd.DataFrame: Combined transaction data from all files
    """
    try:
        # Try to find all CSV files in inputs directory
        inputs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'inputs')
        if not os.path.exists(inputs_dir):
            return pd.DataFrame()
        
        # Find all CSV files
        csv_files = [f for f in os.listdir(inputs_dir) if f.lower().endswith('.csv')]
        if not csv_files:
            return pd.DataFrame()
        
        all_dataframes = []
        
        # Process each CSV file
        for csv_file in csv_files:
            file_path = os.path.join(inputs_dir, csv_file)
            try:
                df = extract_data_from_file(file_path)
                if df is not None and not df.empty:
                    # Add source file info
                    df['Source_File'] = csv_file
                    all_dataframes.append(df)
            except Exception as e:
                print(f"Error processing {csv_file}: {e}")
                continue
        
        # Combine all dataframes
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            
            # Remove duplicates based on date, description, and amount
            if len(combined_df) > 0:
                duplicate_cols = ['Transaction Date', 'Description', 'Amount']
                available_cols = [col for col in duplicate_cols if col in combined_df.columns]
                if available_cols:
                    combined_df = combined_df.drop_duplicates(subset=available_cols, keep='first')
            
            # Sort by date if available
            if 'Transaction Date' in combined_df.columns:
                combined_df = combined_df.sort_values('Transaction Date', ascending=False)
            
            # Save the combined data for persistence
            save_processed_data(combined_df)
            
            return combined_df
        else:
            return pd.DataFrame()
    
    except Exception as e:
        print(f"Error in get_all_transaction_data: {e}")
        return pd.DataFrame()


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