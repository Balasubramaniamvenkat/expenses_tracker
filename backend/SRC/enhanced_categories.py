"""
Enhanced transaction categorization system with improved keyword mapping
and user feedback mechanisms to minimize "Other" category usage.
"""

import re
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Enhanced category definitions with comprehensive keywords
ENHANCED_CATEGORIES = {
    'Investments': {
        'description': 'Mutual funds, stocks, gold purchases, fixed deposits, pension plans, demat transfers',
        'subcategories': {
            'Mutual Funds & SIP': {
                'keywords': ['mutual fund', 'sip', 'systematic', 'amc', 'fund house', 'nav', 'equity',
                           'debt fund', 'hybrid', 'elss', 'tax saver', 'hdfc amc', 'icici pru', 'sbi mf',
                           'axis mf', 'kotak mf', 'nippon', 'franklin', 'mirae', 'parag parikh'],
                'patterns': [r'.*mutual.*fund.*', r'.*sip.*', r'.*amc.*']
            },
            'Stocks & Trading': {
                'keywords': ['zerodha', 'upstox', 'angel', 'sharekhan', 'iifl', 'kotak securities',
                           'hdfc securities', 'icici direct', 'axis direct', 'trading', 'demat',
                           'brokerage', 'equity', 'stock', 'share', 'nse', 'bse', 'sensex', 'nifty'],
                'patterns': [r'.*zerodha.*', r'.*trading.*', r'.*demat.*', r'.*brokerage.*']
            },            'Gold & Jewelry': {
                'keywords': ['gold', 'silver', 'jewelry', 'jewellery', 'ornament', 'tanishq', 'kalyan',
                           'joyalukkas', 'grt', 'mmtc', 'digital gold', 'gold etf', 'sovereign gold',
                           'gold bonds', 'gold savings', 'precious metals', 'bullion'],
                'patterns': [r'.*gold.*', r'.*jewelry.*', r'.*jewellery.*', r'.*tanishq.*']
            },
            'Fixed Deposits & Savings': {
                'keywords': ['fixed deposit', 'fd', 'recurring deposit', 'savings account',
                           'deposit', 'maturity', 'investment account', 'term deposit', 'time deposit'],
                'patterns': [r'.*fixed.*deposit.*', r'.*\bfd\b.*', r'.*recurring.*deposit.*', r'.*deposit.*']
            },
            'Pension & Insurance': {
                'keywords': ['ppf', 'epf', 'pf', 'provident fund', 'pension', 'nps', 'retirement',
                           'life insurance', 'term insurance', 'endowment', 'ulip', 'annuity'],
                'patterns': [r'.*pension.*', r'.*provident.*fund.*', r'.*insurance.*']
            }
        }
    },
    'Education': {
        'description': 'School fees, college tuition, exam fees, course payments, educational materials',
        'subcategories': {
            'School & College Fees': {
                'keywords': ['school', 'college', 'university', 'fees', 'tuition', 'admission', 'semester',
                           'academic', 'education', 'student', 'course fee', 'registration', 'enrollment'],
                'patterns': [r'.*school.*fee.*', r'.*college.*fee.*', r'.*tuition.*', r'.*education.*']
            },
            'Exam & Course Fees': {
                'keywords': ['exam', 'test', 'certification', 'course', 'training', 'workshop', 'seminar',
                           'online course', 'udemy', 'coursera', 'byju', 'unacademy', 'vedantu'],
                'patterns': [r'.*exam.*fee.*', r'.*course.*fee.*', r'.*training.*']
            },
            'Books & Materials': {
                'keywords': ['book', 'notebook', 'stationery', 'pen', 'pencil', 'study material',
                           'textbook', 'reference', 'library', 'educational material'],
                'patterns': [r'.*book.*', r'.*stationery.*', r'.*study.*material.*']
            }
        }
    },
    'Transfers & Payments': {
        'description': 'Bank transfers, wallet top-ups, loan repayments, credit card payments, rent, family transfers',
        'subcategories': {
            'Bank Transfers': {
                'keywords': ['neft', 'imps', 'rtgs', 'upi', 'bank transfer', 'fund transfer', 'online transfer',
                           'net banking', 'mobile banking', 'paytm', 'phonepe', 'googlepay', 'amazon pay'],
                'patterns': [r'.*neft.*', r'.*imps.*', r'.*upi.*', r'.*transfer.*']
            },
            'Credit Card & Loan Payments': {
                'keywords': ['credit card', 'loan', 'emi', 'repayment', 'outstanding', 'due amount',
                           'minimum payment', 'principal', 'interest', 'home loan', 'personal loan',
                           'car loan', 'education loan', 'credit limit'],
                'patterns': [r'.*credit.*card.*', r'.*loan.*', r'.*emi.*']
            },
            'Wallet & Digital Payments': {
                'keywords': ['wallet', 'paytm', 'phonepe', 'googlepay', 'amazon pay', 'mobikwik',
                           'freecharge', 'airtel money', 'jio money', 'digital wallet', 'e-wallet'],
                'patterns': [r'.*wallet.*', r'.*paytm.*', r'.*phonepe.*', r'.*googlepay.*']
            },
            'Rent & Housing': {
                'keywords': ['rent', 'house rent', 'flat rent', 'room rent', 'accommodation', 'landlord',
                           'tenant', 'security deposit', 'advance', 'maintenance', 'society fee'],
                'patterns': [r'.*rent.*', r'.*accommodation.*', r'.*landlord.*']
            },
            'Family & Personal': {
                'keywords': ['family', 'parents', 'spouse', 'children', 'allowance', 'pocket money',
                           'gift', 'celebration', 'birthday', 'anniversary', 'festival', 'donation'],
                'patterns': [r'.*family.*', r'.*gift.*', r'.*donation.*']
            }
        }
    },
    'Savings': {
        'description': 'Transfers to savings accounts, recurring deposits, emergency funds',
        'subcategories': {
            'Savings Account': {
                'keywords': ['savings account', 'savings transfer', 'emergency fund', 'contingency',
                           'rainy day fund', 'safety net', 'reserve fund'],
                'patterns': [r'.*savings.*account.*', r'.*emergency.*fund.*']
            },            'Recurring Deposits': {
                'keywords': ['recurring deposit', 'monthly deposit', 'systematic deposit'],
                'patterns': [r'.*recurring.*deposit.*', r'.*\brd\b.*']
            }
        }
    },
    'Expenses': {
        'description': 'Daily living expenses including groceries, dining, travel, shopping, utilities, healthcare, entertainment',
        'subcategories': {
            'Groceries': {
                'keywords': ['grocery', 'supermarket', 'mart', 'store', 'shop', 'mall', 'bazar', 'market', 
                           'reliance fresh', 'big basket', 'grofers', 'spencer', 'more', 'dmart', 'food bazaar',
                           'vegetables', 'fruits', 'provisions', 'kirana', 'general store', 'departmental store'],
                'patterns': [r'.*grocery.*', r'.*supermarket.*', r'.*provision.*']
            },
            'Dining & Restaurants': {
                'keywords': ['restaurant', 'hotel', 'cafe', 'coffee', 'tea', 'food', 'meal', 'eating', 'dining',
                           'swiggy', 'zomato', 'uber eats', 'dominos', 'pizza', 'burger', 'kfc', 'mcdonalds',
                           'starbucks', 'ccd', 'food court', 'canteen', 'mess', 'dhaba', 'biryani', 'chinese'],
                'patterns': [r'.*restaurant.*', r'.*hotel.*', r'.*food.*delivery.*']
            },
            'Travel & Transportation': {
                'keywords': ['uber', 'ola', 'taxi', 'cab', 'auto', 'bus', 'train', 'metro', 'flight', 'airline',
                           'fuel', 'petrol', 'diesel', 'gas', 'parking', 'toll', 'transport', 'travel',
                           'irctc', 'railways', 'makemytrip', 'goibibo', 'cleartrip', 'redbus', 'bmtc', 'tsrtc'],
                'patterns': [r'.*travel.*', r'.*transport.*', r'.*fuel.*']
            },
            'Shopping': {
                'keywords': ['amazon', 'flipkart', 'myntra', 'ajio', 'shopping', 'purchase', 'buy', 'order',
                           'clothing', 'dress', 'shirt', 'trouser', 'shoes', 'electronics', 'mobile', 'laptop',
                           'book', 'gift', 'toy', 'home', 'kitchen', 'furniture', 'appliance', 'gadget'],
                'patterns': [r'.*shopping.*', r'.*purchase.*', r'.*order.*']
            },            'Utilities': {
                'keywords': ['electricity', 'electric', 'power', 'water', 'gas', 'internet', 'broadband', 'wifi',
                           'mobile bill', 'phone bill', 'recharge', 'utility', 'maintenance', 'society',
                           'bescom', 'bwssb', 'airtel bill', 'airtel mobile bill', 'jio bill', 'vi bill', 
                           'bsnl bill', 'act bill', 'hathway bill', 'hathway landline bill', 'tata sky bill',
                           'landline bill', 'mobile recharge', 'airtel recharge', 'jio recharge'],
                'patterns': [r'.*bill.*', r'.*recharge.*', r'.*utility.*', r'.*landline.*bill.*', r'.*mobile.*bill.*']
            },
            'Healthcare': {
                'keywords': ['hospital', 'doctor', 'medical', 'medicine', 'pharmacy', 'health', 'dental',
                           'clinic', 'apollo', 'fortis', 'manipal', 'narayana', 'medplus', 'netmeds',
                           'checkup', 'treatment', 'surgery', 'diagnostic', 'lab', 'test', 'consultation'],
                'patterns': [r'.*medical.*', r'.*health.*', r'.*pharmacy.*']
            },
            'Entertainment': {
                'keywords': ['movie', 'cinema', 'netflix', 'amazon prime', 'hotstar', 'spotify', 'youtube',
                           'game', 'gaming', 'entertainment', 'pvr', 'inox', 'multiplex', 'theatre',
                           'subscription', 'streaming', 'music', 'video', 'concert', 'event', 'show'],
                'patterns': [r'.*entertainment.*', r'.*subscription.*', r'.*streaming.*']
            },
            'Personal Care': {
                'keywords': ['salon', 'parlour', 'spa', 'beauty', 'cosmetic', 'grooming', 'haircut',
                           'facial', 'massage', 'gym', 'fitness', 'yoga', 'sports', 'club'],
                'patterns': [r'.*salon.*', r'.*beauty.*', r'.*fitness.*']
            }
        }
    }
}

