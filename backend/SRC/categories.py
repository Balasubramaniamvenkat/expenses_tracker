"""
Transaction categorization rules and helper functions.

This module now uses the RefinedCategorizer from refined_categories.py
for smarter categorization with:
- Investment detection (Zerodha, SIP, Gold, Jewelry)
- Insurance separation (LIC, Health, Vehicle, Term)
- Education categorization (Schools, Training, Courses)
- Healthcare detection (Hospital, Clinic, Pharmacy, Labs)
- Smart UPI handling (differentiates transfers from purchases)
- User-learnable mappings for personalization
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Any, TYPE_CHECKING

# Type checking import to avoid runtime issues
if TYPE_CHECKING:
    from .refined_categories import RefinedCategorizer

# Import refined categorizer
USE_REFINED = False
RefinedCategorizerClass = None

try:
    from .refined_categories import (
        RefinedCategorizer as _RefinedCategorizer, 
        REFINED_CATEGORIES,
        get_category_colors,
        get_category_icons
    )
    RefinedCategorizerClass = _RefinedCategorizer
    USE_REFINED = True
except ImportError:
    try:
        # Try without relative import (when running from different context)
        from refined_categories import (
            RefinedCategorizer as _RefinedCategorizer, 
            REFINED_CATEGORIES,
            get_category_colors,
            get_category_icons
        )
        RefinedCategorizerClass = _RefinedCategorizer
        USE_REFINED = True
    except ImportError:
        USE_REFINED = False

# Legacy category hierarchy (kept for backward compatibility)
CATEGORIES = {
    'Income': {
        'keywords': ['salary', 'deposit', 'interest', 'dividend', 'refund', 'neft cr'],
        'subcategories': ['Salary', 'Interest', 'Dividends', 'Refunds', 'Other Income']
    },
    'Investments': {
        'keywords': [
            # Stock Trading Platforms
            'zerodha', 'upstox', 'groww', 'angel broking', 'angel one',
            'sharekhan', 'iifl', 'kotak securities', 'hdfc securities',
            'icici direct', 'razorpay', 'razpbse', 'demat', 'trading', 'brokerage',
            # Mutual Funds & SIP
            'mutual fund', 'sip', 'systematic investment', 'amc', 'elss',
            'hdfc amc', 'icici pru', 'sbi mf', 'axis mf',
            # Gold & Jewelry (Investment)
            'gold', 'mmtc', 'digital gold', 'sovereign gold', 'gold etf',
            'gold bonds', 'sgb', 'tanishq', 'kalyan', 'joyalukkas', 'grt',
            'jewelry', 'jewellery', 'jewellers', 'malabar gold', 'bullion',
            # Other Investments
            'fixed deposit', 'fd', 'recurring deposit', 'rd',
            'ppf', 'nps', 'provident fund', 'epf'
        ],
        'subcategories': ['Stocks & Trading', 'Mutual Funds & SIP', 'Gold & Jewelry', 
                         'Fixed Deposits', 'Recurring Deposits', 'PPF & NPS']
    },
    'Insurance': {
        'keywords': [
            # Life Insurance
            'lic', 'lic of india', 'lic premium', 'max life', 'hdfc life',
            'icici pru life', 'sbi life', 'bajaj allianz life', 'endowment', 'ulip',
            # Health Insurance
            'health insurance', 'mediclaim', 'medical insurance', 'star health',
            'max bupa', 'care health', 'family floater',
            # Vehicle Insurance
            'car insurance', 'motor insurance', 'vehicle insurance', 'bike insurance',
            'acko', 'digit insurance',
            # Term Insurance
            'term insurance', 'term plan', 'term life',
            # General
            'insurance premium', 'policy premium'
        ],
        'subcategories': ['Life Insurance', 'Health Insurance', 'Vehicle Insurance', 
                         'Term Insurance', 'General Insurance']
    },
    'Education': {
        'keywords': [
            # Schools
            'school', 'school fee', 'tuition', 'vidyalaya', 'academy',
            'cbse', 'icse', 'kindergarten', 'play school',
            # College
            'college', 'university', 'semester fee', 'admission fee',
            'graduation', 'post graduation', 'mba', 'engineering',
            # Training & Courses
            'training', 'course', 'workshop', 'certification',
            'udemy', 'coursera', 'linkedin learning', 'upgrad', 'simplilearn',
            'bootcamp', 'coaching', 'classes',
            # Coaching
            'byjus', 'byju', 'unacademy', 'vedantu', 'aakash', 'allen',
            'physics wallah', 'whitehat',
            # Books
            'book', 'textbook', 'stationery', 'kindle', 'audible'
        ],
        'subcategories': ['School Fees', 'College & University', 'Training & Courses',
                         'Coaching & Tuition', 'Books & Materials']
    },
    'Healthcare': {
        'keywords': [
            # Hospitals
            'hospital', 'apollo', 'fortis', 'max hospital', 'manipal',
            'narayana', 'medanta', 'nursing home', 'surgery', 'operation',
            # Clinics & Doctors
            'clinic', 'doctor', 'physician', 'consultation', 'dr.',
            'specialist', 'opd', 'checkup', 'practo',
            # Pharmacy
            'pharmacy', 'medical', 'medicine', 'medplus', 'apollo pharmacy',
            'netmeds', '1mg', 'pharmeasy', 'chemist', 'prescription',
            # Diagnostic & Labs
            'lab', 'laboratory', 'diagnostic', 'test', 'pathology',
            'thyrocare', 'lal path', 'srl', 'metropolis', 'blood test',
            'x-ray', 'scan', 'mri', 'ct scan', 'ultrasound', 'ecg',
            # Dental
            'dental', 'dentist', 'tooth', 'teeth',
            # Wellness
            'gym', 'fitness', 'yoga', 'cult fit', 'spa', 'physiotherapy'
        ],
        'subcategories': ['Hospital', 'Clinic & Doctor', 'Pharmacy', 
                         'Diagnostic & Labs', 'Dental', 'Wellness & Fitness']
    },
    'Money Transfer': {
        'keywords': ['neft', 'imps', 'rtgs', 'fund transfer', 'bank transfer', 
                    'net banking transfer', 'online transfer'],
        'subcategories': ['NEFT Transfer', 'IMPS Transfer', 'RTGS Transfer', 'Bank Transfer']
    },
    'Food & Dining': {
        'keywords': [
            'swiggy', 'zomato', 'food delivery', 'uber eats',
            'grocery', 'supermarket', 'dmart', 'bigbasket', 'blinkit',
            'restaurant', 'hotel', 'cafe', 'dominos', 'pizza hut',
            'mcdonalds', 'kfc', 'subway', 'starbucks', 'ccd'
        ],
        'subcategories': ['Groceries', 'Food Delivery', 'Restaurants', 'Cafe & Coffee']
    },
    'Shopping': {
        'keywords': [
            'amazon', 'flipkart', 'myntra', 'ajio', 'meesho', 'snapdeal',
            'croma', 'reliance digital', 'vijay sales', 'electronic',
            'lifestyle', 'pantaloons', 'shoppers stop', 'max', 'westside',
            'ikea', 'pepperfry', 'urban ladder', 'furniture'
        ],
        'subcategories': ['Online Shopping', 'Electronics', 'Clothing & Fashion', 'Home & Furniture']
    },
    'Transportation': {
        'keywords': [
            'petrol', 'diesel', 'fuel', 'hp', 'bharat petroleum', 'indian oil',
            'uber', 'ola', 'rapido', 'taxi', 'cab', 'auto',
            'metro', 'irctc', 'railway', 'bus', 'train',
            'parking', 'toll', 'fastag',
            'makemytrip', 'goibibo', 'flight', 'air india', 'indigo'
        ],
        'subcategories': ['Fuel', 'Taxi & Rideshare', 'Public Transport', 
                         'Parking & Toll', 'Travel & Booking']
    },
    'Utilities': {
        'keywords': [
            'electricity', 'bescom', 'tata power', 'power bill',
            'water', 'bwssb', 'water bill',
            'internet', 'broadband', 'wifi', 'act fibernet', 'jio fiber',
            'mobile', 'phone', 'airtel', 'jio', 'vodafone', 'recharge',
            'gas', 'lpg', 'indane', 'hp gas', 'piped gas',
            'dth', 'tata sky', 'dish tv'
        ],
        'subcategories': ['Electricity', 'Water', 'Internet & Broadband', 
                         'Mobile & Phone', 'Gas & LPG', 'DTH & Cable']
    },
    'Entertainment': {
        'keywords': [
            'netflix', 'amazon prime', 'hotstar', 'disney', 'sony liv',
            'spotify', 'youtube premium', 'apple music',
            'pvr', 'inox', 'bookmyshow', 'movie', 'cinema',
            'playstation', 'xbox', 'steam', 'game'
        ],
        'subcategories': ['Streaming Services', 'Movies & Theatre', 'Gaming', 'Events & Activities']
    },
    'Housing': {
        'keywords': [
            'rent', 'house rent', 'flat rent', 'landlord',
            'maintenance', 'society', 'society fee',
            'urban company', 'urbanclap', 'plumber', 'electrician'
        ],
        'subcategories': ['Rent', 'Maintenance', 'Home Services']
    },
    'Other': {
        'keywords': ['atm', 'cash withdrawal', 'bank charge', 'service charge'],
        'subcategories': ['ATM Withdrawal', 'Bank Charges', 'Uncategorized']
    }
}

# Global categorizer instance
_categorizer = None

def get_categorizer() -> Optional[Any]:
    """Get or create the categorizer instance."""
    global _categorizer
    if _categorizer is None and USE_REFINED and RefinedCategorizerClass is not None:
        _categorizer = RefinedCategorizerClass()
    return _categorizer


def categorize_transaction(description: str, amount: float) -> Dict[str, str]:
    """
    Categorize a transaction based on its description and amount.
    
    Uses RefinedCategorizer for smart categorization with:
    - Investment detection (Zerodha, SIP, Gold, Jewelry)
    - Separate Insurance category (LIC, Health, Vehicle)
    - Education (Schools, Training, Courses)
    - Healthcare (Hospital, Clinic, Pharmacy, Labs)
    - Smart UPI/NEFT differentiation (transfers vs purchases)
    
    Args:
        description (str): Transaction description
        amount (float): Transaction amount
    
    Returns:
        Dict with category and subcategory
    """
    # Use refined categorizer if available
    if USE_REFINED:
        categorizer = get_categorizer()
        if categorizer:
            result = categorizer.categorize(description, amount)
            return {
                'category': result['category'],
                'subcategory': result['subcategory']
            }
    
    # Fallback to legacy categorization
    return _legacy_categorize(description, amount)


def _legacy_categorize(description: str, amount: float) -> Dict[str, str]:
    """Legacy categorization logic (fallback)."""
    description_lower = description.lower()
    
    # Handle income transactions
    if amount > 0:
        investment_income_keywords = ['dividend', 'interest', 'gold redemption']
        if any(keyword in description_lower for keyword in investment_income_keywords):
            return {'category': 'Income', 'subcategory': 'Investment Income'}
        return {'category': 'Income', 'subcategory': 'Other Income'}
    
    # Check categories in priority order
    priority_order = ['Insurance', 'Investments', 'Money Transfer', 'Healthcare', 
                      'Education', 'Food & Dining', 'Shopping', 'Transportation',
                      'Utilities', 'Entertainment', 'Housing', 'Other']
    
    for category in priority_order:
        if category in CATEGORIES:
            cat_info = CATEGORIES[category]
            for keyword in cat_info.get('keywords', []):
                if keyword in description_lower:
                    subcategories = cat_info.get('subcategories', ['Other'])
                    # Try to match a specific subcategory
                    for subcat in subcategories:
                        if subcat.lower() in description_lower:
                            return {'category': category, 'subcategory': subcat}
                    return {'category': category, 'subcategory': subcategories[0]}
    
    return {'category': 'Other', 'subcategory': 'Uncategorized'}

def get_all_categories() -> Dict[str, List[str]]:
    """Get all categories and their subcategories."""
    if USE_REFINED:
        categorizer = get_categorizer()
        if categorizer:
            return categorizer.get_all_categories()
    return {cat: info['subcategories'] for cat, info in CATEGORIES.items()}


def get_category_keywords() -> Dict[str, List[str]]:
    """Get all categories and their keywords."""
    return {cat: info['keywords'] for cat, info in CATEGORIES.items()}


def learn_category(description: str, category: str, subcategory: str) -> bool:
    """
    Learn from user corrections for future categorization.
    
    Args:
        description: Transaction description
        category: Correct category
        subcategory: Correct subcategory
    
    Returns:
        True if learning was successful
    """
    if USE_REFINED:
        categorizer = get_categorizer()
        if categorizer:
            return categorizer.learn(description, category, subcategory)
    return False


def get_category_info(category: str) -> Optional[Dict]:
    """Get detailed info about a category."""
    if USE_REFINED:
        categorizer = get_categorizer()
        if categorizer:
            return categorizer.get_category_info(category)
    return CATEGORIES.get(category)


def recategorize_all_transactions(transactions: List[Dict]) -> List[Dict]:
    """
    Re-categorize all transactions using the refined categorizer.
    
    Args:
        transactions: List of transaction dictionaries
    
    Returns:
        Updated list with new categories
    """
    for txn in transactions:
        description = txn.get('description', txn.get('narration', ''))
        amount = float(txn.get('amount', 0))
        
        result = categorize_transaction(description, amount)
        txn['category'] = result['category']
        txn['subcategory'] = result['subcategory']
    
    return transactions