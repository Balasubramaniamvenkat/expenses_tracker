"""
Transaction API endpoints for Family Finance Tracker
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel
import pandas as pd
import sys
import os

# Add multiple directories to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'SRC')
project_root = os.path.dirname(parent_dir)

# Add all potential import paths
for path in [src_dir, parent_dir, project_root]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Define fallback functions first
def get_transaction_data():
    """Fallback function to get transaction data"""
    return pd.DataFrame()

def load_processed_data():
    """Fallback function to load processed data"""
    return pd.DataFrame()

def calculate_summary_statistics(df):
    """Fallback function for summary statistics"""
    return {}

def categorize_transaction(desc, amount=0):
    """Fallback function for transaction categorization"""
    # Simple categorization based on description keywords
    desc_lower = str(desc).lower()
    
    # Income patterns
    if any(word in desc_lower for word in ['salary', 'credit', 'deposit', 'income', 'refund', 'cashback']):
        return {"category": "Income", "subcategory": "Other Income"}
    
    # Food patterns
    elif any(word in desc_lower for word in ['grocery', 'restaurant', 'food', 'dining', 'cafe', 'swiggy', 'zomato']):
        return {"category": "Food & Dining", "subcategory": "Dining"}
    
    # Transportation patterns
    elif any(word in desc_lower for word in ['fuel', 'petrol', 'gas', 'uber', 'ola', 'metro', 'bus']):
        return {"category": "Transportation", "subcategory": "Fuel"}
    
    # Shopping patterns
    elif any(word in desc_lower for word in ['amazon', 'flipkart', 'shopping', 'purchase', 'store']):
        return {"category": "Shopping", "subcategory": "Online"}
    
    # Education patterns
    elif any(word in desc_lower for word in ['education', 'school', 'college', 'course', 'tuition', 'fees']):
        return {"category": "Education", "subcategory": "Tuition"}
    
    # Insurance patterns
    elif any(word in desc_lower for word in ['insurance', 'lic', 'policy', 'premium']):
        return {"category": "LIC/Insurance", "subcategory": "Premium"}
    
    # Healthcare patterns
    elif any(word in desc_lower for word in ['medical', 'hospital', 'doctor', 'pharmacy', 'medicine']):
        return {"category": "Healthcare", "subcategory": "Medical"}
    
    # Utilities patterns
    elif any(word in desc_lower for word in ['electricity', 'water', 'gas', 'internet', 'mobile', 'phone']):
        return {"category": "Utilities", "subcategory": "Bills"}
    
    # Default to Other if amount is positive (income) or negative (expense)
    elif amount > 0:
        return {"category": "Income", "subcategory": "Other Income"}
    else:
        return {"category": "Other", "subcategory": "Miscellaneous"}

# Try to import backend modules dynamically to avoid static analysis warnings
def try_import_modules():
    """Dynamically import backend modules"""
    global get_transaction_data, load_processed_data, calculate_summary_statistics, categorize_transaction
    
    try:
        import importlib.util
        
        # Try to import data_extraction
        spec = importlib.util.spec_from_file_location("data_extraction", os.path.join(src_dir, "data_extraction.py"))
        if spec and spec.loader:
            data_extraction = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(data_extraction)
            get_transaction_data = data_extraction.get_transaction_data
            load_processed_data = data_extraction.load_processed_data
            print("✓ Successfully imported data_extraction module")
    except Exception as e:
        print(f"⚠ Using fallback for data_extraction: {e}")
    
    try:
        # Try to import analysis
        spec = importlib.util.spec_from_file_location("analysis", os.path.join(src_dir, "analysis.py"))
        if spec and spec.loader:
            analysis = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(analysis)
            calculate_summary_statistics = analysis.calculate_summary_statistics
            print("✓ Successfully imported analysis module")
    except Exception as e:
        print(f"⚠ Using fallback for analysis: {e}")
    
    try:
        # Try to import categories
        spec = importlib.util.spec_from_file_location("categories", os.path.join(src_dir, "categories.py"))
        if spec and spec.loader:
            categories = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(categories)
            categorize_transaction = categories.categorize_transaction
            print("✓ Successfully imported categories module")
    except Exception as e:
        print(f"⚠ Using fallback for categories: {e}")

# Initialize the modules
try_import_modules()

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Pydantic models for API responses
class TransactionResponse(BaseModel):
    id: str
    date: str
    description: str
    amount: float
    category: str
    account: str
    balance: float
    type: str  # "income" or "expense"

class TransactionMetrics(BaseModel):
    total_transactions: int
    total_income: float
    total_expenses: float
    net_savings: float
    monthly_averages: Dict[str, Any]
    yearly_averages: Dict[str, Any]

class TimelineData(BaseModel):
    dates: List[str]
    amounts: List[float]
    types: List[str]  # "income" or "expense"

class PaginationResponse(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    page_size: int

class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    pagination: PaginationResponse

def get_data_df():
    """Get transaction data from the backend"""
    try:
        # Get the correct path to processed_data.csv
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        processed_file = os.path.join(project_root, 'processed_data.csv')
        
        print(f"Looking for processed data at: {processed_file}")
        
        if os.path.exists(processed_file):
            try:
                df = pd.read_csv(processed_file)
                print(f"✓ Loaded {len(df)} transactions from processed_data.csv")
                
                # Ensure Transaction Date is properly formatted
                if 'Transaction Date' in df.columns:
                    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
                
                return df
            except Exception as e:
                print(f"Error reading processed_data.csv: {e}")
        else:
            print(f"Warning: {processed_file} not found")
        
        # Fallback to other methods if CSV doesn't exist or is empty
        print("Trying fallback data loading...")
        df = load_processed_data()
        if df.empty:
            df = get_transaction_data()
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def filter_dataframe(df: pd.DataFrame, 
                    start_date: Optional[date] = None,
                    end_date: Optional[date] = None,
                    account: Optional[str] = None,
                    category: Optional[str] = None,
                    search: Optional[str] = None,
                    min_amount: Optional[float] = None,
                    max_amount: Optional[float] = None) -> pd.DataFrame:
    """Apply filters to dataframe"""
    print(f"Backend filter_dataframe called with:")
    print(f"  start_date: {start_date}")
    print(f"  end_date: {end_date}")
    print(f"  account: {account}")
    print(f"  category: {category}")
    print(f"  search: {search}")
    print(f"  min_amount: {min_amount}")
    print(f"  max_amount: {max_amount}")
    
    if df.empty:
        print("DataFrame is empty, returning empty DataFrame")
        return df
    
    filtered_df = df.copy()
    print(f"Initial DataFrame shape: {filtered_df.shape}")
    
    # Date filtering
    if start_date and 'Transaction Date' in filtered_df.columns:
        filtered_df = filtered_df[pd.to_datetime(filtered_df['Transaction Date']) >= pd.to_datetime(start_date)]
        print(f"After start_date filter: {filtered_df.shape}")
    
    if end_date and 'Transaction Date' in filtered_df.columns:
        filtered_df = filtered_df[pd.to_datetime(filtered_df['Transaction Date']) <= pd.to_datetime(end_date)]
        print(f"After end_date filter: {filtered_df.shape}")
    
    # Category filtering
    if category and category != "All Categories":
        if 'Category' in filtered_df.columns:
            # Handle multiple categories separated by commas
            categories = [cat.strip() for cat in category.split(',') if cat.strip()]
            print(f"Filtering by categories: {categories}")
            if categories:
                # Make category comparison case-insensitive
                category_mask = filtered_df['Category'].fillna('').astype(str).str.lower().isin([cat.lower() for cat in categories])
                filtered_df = filtered_df[category_mask]
                print(f"After category filter: {filtered_df.shape}")
        elif 'category' in filtered_df.columns:  # Try lowercase column name as fallback
            categories = [cat.strip() for cat in category.split(',') if cat.strip()]
            print(f"Filtering by lowercase 'category' column: {categories}")
            if categories:
                category_mask = filtered_df['category'].fillna('').astype(str).str.lower().isin([cat.lower() for cat in categories])
                filtered_df = filtered_df[category_mask]
                print(f"After category filter: {filtered_df.shape}")
    
    # Account filtering  
    if account and account != "All Accounts":
        if 'Account' in filtered_df.columns:
            # Handle multiple accounts separated by commas
            accounts = [acc.strip() for acc in account.split(',') if acc.strip()]
            print(f"Filtering by accounts: {accounts}")
            if accounts:
                filtered_df = filtered_df[filtered_df['Account'].isin(accounts)]
                print(f"After account filter: {filtered_df.shape}")
    
    # Search filtering
    if search and 'Description' in filtered_df.columns:
        search_mask = filtered_df['Description'].str.contains(search, case=False, na=False)
        filtered_df = filtered_df[search_mask]
        print(f"After search filter: {filtered_df.shape}")
    
    # Min/Max amount filtering
    if min_amount is not None and 'Amount' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Amount'] >= min_amount]
        print(f"After min_amount filter: {filtered_df.shape}")
    
    if max_amount is not None and 'Amount' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Amount'] <= max_amount]
        print(f"After max_amount filter: {filtered_df.shape}")
    
    print(f"Final filtered DataFrame shape: {filtered_df.shape}")
    return filtered_df

@router.get("/", response_model=TransactionListResponse)
async def get_transactions(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    account: Optional[str] = Query(None, description="Account filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    search: Optional[str] = Query(None, description="Search text filter"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    sort_by: str = Query("date", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)")
):
    """Get filtered transactions with pagination"""
    print(f"Backend endpoint called with parameters:")
    print(f"  start_date: {start_date}")
    print(f"  end_date: {end_date}")
    print(f"  account: {account}")
    print(f"  category: {category}")
    print(f"  search: {search}")
    print(f"  min_amount: {min_amount}")
    print(f"  max_amount: {max_amount}")
    print(f"  page: {page}")
    print(f"  page_size: {page_size}")
    
    try:
        # Get transaction data
        df = get_data_df()
        
        if df.empty:
            print("No data available, returning empty response")
            return TransactionListResponse(
                transactions=[],
                pagination=PaginationResponse(
                    total_items=0,
                    total_pages=0,
                    current_page=page,
                    page_size=page_size
                )
            )
        
        # Apply filters
        filtered_df = filter_dataframe(df, start_date, end_date, account, category, search, min_amount, max_amount)
        
        # Always ensure Category column exists and is populated
        if 'Category' not in filtered_df.columns:
            if 'Description' in filtered_df.columns:
                print("Adding categories to transactions...")
                categories = []
                for _, row in filtered_df.iterrows():
                    desc = str(row.get('Description', ''))
                    amount = float(row.get('Amount', 0))
                    cat_result = categorize_transaction(desc, int(amount))
                    if isinstance(cat_result, dict):
                        categories.append(cat_result.get('category', 'Other'))
                    else:
                        categories.append(str(cat_result) if cat_result else 'Other')
                filtered_df['Category'] = categories
            else:
                filtered_df['Category'] = 'Other'
        else:
            # Fill any missing categories
            missing_categories = filtered_df['Category'].isna() | (filtered_df['Category'] == '')
            if missing_categories.any() and 'Description' in filtered_df.columns:
                for idx in filtered_df[missing_categories].index:
                    row = filtered_df.loc[idx]
                    desc = str(row.get('Description', ''))
                    amount = float(row.get('Amount', 0))
                    cat_result = categorize_transaction(desc, int(amount))
                    if isinstance(cat_result, dict):
                        filtered_df.loc[idx, 'Category'] = cat_result.get('category', 'Other')
                    else:
                        filtered_df.loc[idx, 'Category'] = str(cat_result) if cat_result else 'Other'
        
        # Sort data
        sort_column = 'Transaction Date' if sort_by == 'date' else sort_by
        if sort_column in filtered_df.columns:
            ascending = sort_order.lower() == "asc"
            filtered_df = filtered_df.sort_values(by=sort_column, ascending=ascending)
        
        # Pagination
        total_items = len(filtered_df)
        total_pages = (total_items + page_size - 1) // page_size
        
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        
        page_df = filtered_df.iloc[start_idx:end_idx]
          # Format data for response
        transactions = []
        for idx, row in page_df.iterrows():
            # Format date properly
            date_val = row.get('Transaction Date', '')
            date_str = ''
            if pd.notna(date_val) and date_val != '':
                try:
                    if isinstance(date_val, str):
                        date_val = pd.to_datetime(date_val)
                    if hasattr(date_val, 'strftime'):
                        date_str = date_val.strftime("%Y-%m-%d")
                except:
                    date_str = str(date_val) if date_val else ''
            
            # Get amount and ensure it's a valid number
            amount = 0.0
            try:
                amount = float(row.get('Amount', 0))
            except (ValueError, TypeError):
                amount = 0.0
            
            # Get balance and ensure it's a valid number
            balance = 0.0
            try:
                balance = float(row.get('Balance', 0))
            except (ValueError, TypeError):
                balance = 0.0

            transactions.append(TransactionResponse(
                id=str(idx),
                date=date_str,
                description=str(row.get('Description', '')),
                amount=amount,
                category=str(row.get('Category', 'Other')),
                account=str(row.get('Account', 'Primary Account')),
                balance=balance,
                type="income" if amount > 0 else "expense"
            ))
        
        return TransactionListResponse(
            transactions=transactions,
            pagination=PaginationResponse(
                total_items=total_items,
                total_pages=total_pages,
                current_page=page,
                page_size=page_size
            )
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving transactions: {str(e)}")

@router.get("/metrics", response_model=TransactionMetrics)
async def get_transaction_metrics(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    account: Optional[str] = Query(None, description="Account filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    search: Optional[str] = Query(None, description="Search text filter"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter")
):
    """Get transaction metrics including monthly and yearly averages"""
    try:
        # Get transaction data
        df = get_data_df()
        
        if df.empty:
            return TransactionMetrics(
                total_transactions=0,
                total_income=0,
                total_expenses=0,
                net_savings=0,
                monthly_averages={
                    "months": 0,
                    "transactions": 0,
                    "income": 0,
                    "expenses": 0,
                    "savings": 0
                },
                yearly_averages={
                    "years": 0,
                    "transactions": 0,
                    "income": 0,
                    "expenses": 0,
                    "savings": 0
                }
            )
        
        # Apply filters
        filtered_df = filter_dataframe(df, start_date, end_date, account, category, search, min_amount, max_amount)
        
        # Calculate metrics
        total_transactions = len(filtered_df)
        total_income = filtered_df[filtered_df['Amount'] > 0]['Amount'].sum() if not filtered_df.empty else 0
        total_expenses = abs(filtered_df[filtered_df['Amount'] < 0]['Amount'].sum()) if not filtered_df.empty else 0
        net_savings = total_income - total_expenses
        
        # Calculate date range for averages
        monthly_averages = {"months": 0, "transactions": 0, "income": 0, "expenses": 0, "savings": 0}
        yearly_averages = {"years": 0, "transactions": 0, "income": 0, "expenses": 0, "savings": 0}
        
        if not filtered_df.empty and 'Transaction Date' in filtered_df.columns:
            try:
                dates = pd.to_datetime(filtered_df['Transaction Date']).dropna()
                if not dates.empty:
                    min_date = dates.min()
                    max_date = dates.max()
                    
                    # Monthly averages
                    months_diff = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month + 1
                    if months_diff > 0:
                        monthly_averages = {
                            "months": months_diff,
                            "transactions": total_transactions / months_diff,
                            "income": total_income / months_diff,
                            "expenses": total_expenses / months_diff,
                            "savings": net_savings / months_diff
                        }
                    
                    # Yearly averages
                    # Calculate actual years difference (more accurate than just year subtraction)
                    days_diff = (max_date - min_date).days
                    years_diff = max(1, round(days_diff / 365.25))
                    
                    # Print debug information
                    print(f"Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
                    print(f"Days between: {days_diff}, calculated years: {years_diff}")
                    
                    yearly_averages = {
                        "years": years_diff,
                        "transactions": total_transactions / years_diff,
                        "income": total_income / years_diff,
                        "expenses": total_expenses / years_diff,
                        "savings": net_savings / years_diff
                    }
            except Exception as e:
                print(f"Error calculating date ranges: {e}")
        
        return TransactionMetrics(
            total_transactions=total_transactions,
            total_income=float(total_income),
            total_expenses=float(total_expenses),
            net_savings=float(net_savings),
            monthly_averages=monthly_averages,
            yearly_averages=yearly_averages
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")

class TimelineScatterData(BaseModel):
    credits: list
    debits: list

@router.get("/timeline", response_model=TimelineScatterData)
async def get_transaction_timeline(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    account: Optional[str] = Query(None, description="Account filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    search: Optional[str] = Query(None, description="Search text filter"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter")
):
    """Get timeline data for scatter plot visualization (credits and debits separated)"""
    try:
        df = get_data_df()
        
        if df.empty:
            return TimelineScatterData(credits=[], debits=[])
        
        filtered_df = filter_dataframe(df, start_date, end_date, account, category, search, min_amount, max_amount)
        
        if filtered_df.empty:
            return TimelineScatterData(credits=[], debits=[])
        
        # Ensure Category column exists
        if 'Category' not in filtered_df.columns and 'Description' in filtered_df.columns:
            categories = []
            for _, row in filtered_df.iterrows():
                desc = str(row.get('Description', ''))
                amount = float(row.get('Amount', 0))
                cat_result = categorize_transaction(desc, int(amount))
                if isinstance(cat_result, dict):
                    categories.append(cat_result.get('category', 'Other'))
                else:
                    categories.append(str(cat_result) if cat_result else 'Other')
            filtered_df['Category'] = categories
        
        credits = []
        debits = []
        
        for _, row in filtered_df.iterrows():
            try:
                # Get and validate date
                date_val = row.get('Transaction Date')
                if pd.isna(date_val) or date_val == '':
                    continue
                    
                if isinstance(date_val, str):
                    try:
                        date_val = pd.to_datetime(date_val)
                    except:
                        continue
                elif not hasattr(date_val, 'strftime'):
                    continue
                
                # Get and validate amount
                amount = row.get('Amount', 0)
                if pd.isna(amount):
                    continue
                    
                try:
                    amount = float(amount)
                except (ValueError, TypeError):
                    continue
                
                # Create data point
                point = {
                    "x": date_val.strftime("%Y-%m-%d"),
                    "y": abs(amount),  # Always positive for chart display
                    "description": str(row.get('Description', '')),
                    "category": str(row.get('Category', 'Other'))
                }
                
                # Categorize as income or expense
                if amount > 0:
                    credits.append(point)
                else:
                    debits.append(point)
                    
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
        
        print(f"Timeline data generated: {len(credits)} credits, {len(debits)} debits")
        return TimelineScatterData(credits=credits, debits=debits)
    
    except Exception as e:
        print(f"Error in get_transaction_timeline: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting timeline data: {str(e)}")

@router.get("/filter-options")
async def get_filter_options():
    """Get available filter options for categories and accounts, and min/max date"""
    try:
        df = get_data_df()
        
        if df.empty:
            return {
                "categories": ["All Categories"],
                "accounts": ["All Accounts"],
                "date_range": {"min": None, "max": None}
            }
        
        # Ensure Category column exists
        if 'Category' not in df.columns and 'Description' in df.columns:
            categories = []
            for _, row in df.iterrows():
                desc = str(row.get('Description', ''))
                amount = float(row.get('Amount', 0))
                cat_result = categorize_transaction(desc, int(amount))
                if isinstance(cat_result, dict):
                    categories.append(cat_result.get('category', 'Other'))
                else:
                    categories.append(str(cat_result) if cat_result else 'Other')
            df['Category'] = categories
        
        categories = ["All Categories"] + sorted(df['Category'].dropna().unique().tolist())
        accounts = ["All Accounts"] + sorted(df['Account'].dropna().unique().tolist()) if 'Account' in df.columns else ["All Accounts"]
        
        # Date range
        min_date = None
        max_date = None
        if 'Transaction Date' in df.columns:
            dates = pd.to_datetime(df['Transaction Date'], errors='coerce').dropna()
            if not dates.empty:
                min_date = dates.min().strftime("%Y-%m-%d")
                max_date = dates.max().strftime("%Y-%m-%d")
        
        return {
            "categories": categories,
            "accounts": accounts,
            "date_range": {"min": min_date, "max": max_date}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving filter options: {str(e)}")

@router.get("/debug")
async def debug_data_loading():
    """Debug endpoint to check data loading"""
    try:
        # Get the path to processed_data.csv
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        processed_file = os.path.join(project_root, 'processed_data.csv')
        
        # Check if file exists
        file_exists = os.path.exists(processed_file)
        
        # Try loading the data
        df = get_data_df()
        
        # Get column information
        columns = list(df.columns) if not df.empty else []
        sample = df.head(1).to_dict('records') if not df.empty else []
        
        return {
            "file_exists": file_exists,
            "file_path": processed_file,
            "row_count": len(df),
            "columns": columns,
            "sample": sample
        }
    except Exception as e:
        return {"error": str(e)}
