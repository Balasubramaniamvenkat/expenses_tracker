"""
Hierarchical Categories API for drill-down chart support
Provides Category → Subcategory → Merchant hierarchy for dashboard visualization

Updated to use refined categorization with:
- Investment: Zerodha, SIP, Gold, Jewelry
- Insurance: LIC, Health, Vehicle (separate from Investments)
- Education: Schools, Training, Courses
- Healthcare: Hospital, Clinic, Pharmacy, Labs
- Smart UPI differentiation (transfers vs purchases)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import re

router = APIRouter(prefix="/api/categories", tags=["categories-hierarchy"])

# Add SRC to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'SRC')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import the shared categorizer so hierarchy and transaction filters use the
# same category and subcategory assignments as the rest of the application.
from refined_categories import (
    MERCHANT_LOOKUP,
    REFINED_CATEGORIES,
    _extract_upi_payee_name,
    _extract_upi_vpa_identifier,
    _merchant_matches,
    get_category_colors,
    get_category_group,
    get_category_icons,
)
from categories import categorize_transaction
from data_extraction import get_processed_data_path as get_canonical_processed_data_path

def get_processed_data_path() -> Optional[str]:
    """Return the single generated dataset path used by the upload pipeline."""
    path = get_canonical_processed_data_path()
    return path if os.path.exists(path) else None


def load_transaction_data() -> Optional[pd.DataFrame]:
    """Load and clean transaction data"""
    csv_path = get_processed_data_path()
    if not csv_path:
        return None
    
    try:
        df = pd.read_csv(csv_path)
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
        df = df.dropna(subset=['Amount', 'Transaction Date'])
        if 'Description' not in df.columns:
            df['Description'] = ''
        if 'Category' not in df.columns:
            df['Category'] = ''
        if 'Subcategory' not in df.columns:
            df['Subcategory'] = ''

        missing_categories = df['Category'].isna() | df['Category'].astype(str).str.strip().eq('')
        if missing_categories.any():
            for index in df.index[missing_categories]:
                result = categorize_transaction(str(df.at[index, 'Description']), float(df.at[index, 'Amount']))
                df.at[index, 'Category'] = result['category']
                df.at[index, 'Subcategory'] = result['subcategory']

        missing_subcategories = df['Subcategory'].isna() | df['Subcategory'].astype(str).str.strip().eq('')
        if missing_subcategories.any():
            for index in df.index[missing_subcategories]:
                result = categorize_transaction(str(df.at[index, 'Description']), float(df.at[index, 'Amount']))
                df.at[index, 'Subcategory'] = result['subcategory']
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


# Category color and icon mapping - always use the function (works with fallback)
CATEGORY_COLORS = get_category_colors()
CATEGORY_ICONS = get_category_icons()

# Subcategory color variations (lighter shades)
def get_subcategory_color(parent_color: str, index: int) -> str:
    """Generate a color variation for subcategories"""
    # Lighten the color based on index
    base_colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    return base_colors[index % len(base_colors)]


def extract_merchant_name(description: str) -> str:
    """Extract the UPI payee or a known merchant without mistaking the bank for it."""
    if not isinstance(description, str):
        description = '' if pd.isna(description) else str(description)
    description = description.strip()
    if not description:
        return 'Other'

    payee = _extract_upi_payee_name(description)
    if payee:
        normalized_payee = re.sub(r'\s+', ' ', payee).strip(' /-.')
        payee_lower = normalized_payee.lower()
        vpa = (_extract_upi_vpa_identifier(description) or '').lower()
        if 'bundl technologies' in payee_lower and 'swiggy' in vpa:
            return 'Swiggy Instamart' if 'instamart' in vpa else 'Swiggy'
        display_aliases = {
            'innovative retail': 'BigBasket',
            'bigbasket': 'BigBasket',
            'big basket': 'BigBasket',
            'bbnow': 'BigBasket',
            'bb now': 'BigBasket',
            'swiggy instamart': 'Swiggy Instamart',
            'swiggyinstamart': 'Swiggy Instamart',
            'swiggy': 'Swiggy',
            'zomato': 'Zomato',
            'grofers india': 'Grofers',
            'grofers': 'Grofers',
            'natures basket': "Nature's Basket",
            'cococart': 'CocoCart',
            'hopcoms': 'Hopcoms',
            'airtel': 'Airtel',
            'jio': 'Jio',
            'vodafone': 'Vodafone Idea (Vi)',
            'vi': 'Vodafone Idea (Vi)',
            'irctc': 'IRCTC',
            'eversub india': 'Subway',
        }
        for alias in sorted(display_aliases, key=len, reverse=True):
            if payee_lower == alias or payee_lower.startswith(alias + ' '):
                return display_aliases[alias]
        if description.upper().startswith('UPI/'):
            return normalized_payee.title()
        return normalized_payee.title()

    description_lower = description.lower()
    if description.upper().startswith('UPI'):
        return 'UPI merchant'

    merchant_aliases = {
        'paytmirctcecatering': 'IRCTC Catering',
        'payuirctc': 'IRCTC',
        'cornerhouseicecreams': 'Corner House',
    }
    for alias in sorted(merchant_aliases, key=len, reverse=True):
        if alias in description_lower:
            return merchant_aliases[alias]

    known_aliases = sorted(MERCHANT_LOOKUP, key=len, reverse=True)
    for alias in known_aliases:
        if _merchant_matches(alias, description_lower):
            return alias.title()

    words = [word for word in description.split() if len(word) > 2 and not word.isdigit()]
    if words:
        return ' '.join(words[:2]).title()
    return 'Other'


INCOME_GROUP_BY_SUBCATEGORY = {
    'Salary': 'Salary & Earnings',
    'Dividends': 'Investment Income',
    'Interest': 'Investment Income',
    'Investment Returns': 'Investment Income',
    'Refunds': 'Refunds & Other',
    'Other Income': 'Refunds & Other',
}
INCOME_GROUP_STYLE = {
    'Salary & Earnings': {'icon': '💼', 'color': '#2E7D32'},
    'Investment Income': {'icon': '📈', 'color': '#1976D2'},
    'Refunds & Other': {'icon': '↩️', 'color': '#8D6E63'},
}


def income_group_name(subcategory: Any) -> str:
    """Map an Income subcategory to the top-level bucket shown in income drill-downs."""
    if not isinstance(subcategory, str):
        return 'Refunds & Other'
    return INCOME_GROUP_BY_SUBCATEGORY.get(subcategory.strip(), 'Refunds & Other')


def _tidy_name(text: str) -> str:
    return ' '.join(word.capitalize() for word in re.sub(r'\s+', ' ', text).strip(' -/.').split())


def extract_income_source(description: str) -> str:
    """Name who paid money in (employer, company, broker, bank) from a credit narration."""
    if not isinstance(description, str):
        description = '' if pd.isna(description) else str(description)
    text = re.sub(r'\s+', ' ', description).strip()
    upper = text.upper()
    if not text:
        return 'Unknown source'

    if upper.startswith(('NEFT CR-', 'NEFT CR/')):
        parts = re.split(r'[-/]', text)
        if len(parts) > 2 and parts[2].strip():
            return _tidy_name(parts[2])

    if upper.startswith('ACH C'):
        company = re.sub(r'^ACH C-?\s*', '', text, flags=re.IGNORECASE)
        company = re.split(r'-\d', company)[0]
        company = re.sub(r'[\s\d]+$', '', company)
        # A single glued token such as COLGATE2NDINTDIV2425 -> its leading letters
        single_token = re.match(r'^([A-Za-z]{4,})\d', company)
        if ' ' not in company and single_token:
            company = single_token.group(1)
        if company:
            return _tidy_name(company)

    if upper.startswith(('REV-', 'REV/')):
        return 'UPI Reversal'

    if re.search(r'\bINTEREST\b|\bINT\.?\s?PD\b', upper):
        return 'Bank Interest'

    dividend_issuer = re.match(r'^(.*?)\s+DIV\d', text, flags=re.IGNORECASE)
    if dividend_issuer and dividend_issuer.group(1).strip():
        return _tidy_name(dividend_issuer.group(1))

    return extract_merchant_name(text)


def extract_display_name(description: str, category: Any) -> str:
    """Merchant for spending rows, paying source for income rows."""
    if get_category_group(str(category)) == 'Income':
        return extract_income_source(description)
    return extract_merchant_name(description)


def get_subcategory_from_description(description: str, category: str) -> str:
    """Determine subcategory based on description and category"""
    desc_lower = description.lower()
    
    # Define subcategory mappings
    subcategory_mappings = {
        'Food': {
            'Groceries': ['grocery', 'supermarket', 'dmart', 'bigbasket', 'more', 'reliance fresh'],
            'Dining Out': ['swiggy', 'zomato', 'restaurant', 'hotel', 'cafe', 'food court'],
            'Fast Food': ['dominos', 'pizza', 'burger', 'kfc', 'mcdonalds'],
            'Beverages': ['starbucks', 'ccd', 'coffee', 'tea'],
        },
        'Shopping': {
            'Online Shopping': ['amazon', 'flipkart', 'myntra', 'ajio', 'meesho'],
            'Electronics': ['mobile', 'laptop', 'electronic', 'croma', 'reliance digital'],
            'Clothing': ['clothing', 'fashion', 'apparel', 'max', 'lifestyle'],
            'General': ['store', 'mart', 'shop'],
        },
        'Transportation': {
            'Fuel': ['petrol', 'diesel', 'fuel', 'hp', 'bharat petroleum', 'indian oil'],
            'Ride Sharing': ['uber', 'ola', 'rapido', 'taxi', 'cab'],
            'Public Transport': ['metro', 'bus', 'train', 'irctc', 'railway'],
            'Parking & Toll': ['parking', 'toll', 'fastag'],
        },
        'Utilities': {
            'Electricity': ['electricity', 'bescom', 'power', 'electric'],
            'Water': ['water', 'bwssb'],
            'Internet & Phone': ['airtel', 'jio', 'vi', 'vodafone', 'broadband', 'internet', 'mobile', 'recharge'],
            'Gas': ['gas', 'lpg', 'indane', 'bharat gas'],
        },
        'Entertainment': {
            'Streaming': ['netflix', 'hotstar', 'prime', 'spotify', 'youtube', 'zee5'],
            'Movies': ['pvr', 'inox', 'cinema', 'movie', 'bookmyshow'],
            'Gaming': ['playstation', 'xbox', 'game', 'gaming'],
            'Events': ['event', 'concert', 'show', 'ticket'],
        },
        'Healthcare': {
            'Hospital': ['hospital', 'clinic', 'apollo', 'fortis', 'manipal'],
            'Pharmacy': ['pharmacy', 'medical', 'medicine', 'medplus', 'netmeds', '1mg'],
            'Diagnostic': ['lab', 'diagnostic', 'test', 'scan', 'thyrocare'],
            'Wellness': ['gym', 'fitness', 'yoga', 'spa', 'salon'],
        },
        'Investments': {
            'Mutual Funds': ['mutual fund', 'sip', 'amc', 'mf'],
            'Stocks': ['zerodha', 'groww', 'upstox', 'angel', 'shares', 'trading'],
            'Gold': ['gold', 'sovereign', 'mmtc'],
            'Fixed Deposits': ['fd', 'fixed deposit', 'deposit'],
        },
        'Education': {
            'Courses': ['course', 'udemy', 'coursera', 'training'],
            'Books': ['book', 'amazon kindle'],
            'School/College': ['school', 'college', 'university', 'fees', 'tuition'],
        },
        'Money Transfer': {
            'UPI': ['upi', 'phonepe', 'gpay', 'paytm'],
            'Bank Transfer': ['neft', 'imps', 'rtgs', 'transfer'],
            'Wallet': ['wallet', 'topup'],
        },
        'Income': {
            'Salary': ['salary', 'pay', 'wages'],
            'Interest': ['interest', 'dividend'],
            'Refund': ['refund', 'cashback', 'reversal'],
            'Other Income': [],
        }
    }
    
    if category in subcategory_mappings:
        for subcategory, keywords in subcategory_mappings[category].items():
            if any(kw in desc_lower for kw in keywords):
                return subcategory
    
    return 'Other'


def _months_covered(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> float:
    dates = df['Transaction Date'].dropna()
    if dates.empty and not (start_date and end_date):
        return 1
    first = pd.to_datetime(start_date) if start_date else dates.min()
    last = pd.to_datetime(end_date) if end_date else dates.max()
    months_between = (last.year - first.year) * 12 + last.month - first.month
    if start_date and end_date:
        if months_between == 0:
            return max(1 / first.days_in_month, (last.day - first.day + 1) / first.days_in_month)
        return (
            (first.days_in_month - first.day + 1) / first.days_in_month
            + months_between - 1
            + last.day / last.days_in_month
        )
    return float(max(1, months_between + 1))


@router.get("/hierarchy")
async def get_category_hierarchy(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    transaction_type: Optional[str] = Query("expense", description="Transaction type: income, expense, investment, all")
) -> Dict[str, Any]:
    """
    Get hierarchical category data for drill-down charts
    Returns: Category → Subcategory → Merchant hierarchy with amounts and percentages
    """
    
    print(f"📊 Category Hierarchy API called")
    print(f"   - Start Date: {start_date}")
    print(f"   - End Date: {end_date}")
    print(f"   - Transaction Type: {transaction_type}")
    
    df = load_transaction_data()
    
    if df is None or df.empty:
        return {
            "success": False,
            "message": "No transaction data found",
            "hierarchy": [],
            "summary": {}
        }
    
    # Filter by date range
    if start_date:
        df = df[df['Transaction Date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Transaction Date'] < pd.to_datetime(end_date) + pd.Timedelta(days=1)]
    months_covered = _months_covered(df, start_date, end_date)
    
    # Filter by transaction type
    group_column = 'Category'
    if transaction_type == "income":
        df = df[
            df['Amount'].gt(0)
            & df['Category'].map(get_category_group).eq('Income')
        ].copy()
        # Every income row shares the category "Income", so bucket by source type.
        df['IncomeGroup'] = df['Subcategory'].map(income_group_name)
        group_column = 'IncomeGroup'
    elif transaction_type == "expense":
        df = df[df['Amount'] < 0].copy()
        df['Amount'] = df['Amount'].abs()  # Make amounts positive for display
        df = df[df['Category'].map(get_category_group).eq('Expense')]
    elif transaction_type == "investment":
        df = df[df['Amount'] < 0].copy()
        df['Amount'] = df['Amount'].abs()
        df = df[df['Category'].map(get_category_group).eq('Investment')]
    
    if df.empty:
        return {
            "success": True,
            "message": "No transactions found for the selected criteria",
            "hierarchy": [],
            "summary": {"monthsCovered": months_covered}
        }
    
    total_amount = df['Amount'].sum()
    
    # Build hierarchy
    hierarchy = []
    
    # Group by category
    if 'Category' not in df.columns:
        df['Category'] = 'Other'
    
    category_groups = df.groupby(group_column)
    
    for category, cat_df in category_groups:
        income_style = INCOME_GROUP_STYLE.get(str(category)) if group_column == 'IncomeGroup' else None
        category_color = income_style['color'] if income_style else CATEGORY_COLORS.get(category, '#667eea')
        category_icon = income_style['icon'] if income_style else CATEGORY_ICONS.get(category, '📊')
        cat_amount = float(cat_df['Amount'].sum())
        cat_percentage = (cat_amount / total_amount * 100) if total_amount > 0 else 0
        
        # Build subcategories - using explicit dict structure
        subcategories = []
        subcat_data: Dict[str, Dict[str, Any]] = {}
        
        for _, row in cat_df.iterrows():
            description = row.get('Description', '')
            amount = float(row['Amount'])
            
            # Determine subcategory
            saved_subcategory = row.get('Subcategory', '')
            subcategory = (
                str(saved_subcategory).strip()
                if pd.notna(saved_subcategory) and str(saved_subcategory).strip()
                else get_subcategory_from_description(description, row['Category'])
            )
            
            # Extract merchant (or paying source for income)
            merchant = extract_display_name(description, row['Category'])
            
            # Initialize subcategory data if not exists
            if subcategory not in subcat_data:
                subcat_data[subcategory] = {
                    'amount': 0.0,
                    'transactions': [],
                    'merchants': {}
                }
            
            subcat_data[subcategory]['amount'] += amount
            subcat_data[subcategory]['transactions'].append({
                'date': row['Transaction Date'].strftime('%Y-%m-%d') if pd.notna(row['Transaction Date']) else '',
                'description': description,
                'amount': amount,
                'merchant': merchant
            })
            
            # Initialize merchant data if not exists
            if merchant not in subcat_data[subcategory]['merchants']:
                subcat_data[subcategory]['merchants'][merchant] = {'amount': 0.0, 'count': 0}
            
            subcat_data[subcategory]['merchants'][merchant]['amount'] += amount
            subcat_data[subcategory]['merchants'][merchant]['count'] += 1
        
        # Convert subcategory data to list
        sorted_subcats = sorted(subcat_data.items(), key=lambda x: -x[1]['amount'])
        for idx, (subcat_name, subcat_info) in enumerate(sorted_subcats):
            subcat_info['transactions'].sort(key=lambda txn: txn['date'], reverse=True)
            subcat_amount = float(subcat_info['amount'])
            subcat_percentage = (subcat_amount / cat_amount * 100) if cat_amount > 0 else 0
            
            # Build merchant list
            merchants = []
            sorted_merchants = sorted(subcat_info['merchants'].items(), key=lambda x: -x[1]['amount'])
            for merchant_name, merchant_info in sorted_merchants:
                merchant_percentage = (merchant_info['amount'] / subcat_amount * 100) if subcat_amount > 0 else 0
                merchants.append({
                    'name': merchant_name,
                    'amount': float(merchant_info['amount']),
                    'averageMonthlyAmount': float(merchant_info['amount'] / months_covered),
                    'count': merchant_info['count'],
                    'percentage': round(merchant_percentage, 1),
                    'color': get_subcategory_color(category_color, len(merchants))
                })
            
            subcategories.append({
                'id': f"{category}_{subcat_name}".replace(' ', '_').lower(),
                'name': subcat_name,
                'amount': float(subcat_amount),
                'averageMonthlyAmount': float(subcat_amount / months_covered),
                'percentage': round(subcat_percentage, 1),
                'percentageOfTotal': round((subcat_amount / total_amount * 100) if total_amount > 0 else 0, 1),
                'transactionCount': len(subcat_info['transactions']),
                'color': get_subcategory_color(category_color, idx),
                'merchants': merchants[:10],  # Top 10 merchants
                'transactions': subcat_info['transactions'][:20]
            })
        
        hierarchy.append({
            'id': category.replace(' ', '_').lower(),
            'name': category,
            'icon': category_icon,
            'color': category_color,
            'amount': float(cat_amount),
            'averageMonthlyAmount': float(cat_amount / months_covered),
            'percentage': round(cat_percentage, 1),
            'transactionCount': len(cat_df),
            'subcategories': subcategories
        })
    
    # Sort by amount descending
    hierarchy.sort(key=lambda x: -x['amount'])
    
    # Calculate summary statistics
    summary = {
        'totalAmount': float(total_amount),
        'monthsCovered': months_covered,
        'categoryCount': len(hierarchy),
        'transactionCount': len(df),
        'dateRange': {
            'from': df['Transaction Date'].min().strftime('%Y-%m-%d'),
            'to': df['Transaction Date'].max().strftime('%Y-%m-%d')
        },
        'topCategory': hierarchy[0]['name'] if hierarchy else None,
        'transactionType': transaction_type
    }
    
    return {
        "success": True,
        "message": f"Found {len(hierarchy)} categories",
        "hierarchy": hierarchy,
        "summary": summary
    }


@router.get("/transactions-by-category")
async def get_transactions_by_category(
    category: str = Query(..., description="Category name"),
    subcategory: Optional[str] = Query(None, description="Subcategory name"),
    merchant: Optional[str] = Query(None, description="Merchant name"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, description="Maximum transactions to return"),
    offset: int = Query(0, description="Offset for pagination")
) -> Dict[str, Any]:
    """
    Get transactions filtered by category hierarchy level
    Used for transaction drawer when clicking on chart segments
    """
    
    df = load_transaction_data()
    
    if df is None or df.empty:
        return {
            "success": False,
            "message": "No transaction data found",
            "transactions": [],
            "total": 0
        }
    
    # Filter by date range
    if start_date:
        df = df[df['Transaction Date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Transaction Date'] < pd.to_datetime(end_date) + pd.Timedelta(days=1)]
    
    # Filter by the same category fields used to build the hierarchy.
    if category in INCOME_GROUP_STYLE:
        # Income buckets are virtual: they group several Income subcategories.
        df = df[
            df['Amount'].gt(0)
            & df['Category'].map(get_category_group).eq('Income')
            & df['Subcategory'].map(income_group_name).eq(category)
        ]
    else:
        df = df[df['Category'].fillna('').astype(str).str.lower() == category.lower()]

    if subcategory:
        df = df[
            df['Subcategory'].fillna('').astype(str).str.lower() == subcategory.lower()
        ]
    
    # Filter by merchant (paying source for income rows)
    if merchant:
        mask = df.apply(
            lambda row: extract_display_name(row['Description'], row['Category']).lower() == merchant.lower(),
            axis=1,
        ) if not df.empty else pd.Series(False, index=df.index)
        df = df[mask]
    
    total = len(df)
    
    # Sort by date descending
    df = df.sort_values(by='Transaction Date', ascending=False)  # type: ignore
    
    # Apply pagination
    df = df.iloc[offset:offset + limit]
    
    # Format transactions
    transactions = []
    for _, row in df.iterrows():
        transactions.append({
            'date': row['Transaction Date'].strftime('%Y-%m-%d'),
            'description': row.get('Description', ''),
            'amount': float(row['Amount']),
            'category': row['Category'] if category in INCOME_GROUP_STYLE else category,
            'subcategory': row.get('Subcategory') or get_subcategory_from_description(row.get('Description', ''), row['Category']),
            'merchant': extract_display_name(row.get('Description', ''), row['Category']),
        })
    
    return {
        "success": True,
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {
            "category": category,
            "subcategory": subcategory,
            "merchant": merchant
        }
    }


@router.get("/trend-comparison")
async def get_trend_comparison(
    months: int = Query(3, description="Number of months to compare")
) -> Dict[str, Any]:
    """
    Get trend comparison data for summary cards
    Compares current period with previous period
    """
    
    df = load_transaction_data()
    
    if df is None or df.empty:
        return {
            "success": False,
            "message": "No transaction data found",
            "comparisons": {}
        }
    
    # Determine date ranges
    latest_date = df['Transaction Date'].max()
    current_period_start = latest_date - timedelta(days=30 * months)
    previous_period_start = current_period_start - timedelta(days=30 * months)
    
    # Current period data
    current_df = df[(df['Transaction Date'] >= current_period_start) & (df['Transaction Date'] <= latest_date)]
    
    # Previous period data
    previous_df = df[(df['Transaction Date'] >= previous_period_start) & (df['Transaction Date'] < current_period_start)]
    
    def calculate_metrics(period_df: pd.DataFrame) -> Dict[str, float]:
        category_groups = period_df['Category'].map(get_category_group)
        income = period_df[
            period_df['Amount'].gt(0) & category_groups.eq('Income')
        ]['Amount'].sum()
        actual_expenses = abs(period_df[
            period_df['Amount'].lt(0) & category_groups.eq('Expense')
        ]['Amount'].sum())
        investments = abs(period_df[
            period_df['Amount'].lt(0) & category_groups.eq('Investment')
        ]['Amount'].sum())
        
        return {
            'income': float(income),
            'expenses': float(actual_expenses),
            'investments': float(investments),
            'savings': float(income - actual_expenses)
        }
    
    current_metrics = calculate_metrics(current_df)
    previous_metrics = calculate_metrics(previous_df)
    
    # Calculate percentage changes
    def calc_change(current: float, previous: float) -> Dict[str, Any]:
        if previous == 0:
            change_percent = 100 if current > 0 else 0
        else:
            change_percent = ((current - previous) / previous) * 100
        
        return {
            'current': current,
            'previous': previous,
            'change': round(change_percent, 1),
            'trend': 'up' if change_percent > 0 else ('down' if change_percent < 0 else 'stable'),
            'isPositive': (change_percent > 0 and current == current_metrics.get('income', 0)) or \
                         (change_percent < 0 and current == current_metrics.get('expenses', 0))
        }
    
    return {
        "success": True,
        "comparisons": {
            "income": calc_change(current_metrics['income'], previous_metrics['income']),
            "expenses": calc_change(current_metrics['expenses'], previous_metrics['expenses']),
            "investments": calc_change(current_metrics['investments'], previous_metrics['investments']),
            "savings": calc_change(current_metrics['savings'], previous_metrics['savings'])
        },
        "periods": {
            "current": {
                "from": current_period_start.strftime('%Y-%m-%d'),
                "to": latest_date.strftime('%Y-%m-%d')
            },
            "previous": {
                "from": previous_period_start.strftime('%Y-%m-%d'),
                "to": (current_period_start - timedelta(days=1)).strftime('%Y-%m-%d')
            }
        }
    }
