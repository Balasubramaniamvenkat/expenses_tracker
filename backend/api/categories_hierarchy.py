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

# Import refined categorizer for colors and icons
USE_REFINED = False
REFINED_CATEGORIES = {}

def _default_get_category_colors():
    return {
        'Income': '#4CAF50', 'Investments': '#2196F3', 'Insurance': '#00BCD4',
        'Education': '#9C27B0', 'Healthcare': '#9966FF', 'Money Transfer': '#607D8B',
        'Food & Dining': '#FF6384', 'Shopping': '#36A2EB', 'Transportation': '#FFCE56',
        'Utilities': '#4BC0C0', 'Entertainment': '#FF9F40', 'Housing': '#8BC34A',
        'Other': '#795548', 'Food': '#FF6384', 'LIC/Insurance': '#00BCD4'
    }

def _default_get_category_icons():
    return {
        'Income': '💰', 'Investments': '💎', 'Insurance': '🛡️', 'Education': '📚',
        'Healthcare': '🏥', 'Money Transfer': '💸', 'Food & Dining': '🍔',
        'Shopping': '🛒', 'Transportation': '🚗', 'Utilities': '💡',
        'Entertainment': '🎬', 'Housing': '🏠', 'Other': '📦',
        'Food': '🍔', 'LIC/Insurance': '🛡️'
    }

try:
    from refined_categories import (
        REFINED_CATEGORIES as _REFINED_CATEGORIES, 
        get_category_colors as _get_category_colors, 
        get_category_icons as _get_category_icons
    )
    REFINED_CATEGORIES = _REFINED_CATEGORIES
    get_category_colors = _get_category_colors
    get_category_icons = _get_category_icons
    USE_REFINED = True
except ImportError:
    get_category_colors = _default_get_category_colors
    get_category_icons = _default_get_category_icons


def get_processed_data_path() -> Optional[str]:
    """Find the processed_data.csv file"""
    possible_paths = [
        'processed_data.csv',
        '../processed_data.csv',
        '../../processed_data.csv',
        os.path.join(os.path.dirname(__file__), '..', '..', 'processed_data.csv')
    ]
    
    for path in possible_paths:
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            return full_path
    return None


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
    """Extract merchant name from transaction description"""
    description = description.upper()
    
    # Common patterns for UPI transactions
    upi_patterns = [
        r'UPI[-/]([A-Za-z0-9\s]+?)[-/@]',
        r'UPI/[^/]+/([^/]+)',
        r'TO\s+([A-Za-z\s]+)',
    ]
    
    # Known merchants mapping
    known_merchants = {
        'SWIGGY': 'Swiggy',
        'ZOMATO': 'Zomato',
        'AMAZON': 'Amazon',
        'FLIPKART': 'Flipkart',
        'UBER': 'Uber',
        'OLA': 'Ola',
        'NETFLIX': 'Netflix',
        'SPOTIFY': 'Spotify',
        'HOTSTAR': 'Hotstar',
        'PAYTM': 'Paytm',
        'PHONEPE': 'PhonePe',
        'GOOGLEPAY': 'Google Pay',
        'GOOGLE PAY': 'Google Pay',
        'ZERODHA': 'Zerodha',
        'GROWW': 'Groww',
        'UPSTOX': 'Upstox',
        'DMART': 'DMart',
        'BIGBASKET': 'Big Basket',
        'RELIANCE': 'Reliance',
        'AIRTEL': 'Airtel',
        'JIO': 'Jio',
        'VODAFONE': 'Vodafone',
        'VI': 'Vi',
        'BESCOM': 'BESCOM',
        'BWSSB': 'BWSSB',
        'IRCTC': 'IRCTC',
        'MAKEMYTRIP': 'MakeMyTrip',
        'HDFC': 'HDFC',
        'ICICI': 'ICICI',
        'SBI': 'SBI',
        'AXIS': 'Axis Bank',
        'KOTAK': 'Kotak',
        'LIC': 'LIC',
        'MUTUAL FUND': 'Mutual Fund',
        'SIP': 'SIP Investment',
        'ATM': 'ATM Withdrawal',
        'NEFT': 'NEFT Transfer',
        'IMPS': 'IMPS Transfer',
        'RTGS': 'RTGS Transfer',
    }
    
    # Check for known merchants
    for key, merchant in known_merchants.items():
        if key in description:
            return merchant
    
    # Try UPI patterns
    for pattern in upi_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2:
                return name.title()
    
    # Fallback: use first few meaningful words
    words = description.split()
    meaningful_words = [w for w in words[:3] if len(w) > 2 and not w.isdigit()]
    if meaningful_words:
        return ' '.join(meaningful_words[:2]).title()
    
    return 'Other'


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


