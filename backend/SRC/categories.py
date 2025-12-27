"""
Transaction categorization rules and helper functions.
"""

import re
from typing import Dict, List, Optional

# Define category hierarchy
CATEGORIES = {
    'Income': {
        'keywords': ['salary', 'deposit', 'interest', 'dividend', 'refund'],
        'subcategories': ['Salary', 'Investment Income', 'Refunds', 'Other Income']
    },
    'Investments': {
        'keywords': ['zerodha', 'mutual fund', 'stocks', 'investment', 'dividend', 'interest', 
                    'gold', 'mmtc', 'tanishq gold', 'digital gold', 'sovereign gold', 'gold etf',
                    'gold bonds', 'gold deposit', 'gold saving', 'gold purchase',
                    'jewellers', 'grt jewellers', 'tanishq', 'kalyan jewellers', 'joyalukkas',
                    'razpbseindiacom', 'razorpay', 'broking', 'trading'],
        'subcategories': ['Stocks', 'Mutual Funds', 'Gold', 'Fixed Deposits', 'Other Investments']
    },
    'Housing': {
        'keywords': ['rent', 'mortgage', 'property', 'maintenance', 'repair'],
        'subcategories': ['Rent/Mortgage', 'Utilities', 'Maintenance', 'Insurance']
    },
    'Transportation': {
        'keywords': ['fuel', 'gas', 'parking', 'uber', 'lyft', 'taxi', 'bus', 'train'],
        'subcategories': ['Fuel', 'Public Transit', 'Ride Share', 'Maintenance']
    },    'Food': {
        'keywords': ['restaurant', 'grocery', 'food', 'meal', 'cafe', 'coffee',
                    'swiggy', 'zomato', 'dominos', 'pizza', 'mcdonald', 'kfc',
                    'subway', 'starbucks', 'ccd', 'cafe coffee day',
                    'natures basket', 'big basket', 'grofers', 'blinkit',
                    'fresh', 'market', 'supermarket', 'hypermarket',
                    'food delivery', 'restaurant', 'dining'],
        'subcategories': ['Groceries', 'Restaurants', 'Food Delivery', 'Coffee Shops']
    },
    'Shopping': {
        'keywords': ['amazon', 'walmart', 'target', 'clothing', 'retail'],
        'subcategories': ['Online Shopping', 'Clothing', 'Electronics', 'Home Goods']
    },
    'Entertainment': {
        'keywords': ['movie', 'netflix', 'spotify', 'game', 'entertainment'],
        'subcategories': ['Streaming Services', 'Movies/Events', 'Games', 'Hobbies']
    },
    'Healthcare': {
        'keywords': ['doctor', 'medical', 'pharmacy', 'health', 'dental'],
        'subcategories': ['Medical', 'Dental', 'Pharmacy', 'Insurance']
    },
    'Education': {
        'keywords': ['tuition', 'book', 'course', 'school'],
        'subcategories': ['Tuition', 'Books', 'Courses', 'Supplies']
    },
    'Utilities': {
        'keywords': ['electric', 'water', 'gas', 'internet', 'phone', 'utility'],
        'subcategories': ['Electricity', 'Water', 'Gas', 'Internet/Phone']
    },
    'Money Transfer': {
        'keywords': ['neft', 'imps', 'netbank', 'bank transfer', 'fund transfer'],
        'subcategories': ['Bank Transfer', 'NEFT', 'IMPS', 'Online Transfer']
    },
    'LIC/Insurance': {
        'keywords': ['lic', 'life insurance', 'insurance', 'policy premium'],
        'subcategories': ['LIC Premium', 'Health Insurance', 'Life Insurance', 'Other Insurance']
    },
    'Other': {
        'keywords': [],
        'subcategories': ['Miscellaneous', 'Fees', 'Unknown']
    }
}

def categorize_transaction(description: str, amount: float) -> Dict[str, str]:
    """
    Categorize a transaction based on its description and amount.
    
    Args:
        description (str): Transaction description
        amount (float): Transaction amount
    
    Returns:
        Dict with category and subcategory
    """
    description = description.lower()
    
    # Handle income transactions
    if amount > 0:
        # Check if it's investment-related income
        investment_income_keywords = ['dividend', 'interest', 'gold redemption', 'gold deposit maturity']
        if any(keyword in description for keyword in investment_income_keywords):
            return {'category': 'Income', 'subcategory': 'Investment Income'}
        return {'category': 'Income', 'subcategory': 'Other Income'}
    
    # For expense transactions, check all categories systematically
    # Priority order: Money Transfer, LIC/Insurance, Investments, then other categories
    
    # Check Money Transfer category first (high priority for NEFT/IMPS)
    if 'Money Transfer' in CATEGORIES:
        for keyword in CATEGORIES['Money Transfer']['keywords']:
            if keyword in description:
                # Check for specific subcategory matches
                for subcategory in CATEGORIES['Money Transfer']['subcategories']:
                    if subcategory.lower() in description:
                        return {'category': 'Money Transfer', 'subcategory': subcategory}
                return {'category': 'Money Transfer', 'subcategory': 'Bank Transfer'}
    
    # Check LIC/Insurance category
    if 'LIC/Insurance' in CATEGORIES:
        for keyword in CATEGORIES['LIC/Insurance']['keywords']:
            if keyword in description:
                # Check for specific subcategory matches
                for subcategory in CATEGORIES['LIC/Insurance']['subcategories']:
                    if subcategory.lower() in description:
                        return {'category': 'LIC/Insurance', 'subcategory': subcategory}
                return {'category': 'LIC/Insurance', 'subcategory': 'LIC Premium'}
    
    # Check for investment transactions (including enhanced keywords)
    if 'Investments' in CATEGORIES:
        for keyword in CATEGORIES['Investments']['keywords']:
            if keyword in description:
                # Check for gold-related transactions
                gold_keywords = ['gold', 'mmtc', 'tanishq gold', 'digital gold', 'sovereign gold', 
                               'gold etf', 'gold bonds', 'gold deposit', 'gold saving', 'gold purchase',
                               'grt jewellers', 'tanishq', 'kalyan jewellers', 'joyalukkas']
                if any(gold_kw in description for gold_kw in gold_keywords):
                    return {'category': 'Investments', 'subcategory': 'Gold'}
                
                # Check for specific investment subcategories
                for subcategory in CATEGORIES['Investments']['subcategories']:
                    if subcategory.lower() in description:
                        return {'category': 'Investments', 'subcategory': subcategory}
                return {'category': 'Investments', 'subcategory': 'Other Investments'}
    
    # Check remaining categories
    for category, info in CATEGORIES.items():
        if category not in ['Income', 'Money Transfer', 'LIC/Insurance', 'Investments', 'Other']:
            for keyword in info['keywords']:
                if keyword in description:
                    # Assign most relevant subcategory
                    for subcategory in info['subcategories']:
                        if subcategory.lower() in description:
                            return {'category': category, 'subcategory': subcategory}
                    return {'category': category, 'subcategory': info['subcategories'][0]}
    
    return {'category': 'Other', 'subcategory': 'Unknown'}

def get_all_categories() -> Dict[str, List[str]]:
    """Get all categories and their subcategories."""
    return {cat: info['subcategories'] for cat, info in CATEGORIES.items()}

def get_category_keywords() -> Dict[str, List[str]]:
    """Get all categories and their keywords."""
    return {cat: info['keywords'] for cat, info in CATEGORIES.items()}