# File to store user-defined category mappings
USER_MAPPINGS_FILE = 'user_category_mappings.json'

class EnhancedCategorizer:
    """Enhanced transaction categorizer with learning capabilities."""
    
    def __init__(self):
        self.user_mappings = self._load_user_mappings()
        self.pending_classifications = []
    
    def _load_user_mappings(self) -> Dict[str, Any]:
        """Load user-defined category mappings from file."""
        try:
            if os.path.exists(USER_MAPPINGS_FILE):
                with open(USER_MAPPINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load user mappings: {e}")
        return {'keywords': {}, 'patterns': {}, 'exact_matches': {}}
    
    def _save_user_mappings(self):
        """Save user-defined mappings to file."""
        try:
            with open(USER_MAPPINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.user_mappings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save user mappings: {e}")
    
    def categorize_transaction(self, description: str, amount: float) -> Dict[str, str]:
        """
        Enhanced transaction categorization with learning capabilities.
        
        Args:
            description (str): Transaction description
            amount (float): Transaction amount
            
        Returns:
            Dict with category, subcategory, and confidence level
        """
        description_lower = description.lower().strip()
        
        # First check user-defined exact matches
        if description_lower in self.user_mappings.get('exact_matches', {}):
            mapping = self.user_mappings['exact_matches'][description_lower]
            return {
                'category': mapping['category'],
                'subcategory': mapping['subcategory'],
                'confidence': 'high'
            }
        
        # Check user-defined keywords
        for keyword, mapping in self.user_mappings.get('keywords', {}).items():
            if keyword in description_lower:
                return {
                    'category': mapping['category'],
                    'subcategory': mapping['subcategory'],
                    'confidence': 'high'
                }
        
        # Handle income transactions
        if amount > 0:
            return self._categorize_income(description_lower)
        
        # Enhanced expense categorization with better matching
        result = self._categorize_expense(description_lower, amount)
        
        # If categorized as "Other", add to pending classifications
        if result['category'] == 'Other':
            self.pending_classifications.append({
                'description': description,
                'amount': amount,
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    
    def _categorize_income(self, description: str) -> Dict[str, str]:
        """Categorize income transactions."""
        investment_keywords = ['dividend', 'interest', 'fd maturity', 'rd maturity', 
                             'mutual fund redemption', 'stock dividend', 'gold redemption']
        
        if any(keyword in description for keyword in investment_keywords):
            return {'category': 'Income', 'subcategory': 'Investment Income', 'confidence': 'high'}
        
        salary_keywords = ['salary', 'pay', 'wages', 'bonus', 'incentive', 'commission']
        if any(keyword in description for keyword in salary_keywords):        return {'category': 'Income', 'subcategory': 'Salary', 'confidence': 'high'}
        
        return {'category': 'Income', 'subcategory': 'Other Income', 'confidence': 'medium'}
    
    def _categorize_expense(self, description: str, amount: float) -> Dict[str, str]:
        """Enhanced expense categorization with multiple matching strategies."""
        
        # Strategy 1: Check for specific service patterns first (to avoid generic UPI matches)
        specific_patterns = {
            'netflix': ('Expenses', 'Entertainment'),
            'netflix com': ('Expenses', 'Entertainment'),
            'amazon prime': ('Expenses', 'Entertainment'),
            'hotstar': ('Expenses', 'Entertainment'),
            'spotify': ('Expenses', 'Entertainment'),
            'airtel mobile bill': ('Expenses', 'Utilities'),
            'airtel bill': ('Expenses', 'Utilities'),
            'jio bill': ('Expenses', 'Utilities'),
            'hathway bill': ('Expenses', 'Utilities'),
            'hathway landline bill': ('Expenses', 'Utilities'),
            'landline bill': ('Expenses', 'Utilities'),
            'mobile bill': ('Expenses', 'Utilities'),
            'paytm recharge': ('Expenses', 'Utilities'),
            'amazon pay': ('Expenses', 'Shopping'),
            'swiggy': ('Expenses', 'Dining & Restaurants'),
            'zomato': ('Expenses', 'Dining & Restaurants'),
            'uber eats': ('Expenses', 'Dining & Restaurants'),
        }
        
        for pattern, (category, subcategory) in specific_patterns.items():
            if pattern in description:
                return {
                    'category': category,
                    'subcategory': subcategory,
                    'confidence': 'high'
                }
        
        # Strategy 2: Exact keyword matching with priority order
        for category_name, category_info in ENHANCED_CATEGORIES.items():
            for subcategory_name, subcategory_info in category_info['subcategories'].items():
                
                # Check exact keywords first
                for keyword in subcategory_info.get('keywords', []):
                    if keyword in description:
                        return {
                            'category': category_name,
                            'subcategory': subcategory_name,
                            'confidence': 'high'
                        }
                
                # Check regex patterns
                for pattern in subcategory_info.get('patterns', []):
                    if re.search(pattern, description, re.IGNORECASE):
                        return {
                            'category': category_name,
                            'subcategory': subcategory_name,
                            'confidence': 'medium'
                        }
        
        # Strategy 3: Fuzzy matching for common misspellings and variations
        fuzzy_result = self._fuzzy_match(description)
        if fuzzy_result:
            return fuzzy_result
        
        # Strategy 4: Amount-based heuristics for specific categories
        amount_result = self._amount_based_categorization(description, abs(amount))
        if amount_result:
            return amount_result
        
        # If nothing matches, return Other with low confidence
        return {'category': 'Other', 'subcategory': 'Uncategorized', 'confidence': 'low'}
    
    def _fuzzy_match(self, description: str) -> Optional[Dict[str, str]]:
        """Apply fuzzy matching for common variations and misspellings."""
        
        # Common variations and abbreviations
        variations = {
            'atm': ('Transfers & Payments', 'Bank Transfers'),
            'pos': ('Expenses', 'Shopping'),
            'ecs': ('Transfers & Payments', 'Credit Card & Loan Payments'),
            'nach': ('Transfers & Payments', 'Credit Card & Loan Payments'),
            'autopay': ('Transfers & Payments', 'Credit Card & Loan Payments'),
            'recharge': ('Expenses', 'Utilities'),
            'top up': ('Transfers & Payments', 'Wallet & Digital Payments'),
            'topup': ('Transfers & Payments', 'Wallet & Digital Payments'),
        }
        
        for variation, (category, subcategory) in variations.items():
            if variation in description:
                return {
                    'category': category,
                    'subcategory': subcategory,
                    'confidence': 'medium'
                }
        
        return None
    
    def _amount_based_categorization(self, description: str, amount: float) -> Optional[Dict[str, str]]:
        """Use amount-based heuristics for categorization."""
        
        # Large amounts might be investments or major purchases
        if amount > 50000:
            investment_indicators = ['purchase', 'buy', 'investment', 'deposit']
            if any(indicator in description for indicator in investment_indicators):
                return {
                    'category': 'Investments',
                    'subcategory': 'Fixed Deposits & Savings',
                    'confidence': 'low'
                }
        
        # Small regular amounts might be utilities or subscriptions
        if 100 < amount < 5000:
            if any(word in description for word in ['monthly', 'subscription', 'bill', 'charges']):
                return {
                    'category': 'Expenses',
                    'subcategory': 'Utilities',
                    'confidence': 'low'
                }
        
        return None
    
    def learn_from_user_input(self, description: str, amount: float, 
                            category: str, subcategory: str, 
                            mapping_type: str = 'keyword') -> bool:
        """
        Learn from user categorization input.
        
        Args:
            description (str): Transaction description
            amount (float): Transaction amount
            category (str): User-selected category
            subcategory (str): User-selected subcategory
            mapping_type (str): Type of mapping ('keyword', 'exact', 'pattern')
            
        Returns:
            bool: True if learning was successful
        """
        try:
            description_lower = description.lower().strip()
            
            if mapping_type == 'exact':
                # Store exact match
                if 'exact_matches' not in self.user_mappings:
                    self.user_mappings['exact_matches'] = {}
                
                self.user_mappings['exact_matches'][description_lower] = {
                    'category': category,
                    'subcategory': subcategory,
                    'learned_date': datetime.now().isoformat()
                }
            
            elif mapping_type == 'keyword':
                # Extract key terms for keyword matching
                key_terms = self._extract_key_terms(description_lower)
                
                if 'keywords' not in self.user_mappings:
                    self.user_mappings['keywords'] = {}
                
                for term in key_terms:
                    if len(term) > 3:  # Only store meaningful terms
                        self.user_mappings['keywords'][term] = {
                            'category': category,
                            'subcategory': subcategory,
                            'learned_date': datetime.now().isoformat()
                        }
            
            # Save the updated mappings
            self._save_user_mappings()
            
            # Remove from pending classifications if it was there
            self.pending_classifications = [
                p for p in self.pending_classifications 
                if p['description'].lower() != description_lower
            ]
            
            return True
            
        except Exception as e:
            print(f"Error learning from user input: {e}")
            return False
    
    def _extract_key_terms(self, description: str) -> List[str]:
        """Extract key terms from transaction description for learning."""
        
        # Remove common noise words
        noise_words = {'the', 'and', 'or', 'at', 'to', 'for', 'of', 'in', 'on', 'by', 'with'}
        
        # Split and clean terms
        terms = re.findall(r'\b[a-zA-Z]{3,}\b', description)
        key_terms = [term.lower() for term in terms if term.lower() not in noise_words]
        
        return key_terms
    
    def get_pending_classifications(self) -> List[Dict[str, Any]]:
        """Get transactions that need user classification."""
        return self.pending_classifications.copy()
    
    def get_category_distribution(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze category distribution and identify potential issues.
        
        Args:
            transactions: List of categorized transactions
            
        Returns:
            Dict with category statistics and recommendations
        """
        if not transactions:
            return {}
        
        # Count transactions by category
        category_counts = {}
        category_amounts = {}
        other_transactions = []
        
        for txn in transactions:
            category = txn.get('category', 'Other')
            amount = abs(txn.get('amount', 0))
            
            category_counts[category] = category_counts.get(category, 0) + 1
            category_amounts[category] = category_amounts.get(category, 0) + amount
            
            if category == 'Other':
                other_transactions.append(txn)
        
        total_transactions = len(transactions)
        total_amount = sum(category_amounts.values())
        
        # Calculate percentages
        category_stats = {}
        for category in category_counts:
            count_pct = (category_counts[category] / total_transactions) * 100
            amount_pct = (category_amounts[category] / total_amount) * 100 if total_amount > 0 else 0
            
            category_stats[category] = {
                'transaction_count': category_counts[category],
                'transaction_percentage': count_pct,
                'amount_total': category_amounts[category],
                'amount_percentage': amount_pct
            }
        
        # Generate recommendations
        recommendations = []
        other_pct = category_stats.get('Other', {}).get('transaction_percentage', 0)
        
        if other_pct > 5:  # If more than 5% are in "Other"
            recommendations.append(f"High 'Other' category usage ({other_pct:.1f}%). Consider reviewing and categorizing these transactions.")
        
        if other_pct > 15:  # Critical level
            recommendations.append("CRITICAL: Too many transactions in 'Other' category. Immediate attention needed.")
        
        return {
            'category_stats': category_stats,
            'other_transactions': other_transactions[:10],  # Show top 10 for review
            'recommendations': recommendations,
            'total_transactions': total_transactions,
            'total_amount': total_amount
        }

# Global instance
enhanced_categorizer = EnhancedCategorizer()

def categorize_transaction_enhanced(description: str, amount: float) -> Dict[str, str]:
    """Enhanced categorization function to replace the original."""
    return enhanced_categorizer.categorize_transaction(description, amount)

def learn_from_user_categorization(description: str, amount: float, 
                                 category: str, subcategory: str) -> bool:
    """Learn from user categorization input."""
    return enhanced_categorizer.learn_from_user_input(description, amount, category, subcategory)

def get_pending_other_transactions() -> List[Dict]:
    """Get transactions that were categorized as 'Other' and need user review."""
    return enhanced_categorizer.get_pending_classifications()

def get_available_categories() -> Dict[str, List[str]]:
    """Get all available categories and subcategories."""
    categories = {}
    for category_name, category_info in ENHANCED_CATEGORIES.items():
        categories[category_name] = list(category_info['subcategories'].keys())
    return categories

def analyze_categorization_quality(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the quality of categorization and provide recommendations."""
    return enhanced_categorizer.get_category_distribution(transactions)