@router.get("/hierarchy")
async def get_category_hierarchy(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    transaction_type: Optional[str] = Query("expense", description="Transaction type: income, expense, all")
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
        df = df[df['Transaction Date'] <= pd.to_datetime(end_date)]
    
    # Filter by transaction type
    if transaction_type == "income":
        df = df[df['Amount'] > 0]
    elif transaction_type == "expense":
        df = df[df['Amount'] < 0]
        df['Amount'] = df['Amount'].abs()  # Make amounts positive for display
    
    if df.empty:
        return {
            "success": True,
            "message": "No transactions found for the selected criteria",
            "hierarchy": [],
            "summary": {}
        }
    
    total_amount = df['Amount'].sum()
    
    # Build hierarchy
    hierarchy = []
    
    # Group by category
    if 'Category' not in df.columns:
        df['Category'] = 'Other'
    
    category_groups = df.groupby('Category')
    
    for category, cat_df in category_groups:
        cat_amount = float(cat_df['Amount'].sum())
        cat_percentage = (cat_amount / total_amount * 100) if total_amount > 0 else 0
        
        # Build subcategories - using explicit dict structure
        subcategories = []
        subcat_data: Dict[str, Dict[str, Any]] = {}
        
        for _, row in cat_df.iterrows():
            description = row.get('Description', '')
            amount = float(row['Amount'])
            
            # Determine subcategory
            subcategory = get_subcategory_from_description(description, category)
            
            # Extract merchant
            merchant = extract_merchant_name(description)
            
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
                    'count': merchant_info['count'],
                    'percentage': round(merchant_percentage, 1),
                    'color': get_subcategory_color(CATEGORY_COLORS.get(category, '#667eea'), len(merchants))
                })
            
            subcategories.append({
                'id': f"{category}_{subcat_name}".replace(' ', '_').lower(),
                'name': subcat_name,
                'amount': float(subcat_amount),
                'percentage': round(subcat_percentage, 1),
                'percentageOfTotal': round((subcat_amount / total_amount * 100) if total_amount > 0 else 0, 1),
                'transactionCount': len(subcat_info['transactions']),
                'color': get_subcategory_color(CATEGORY_COLORS.get(category, '#667eea'), idx),
                'merchants': merchants[:10],  # Top 10 merchants
                'transactions': subcat_info['transactions'][:20]  # Last 20 transactions
            })
        
        hierarchy.append({
            'id': category.replace(' ', '_').lower(),
            'name': category,
            'icon': CATEGORY_ICONS.get(category, '📊'),
            'color': CATEGORY_COLORS.get(category, '#667eea'),
            'amount': float(cat_amount),
            'percentage': round(cat_percentage, 1),
            'transactionCount': len(cat_df),
            'subcategories': subcategories
        })
    
    # Sort by amount descending
    hierarchy.sort(key=lambda x: -x['amount'])
    
    # Calculate summary statistics
    summary = {
        'totalAmount': float(total_amount),
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
        df = df[df['Transaction Date'] <= pd.to_datetime(end_date)]
    
    # Filter by category
    if 'Category' in df.columns:
        df = df[df['Category'].str.lower() == category.lower()]
    
    # Filter by subcategory (re-derive from description)
    if subcategory:
        mask = df['Description'].apply(
            lambda x: get_subcategory_from_description(x, category).lower() == subcategory.lower()
        )
        df = df[mask]
    
    # Filter by merchant
    if merchant:
        mask = df['Description'].apply(
            lambda x: extract_merchant_name(x).lower() == merchant.lower()
        )
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
            'category': category,
            'subcategory': get_subcategory_from_description(row.get('Description', ''), category),
            'merchant': extract_merchant_name(row.get('Description', '')),
            'balance': float(row.get('Balance', 0)) if 'Balance' in row else None
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
        income = period_df[period_df['Amount'] > 0]['Amount'].sum()
        expenses = abs(period_df[period_df['Amount'] < 0]['Amount'].sum())
        
        # Investment detection
        if 'Category' in period_df.columns:
            investment_mask = period_df['Category'].str.lower().str.contains('investment', na=False)
        else:
            investment_keywords = ['zerodha', 'mutual fund', 'investment', 'stocks', 'gold', 'sip']
            investment_mask = period_df['Description'].str.lower().str.contains('|'.join(investment_keywords), na=False)
        
        investments = abs(period_df[investment_mask]['Amount'].sum())
        actual_expenses = expenses - investments
        
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
