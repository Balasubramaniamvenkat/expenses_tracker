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
    from data_extraction import extract_data_from_file, process_csv, get_all_transaction_data, save_processed_data
    print(f"✓ Imported data_extraction from {src_dir}")
except ImportError as e:
    print(f"⚠️ Could not import data_extraction: {e}")
    def extract_data_from_file(file_path):
        return pd.DataFrame()
    def process_csv(file_path):
        return pd.DataFrame()
    def get_all_transaction_data():
        return pd.DataFrame()
    def save_processed_data(df):
        return False

try:
    from categories import categorize_transaction
    print(f"✓ Imported categories")
except ImportError as e:
    print(f"⚠️ Could not import categories: {e}")
    def categorize_transaction(desc):
        return "Other"

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
    income = df[df['Amount'] > 0]['Amount'].sum() if 'Amount' in df.columns else 0
    expenses = abs(df[df['Amount'] < 0]['Amount'].sum()) if 'Amount' in df.columns else 0
    
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

def validate_csv_file(file: UploadFile) -> bool:
    """Validate that the uploaded file is a CSV"""
    if not file.filename:
        return False
    
    # Check file extension
    if not file.filename.lower().endswith('.csv'):
        return False
    
    # Check content type (optional, as browsers may send different MIME types)
    valid_content_types = [
        'text/csv',
        'application/csv',
        'text/plain',
        'application/vnd.ms-excel'
    ]
    
    return True  # Be lenient with content type checking

def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file to inputs directory and return the path"""
    inputs_dir_path = ensure_inputs_directory()
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = file.filename or "unknown.csv"
    name_without_ext = os.path.splitext(original_name)[0]
    
    unique_filename = f"{name_without_ext}_{timestamp}.csv"
    file_path = os.path.join(inputs_dir_path, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path

def process_uploaded_file(file_path: str, original_filename: str) -> FileProcessingResult:
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
            )
        
        # Add categories if not present
        if 'Category' not in df.columns and 'Description' in df.columns and 'Amount' in df.columns:
            df['Category'] = df.apply(
                lambda row: categorize_transaction(row['Description'], row['Amount'])['category'], 
                axis=1
            )
        
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
        )
        
    except Exception as e:
        return FileProcessingResult(
            filename=original_filename,
            success=False,
            message=f"Error processing file: {str(e)}",
            records_processed=0,
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            errors=[str(e)]
        )

@router.post("/single", response_model=FileProcessingResult)
async def upload_single_file(file: UploadFile = File(...)):
    """Upload and process a single CSV file - replaces existing data"""
    
    # Validate file
    if not validate_csv_file(file):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Please upload a CSV file."
        )
    
    try:
        # Save file
        file_path = save_uploaded_file(file)
        
        # Process file
        result = process_uploaded_file(file_path, file.filename or "unknown.csv")
        
        # If upload was successful, save ONLY this file's data as processed data
        # This replaces any existing data (user uploads new file = fresh start)
        if result.success:
            try:
                # Extract data from just this uploaded file
                df = extract_data_from_file(file_path)
                if df is not None and not df.empty:
                    # Add categories
                    if 'Category' not in df.columns and 'Description' in df.columns and 'Amount' in df.columns:
                        df['Category'] = df.apply(
                            lambda row: categorize_transaction(row['Description'], row['Amount'])['category'], 
                            axis=1
                        )
                    save_processed_data(df)
                    print(f"✓ Saved {len(df)} transactions from uploaded file")
            except Exception as e:
                print(f"Warning: Could not save processed data: {e}")
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process upload: {str(e)}"
        )

@router.post("/batch", response_model=BatchUploadResult)
async def upload_batch_files(files: List[UploadFile] = File(...)):
    """Upload and process multiple CSV files"""
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Too many files. Maximum 10 files per batch.")
    
    results = []
    successful_uploads = 0
    failed_uploads = 0
    
    for file in files:
        # Validate each file
        if not validate_csv_file(file):
            result = FileProcessingResult(
                filename=file.filename or "unknown",
                success=False,
                message="Invalid file type. Only CSV files are supported.",
                records_processed=0,
                file_size=0,
                errors=["Invalid file type"]
            )
            results.append(result)
            failed_uploads += 1
            continue
        
        try:
            # Save and process file
            file_path = save_uploaded_file(file)
            result = process_uploaded_file(file_path, file.filename or "unknown.csv")
            results.append(result)
            
            if result.success:
                successful_uploads += 1
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
    
    # If any uploads were successful, refresh the combined processed data
    if successful_uploads > 0:
        try:
            # Get all transaction data and save as processed data
            combined_df = get_all_transaction_data()
            if not combined_df.empty:
                save_processed_data(combined_df)
                print(f"✓ Refreshed processed data with {len(combined_df)} total transactions")
                overall_summary["total_combined_records"] = len(combined_df)
        except Exception as e:
            print(f"Warning: Could not refresh processed data: {e}")
    
    return BatchUploadResult(
        total_files=len(files),
        successful_uploads=successful_uploads,
        failed_uploads=failed_uploads,
        results=results,
        overall_summary=overall_summary
    )

@router.get("/accounts", response_model=List[AccountSummary])
async def get_account_summaries():
    """Get summary of all uploaded accounts"""
    try:
        inputs_dir_path = ensure_inputs_directory()
        
        # Find all CSV files
        csv_files = [f for f in os.listdir(inputs_dir_path) if f.lower().endswith('.csv')]
        
        if not csv_files:
            return []
        
        summaries = []
        for csv_file in csv_files:
            file_path = os.path.join(inputs_dir_path, csv_file)
            
            try:
                df = extract_data_from_file(file_path)
                if df is not None and not df.empty:                    # Get account info
                    account_name = df['Account'].iloc[0] if 'Account' in df.columns and not df.empty else csv_file
                    transactions_count = len(df)
                    total_amount = df['Amount'].sum() if 'Amount' in df.columns else 0
                    
                    # Get date range
                    date_range = {"start": "", "end": ""}
                    if 'Transaction Date' in df.columns:
                        dates = pd.to_datetime(df['Transaction Date'], errors='coerce')
                        dates = dates.dropna()
                        if not dates.empty:
                            date_range = {
                                "start": dates.min().strftime("%Y-%m-%d"),
                                "end": dates.max().strftime("%Y-%m-%d")
                            }
                    
                    summaries.append(AccountSummary(
                        account_name=str(account_name),
                        transactions_count=transactions_count,
                        total_amount=float(total_amount),
                        date_range=date_range
                    ))
                    
            except Exception as e:
                print(f"Error processing {csv_file}: {e}")
                continue
        
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
        inputs_dir_path = ensure_inputs_directory()
        
        # Remove all CSV files
        csv_files = [f for f in os.listdir(inputs_dir_path) if f.lower().endswith('.csv')]
        removed_count = 0
        
        for csv_file in csv_files:
            file_path = os.path.join(inputs_dir_path, csv_file)
            try:
                os.remove(file_path)
                removed_count += 1
            except Exception as e:
                print(f"Error removing {csv_file}: {e}")
        
        return {
            "message": f"Removed {removed_count} files",
            "removed_count": removed_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear files: {str(e)}"
        )
