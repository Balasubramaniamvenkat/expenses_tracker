"""
Refined Transaction Categorization System
==========================================

Categories are organized into:
1. INCOME - Salary, refunds, interest received
2. INVESTMENTS - Stocks, MF, SIP, Gold, Jewelry, Zerodha, FD, RD
3. INSURANCE - LIC, Medical Insurance, Car Insurance, Term Insurance
4. EDUCATION - School, College, Training, Courses, Books
5. HEALTHCARE - Hospital, Clinic, Pharmacy, Medical Tests
6. MONEY TRANSFER - NEFT/IMPS/RTGS transfers to accounts (not purchases)
7. FOOD & DINING - Groceries, Restaurants, Food Delivery
8. SHOPPING - Online/Offline shopping, Electronics, Clothing
9. TRANSPORTATION - Fuel, Taxi, Public Transport
10. UTILITIES - Electricity, Water, Internet, Phone, Gas
11. ENTERTAINMENT - Streaming, Movies, Games
12. HOUSING - Rent, Maintenance, Society Fees
13. OTHER - Uncategorized transactions

Key Logic:
- Uses merchant_database.json for known Indian merchants
- Detects personal names automatically (not in merchant database)
- UPI/NEFT/IMPS to personal names = Money Transfer
- Known jewelry shops (GRT, Bhima, Tanishq, etc.) = Investment/Gold & Jewelry
- Generic keywords like 'gold', 'jewel' alone don't trigger jewelry category
"""

import re
import json
import os
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime


# ============================================================================
# LOAD MERCHANT DATABASE
# ============================================================================

def _get_merchant_db_path() -> str:
    """Get path to merchant database JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'merchant_database.json')


def _load_merchant_database() -> Dict[str, Any]:
    """Load merchant database from JSON file."""
    try:
        db_path = _get_merchant_db_path()
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load merchant database: {e}")
    return {}


# Load merchant database at module level
MERCHANT_DATABASE = _load_merchant_database()


def _build_merchant_lookup() -> Dict[str, Tuple[str, str]]:
    """
    Build a fast lookup dictionary from merchant database.
    Returns: {merchant_name: (category, subcategory)}
    """
    lookup = {}
    for category_key, category_data in MERCHANT_DATABASE.items():
        if category_key.startswith('_'):
            continue  # Skip metadata fields
        
        category = category_data.get('category', 'Other')
        subcategory = category_data.get('subcategory', 'Uncategorized')
        merchants = category_data.get('merchants', [])
        
        for merchant in merchants:
            lookup[merchant.lower()] = (category, subcategory)
    
    return lookup


# Build lookup at module level
MERCHANT_LOOKUP = _build_merchant_lookup()


def _get_all_known_merchants() -> Set[str]:
    """Get a set of all known merchant names for quick checking."""
    return set(MERCHANT_LOOKUP.keys())


KNOWN_MERCHANT_NAMES = _get_all_known_merchants()


# ============================================================================
# CATEGORY DEFINITIONS - Priority ordered for matching
# ============================================================================

REFINED_CATEGORIES = {
    # Priority 1: Income (positive amounts)
    'Income': {
        'priority': 1,
        'icon': '💰',
        'color': '#4CAF50',
        'description': 'Salary, interest, dividends, refunds',
        'subcategories': {
            'Salary': {
                'keywords': ['salary', 'payroll', 'wages', 'monthly pay', 'neft cr'],
                'patterns': [r'.*salary.*', r'.*payroll.*']
            },
            'Interest': {
                'keywords': ['interest', 'int.pd', 'int pd', 'interest credit'],
                'patterns': [r'.*interest.*cr.*', r'.*int\.?pd.*']
            },
            'Dividends': {
                'keywords': ['dividend', 'div', 'payout'],
                'patterns': [r'.*dividend.*']
            },
            'Refunds': {
                'keywords': ['refund', 'cashback', 'reversal', 'credit back', 'returned'],
                'patterns': [r'.*refund.*', r'.*reversal.*']
            },
            'Other Income': {
                'keywords': [],
                'patterns': []
            }
        }
    },

    # Priority 2: Investments (detect early to avoid miscategorization)
    'Investments': {
        'priority': 2,
        'icon': '💎',
        'color': '#2196F3',
        'description': 'Stocks, Mutual Funds, SIP, Gold, Jewelry, FD, RD',
        'subcategories': {
            'Stocks & Trading': {
                'keywords': [
                    'zerodha', 'upstox', 'groww', 'angel broking', 'angel one',
                    'sharekhan', 'iifl', 'kotak securities', 'hdfc securities',
                    'icici direct', 'axis direct', 'motilal', 'sharekhan',
                    '5paisa', 'alice blue', 'fyers', 'trading', 'demat',
                    'brokerage', 'nse', 'bse', 'sensex', 'nifty', 'stocks',
                    'razorpay', 'razpbse', 'clearing corp'
                ],
                'patterns': [
                    r'.*zerodha.*', r'.*groww.*', r'.*upstox.*', r'.*trading.*',
                    r'.*demat.*', r'.*brokerage.*', r'.*razorpay.*securities.*'
                ]
            },
            'Mutual Funds & SIP': {
                'keywords': [
                    'mutual fund', 'sip', 'systematic investment', 'amc',
                    'hdfc amc', 'icici pru', 'sbi mf', 'axis mf', 'kotak mf',
                    'nippon', 'franklin', 'mirae', 'parag parikh', 'ppfas',
                    'dsp', 'tata mf', 'uti mf', 'aditya birla', 'elss',
                    'equity fund', 'debt fund', 'liquid fund', 'balanced fund',
                    'fund house', 'nav', 'hybrid fund'
                ],
                'patterns': [
                    r'.*mutual.*fund.*', r'.*\bsip\b.*', r'.*amc.*',
                    r'.*systematic.*invest.*'
                ]
            },
            'Gold & Jewelry': {
                'keywords': [
                    # Only use very specific indicators, NOT generic words like 'gold', 'jewel'
                    # which might match personal names like "Lakshmi" 
                    'mmtc gold', 'digital gold', 'gold etf', 'sovereign gold',
                    'gold bonds', 'sgb', 'bullion', 'precious metal',
                    # Jewelry shop suffixes - these are safe patterns
                    'jewellers', 'jewellery', 'jewelry shop', 'gold shop'
                    # Specific shop names are in merchant_database.json
                ],
                'patterns': [
                    # Only match if explicitly has jewelry/gold business suffix
                    r'.*jewellers.*', r'.*jewellery.*', r'.*gold\s*(shop|store|house|palace).*',
                    r'.*\bgold\b.*\b(etf|bond|sgb|mmtc|sovereign)\b.*'
                ]
            },
            'Fixed Deposits': {
                'keywords': [
                    'fixed deposit', 'fd', 'term deposit', 'fd booking',
                    'fd renewal', 'fd placement'
                ],
                'patterns': [r'.*fixed.*deposit.*', r'.*\bfd\b.*booking.*']
            },
            'Recurring Deposits': {
                'keywords': [
                    'recurring deposit', 'rd', 'rd installment'
                ],
                'patterns': [r'.*recurring.*deposit.*', r'.*\brd\b.*install.*']
            },
            'PPF & NPS': {
                'keywords': [
                    'ppf', 'public provident', 'nps', 'national pension',
                    'epf', 'pf contribution', 'provident fund'
                ],
                'patterns': [r'.*\bppf\b.*', r'.*\bnps\b.*', r'.*provident.*fund.*']
            }
        }
    },

    # Priority 3: Insurance (before general expenses)
    'Insurance': {
        'priority': 3,
        'icon': '🛡️',
        'color': '#00BCD4',
        'description': 'Life, Health, Vehicle, Term Insurance',
        'subcategories': {
            'Life Insurance': {
                'keywords': [
                    'lic', 'life insurance', 'lic of india', 'lic premium',
                    'max life', 'hdfc life', 'icici pru life', 'sbi life',
                    'bajaj allianz life', 'tata aia', 'kotak life',
                    'endowment', 'money back', 'whole life', 'ulip'
                ],
                'patterns': [r'.*\blic\b.*', r'.*life.*insurance.*', r'.*lic.*premium.*']
            },
            'Health Insurance': {
                'keywords': [
                    'health insurance', 'mediclaim', 'medical insurance',
                    'star health', 'max bupa', 'care health', 'niva bupa',
                    'aditya birla health', 'hdfc ergo health', 'icici lombard health',
                    'family floater', 'health policy'
                ],
                'patterns': [r'.*health.*insurance.*', r'.*mediclaim.*']
            },
            'Vehicle Insurance': {
                'keywords': [
                    'car insurance', 'motor insurance', 'vehicle insurance',
                    'bike insurance', 'two wheeler insurance', 'four wheeler',
                    'comprehensive insurance', 'third party', 'own damage',
                    'acko', 'digit insurance', 'hdfc ergo motor', 'icici lombard motor'
                ],
                'patterns': [r'.*car.*insurance.*', r'.*motor.*insurance.*', r'.*vehicle.*insurance.*']
            },
            'Term Insurance': {
                'keywords': [
                    'term insurance', 'term plan', 'term life', 'pure term',
                    'aegon', 'term cover'
                ],
                'patterns': [r'.*term.*insurance.*', r'.*term.*plan.*']
            },
            'General Insurance': {
                'keywords': [
                    'insurance premium', 'policy premium', 'renewal premium',
                    'home insurance', 'travel insurance', 'accident insurance'
                ],
                'patterns': [r'.*insurance.*premium.*', r'.*policy.*premium.*']
            }
        }
    },

    # Priority 4: Education
    'Education': {
        'priority': 4,
        'icon': '📚',
        'color': '#9C27B0',
        'description': 'School, College, Training, Courses, Books',
        'subcategories': {
            'School Fees': {
                'keywords': [
                    'school', 'school fee', 'school fees', 'tuition',
                    'vidyalaya', 'academy', 'cbse', 'icse', 'state board',
                    'primary school', 'high school', 'pre-school', 'nursery',
                    'kindergarten', 'play school'
                ],
                'patterns': [r'.*school.*fee.*', r'.*school.*', r'.*tuition.*']
            },
            'College & University': {
                'keywords': [
                    'college', 'university', 'semester fee', 'admission fee',
                    'examination fee', 'convocation', 'degree', 'graduation',
                    'post graduation', 'mba', 'engineering', 'medical college',
                    'institute', 'iit', 'iim', 'nit', 'bits'
                ],
                'patterns': [r'.*college.*fee.*', r'.*university.*', r'.*semester.*']
            },
            'Training & Courses': {
                'keywords': [
                    'training', 'course', 'workshop', 'seminar', 'certification',
                    'udemy', 'coursera', 'linkedin learning', 'skillshare',
                    'upgrad', 'simplilearn', 'great learning', 'coding',
                    'bootcamp', 'coaching', 'classes', 'tutorial', 'lesson'
                ],
                'patterns': [r'.*training.*', r'.*course.*fee.*', r'.*workshop.*']
            },
            'Coaching & Tuition': {
                'keywords': [
                    'coaching', 'tuition', 'byjus', 'byju', 'unacademy',
                    'vedantu', 'aakash', 'allen', 'fiitjee', 'resonance',
                    'physics wallah', 'whitehat', 'toppr', 'extra class'
                ],
                'patterns': [r'.*coaching.*', r'.*byjus.*', r'.*unacademy.*']
            },
            'Books & Materials': {
                'keywords': [
                    'book', 'books', 'textbook', 'stationery', 'notebook',
                    'study material', 'kindle', 'amazon kindle', 'audible'
                ],
                'patterns': [r'.*book.*', r'.*stationery.*']
            }
        }
    },

    # Priority 5: Healthcare
    'Healthcare': {
        'priority': 5,
        'icon': '🏥',
        'color': '#9966FF',
        'description': 'Hospital, Clinic, Pharmacy, Medical Tests',
        'subcategories': {
            'Hospital': {
                'keywords': [
                    'hospital', 'apollo', 'fortis', 'max hospital', 'manipal',
                    'narayana', 'columbia asia', 'medanta', 'aiims',
                    'medical center', 'healthcare', 'nursing home', 'icu',
                    'surgery', 'operation', 'treatment', 'admission'
                ],
                'patterns': [r'.*hospital.*', r'.*apollo.*', r'.*fortis.*']
            },
            'Clinic & Doctor': {
                'keywords': [
                    'clinic', 'doctor', 'physician', 'consultation', 'dr.',
                    'specialist', 'opd', 'checkup', 'check-up', 'diagnosis',
                    'practo', 'docsapp', 'lybrate', 'portea'
                ],
                'patterns': [r'.*clinic.*', r'.*doctor.*', r'.*\bdr\..*']
            },
            'Pharmacy': {
                'keywords': [
                    'pharmacy', 'medical', 'medicine', 'medplus', 'apollo pharmacy',
                    'netmeds', '1mg', 'pharmeasy', 'medlife', 'chemist',
                    'drug store', 'prescription', 'tablet', 'capsule'
                ],
                'patterns': [r'.*pharmacy.*', r'.*medplus.*', r'.*netmeds.*', r'.*1mg.*']
            },
            'Diagnostic & Labs': {
                'keywords': [
                    'lab', 'laboratory', 'diagnostic', 'test', 'pathology',
                    'thyrocare', 'lal path', 'srl', 'metropolis', 'blood test',
                    'x-ray', 'scan', 'mri', 'ct scan', 'ultrasound', 'ecg',
                    'health checkup', 'full body', 'preventive'
                ],
                'patterns': [r'.*lab.*', r'.*diagnostic.*', r'.*thyrocare.*', r'.*pathology.*']
            },
            'Dental': {
                'keywords': [
                    'dental', 'dentist', 'tooth', 'teeth', 'orthodontist',
                    'dental clinic', 'clove dental', 'mydentist', 'sabka dentist'
                ],
                'patterns': [r'.*dental.*', r'.*dentist.*']
            },
            'Wellness & Fitness': {
                'keywords': [
                    'gym', 'fitness', 'yoga', 'cult', 'cult fit', 'gold gym',
                    'anytime fitness', 'spa', 'massage', 'physiotherapy',
                    'ayurveda', 'wellness'
                ],
                'patterns': [r'.*gym.*', r'.*fitness.*', r'.*cult.*fit.*']
            }
        }
    },

    # Priority 6: Money Transfer (NEFT/IMPS to persons, not purchases)
    'Money Transfer': {
        'priority': 6,
        'icon': '💸',
        'color': '#607D8B',
        'description': 'NEFT/IMPS/RTGS transfers to other accounts',
        'subcategories': {
            'NEFT Transfer': {
                'keywords': ['neft'],
                'patterns': [r'.*neft.*'],
                'is_transfer': True
            },
            'IMPS Transfer': {
                'keywords': ['imps'],
                'patterns': [r'.*imps.*'],
                'is_transfer': True
            },
            'RTGS Transfer': {
                'keywords': ['rtgs'],
                'patterns': [r'.*rtgs.*'],
                'is_transfer': True
            },
            'Bank Transfer': {
                'keywords': ['fund transfer', 'bank transfer', 'online transfer', 'net banking transfer'],
                'patterns': [r'.*fund.*transfer.*', r'.*bank.*transfer.*'],
                'is_transfer': True
            }
        }
    },

    # Priority 7: Food & Dining
    'Food & Dining': {
        'priority': 7,
        'icon': '🍔',
        'color': '#FF6384',
        'description': 'Groceries, Restaurants, Food Delivery',
        'subcategories': {
            'Groceries': {
                'keywords': [
                    'grocery', 'supermarket', 'dmart', 'big basket', 'bigbasket',
                    'blinkit', 'grofers', 'jiomart', 'amazon fresh', 'nature basket',
                    'more supermarket', 'reliance fresh', 'spencer', 'star bazaar',
                    'vegetables', 'fruits', 'provisions', 'kirana', 'general store',
                    'departmental', 'hypermarket', 'spar'
                ],
                'patterns': [r'.*grocery.*', r'.*supermarket.*', r'.*dmart.*', r'.*bigbasket.*']
            },
            'Food Delivery': {
                'keywords': [
                    'swiggy', 'zomato', 'uber eats', 'food panda', 'dunzo',
                    'faasos', 'box8', 'behrouz', 'eatfit', 'freshmenu'
                ],
                'patterns': [r'.*swiggy.*', r'.*zomato.*']
            },
            'Restaurants': {
                'keywords': [
                    'restaurant', 'hotel', 'cafe', 'dhaba', 'food court',
                    'biryani', 'chinese', 'pizza', 'burger', 'dominos',
                    'pizza hut', 'mcdonalds', 'kfc', 'subway', 'taco bell',
                    'barbeque nation', 'mainland china', 'paradise', 'dining'
                ],
                'patterns': [r'.*restaurant.*', r'.*dominos.*', r'.*pizza.*hut.*']
            },
            'Cafe & Coffee': {
                'keywords': [
                    'starbucks', 'ccd', 'cafe coffee day', 'barista', 'costa',
                    'third wave', 'blue tokai', 'coffee', 'tea', 'chai'
                ],
                'patterns': [r'.*starbucks.*', r'.*cafe.*coffee.*day.*', r'.*coffee.*']
            }
        }
    },

    # Priority 8: Shopping
    'Shopping': {
        'priority': 8,
        'icon': '🛒',
        'color': '#36A2EB',
        'description': 'Online & Offline Shopping',
        'subcategories': {
            'Online Shopping': {
                'keywords': [
                    'amazon', 'flipkart', 'myntra', 'ajio', 'meesho', 'snapdeal',
                    'tatacliq', 'nykaa', 'purplle', 'mamaearth', 'wow', 'firstcry',
                    'shopclues', 'paytm mall', 'pepperfry', 'urban ladder'
                ],
                'patterns': [r'.*amazon(?!.*prime).*', r'.*flipkart.*', r'.*myntra.*']
            },
            'Electronics': {
                'keywords': [
                    'croma', 'reliance digital', 'vijay sales', 'mobile', 'laptop',
                    'computer', 'electronic', 'gadget', 'samsung', 'apple store',
                    'mi store', 'oneplus', 'headphone', 'earphone', 'camera'
                ],
                'patterns': [r'.*croma.*', r'.*reliance.*digital.*', r'.*electronic.*']
            },
            'Clothing & Fashion': {
                'keywords': [
                    'max', 'lifestyle', 'pantaloons', 'westside', 'shoppers stop',
                    'zara', 'h&m', 'levis', 'wrangler', 'peter england',
                    'van heusen', 'allen solly', 'clothing', 'garment', 'apparel'
                ],
                'patterns': [r'.*lifestyle.*', r'.*pantaloons.*', r'.*shoppers.*stop.*']
            },
            'Home & Furniture': {
                'keywords': [
                    'ikea', 'home centre', 'hometown', 'pepperfry', 'urban ladder',
                    'godrej interio', 'nilkamal', 'furniture', 'home decor',
                    'mattress', 'bedsheet', 'curtain'
                ],
                'patterns': [r'.*ikea.*', r'.*pepperfry.*', r'.*urban.*ladder.*']
            }
        }
    },

    # Priority 9: Transportation
    'Transportation': {
        'priority': 9,
        'icon': '🚗',
        'color': '#FFCE56',
        'description': 'Fuel, Taxi, Public Transport',
        'subcategories': {
            'Fuel': {
                'keywords': [
                    'petrol', 'diesel', 'fuel', 'hp', 'bharat petroleum', 'bpcl',
                    'indian oil', 'iocl', 'shell', 'reliance petrol', 'petrol pump',
                    'gas station', 'filling station', 'cng'
                ],
                'patterns': [r'.*petrol.*', r'.*diesel.*', r'.*fuel.*', r'.*\bhp\b.*petrol.*']
            },
            'Taxi & Rideshare': {
                'keywords': [
                    'uber', 'ola', 'rapido', 'taxi', 'cab', 'auto', 'rickshaw',
                    'meru', 'fasttrack', 'airport taxi'
                ],
                'patterns': [r'.*uber.*', r'.*\bola\b.*', r'.*rapido.*', r'.*taxi.*']
            },
            'Public Transport': {
                'keywords': [
                    'metro', 'bus', 'train', 'irctc', 'railway', 'bmtc', 'best',
                    'dtc', 'ticket', 'pass', 'travel card'
                ],
                'patterns': [r'.*metro.*', r'.*irctc.*', r'.*railway.*']
            },
            'Parking & Toll': {
                'keywords': [
                    'parking', 'toll', 'fastag', 'nhai', 'expressway', 'highway'
                ],
                'patterns': [r'.*parking.*', r'.*toll.*', r'.*fastag.*']
            },
            'Travel & Booking': {
                'keywords': [
                    'makemytrip', 'goibibo', 'cleartrip', 'yatra', 'redbus',
                    'abhibus', 'ixigo', 'flight', 'air india', 'indigo',
                    'spicejet', 'vistara', 'airasia'
                ],
                'patterns': [r'.*makemytrip.*', r'.*goibibo.*', r'.*flight.*']
            }
        }
    },

    # Priority 10: Utilities
    'Utilities': {
        'priority': 10,
        'icon': '💡',
        'color': '#4BC0C0',
        'description': 'Electricity, Water, Internet, Phone, Gas',
        'subcategories': {
            'Electricity': {
                'keywords': [
                    'electricity', 'electric', 'bescom', 'bses', 'tata power',
                    'adani electricity', 'reliance energy', 'power bill',
                    'eb bill', 'mseb', 'tneb', 'wbsedcl'
                ],
                'patterns': [r'.*electricity.*', r'.*bescom.*', r'.*power.*bill.*']
            },
            'Water': {
                'keywords': [
                    'water', 'bwssb', 'water bill', 'water supply', 'municipal water'
                ],
                'patterns': [r'.*water.*bill.*', r'.*bwssb.*']
            },
            'Internet & Broadband': {
                'keywords': [
                    'internet', 'broadband', 'wifi', 'act fibernet', 'jio fiber',
                    'airtel xstream', 'hathway', 'tikona', 'you broadband',
                    'excitel', 'tata sky broadband', 'spectra'
                ],
                'patterns': [r'.*internet.*', r'.*broadband.*', r'.*wifi.*']
            },
            'Mobile & Phone': {
                'keywords': [
                    'mobile', 'phone', 'airtel', 'jio', 'vodafone', 'vi', 'bsnl',
                    'recharge', 'prepaid', 'postpaid', 'mobile bill', 'phone bill'
                ],
                'patterns': [r'.*mobile.*bill.*', r'.*phone.*bill.*', r'.*recharge.*']
            },
            'Gas & LPG': {
                'keywords': [
                    'gas', 'lpg', 'indane', 'bharat gas', 'hp gas', 'piped gas',
                    'png', 'igl', 'mahanagar gas', 'cooking gas', 'cylinder'
                ],
                'patterns': [r'.*\blpg\b.*', r'.*gas.*cylinder.*', r'.*indane.*']
            },
            'DTH & Cable': {
                'keywords': [
                    'dth', 'tata sky', 'dish tv', 'airtel dth', 'videocon d2h',
                    'sun direct', 'cable', 'tv recharge'
                ],
                'patterns': [r'.*tata.*sky.*', r'.*dish.*tv.*', r'.*\bdth\b.*']
            }
        }
    },

    # Priority 11: Entertainment
    'Entertainment': {
        'priority': 11,
        'icon': '🎬',
        'color': '#FF9F40',
        'description': 'Streaming, Movies, Games, Events',
        'subcategories': {
            'Streaming Services': {
                'keywords': [
                    'netflix', 'amazon prime', 'hotstar', 'disney', 'sony liv',
                    'zee5', 'voot', 'jio cinema', 'mubi', 'apple tv', 'youtube premium',
                    'spotify', 'gaana', 'wynk', 'amazon music', 'apple music'
                ],
                'patterns': [r'.*netflix.*', r'.*hotstar.*', r'.*prime.*video.*', r'.*spotify.*']
            },
            'Movies & Theatre': {
                'keywords': [
                    'pvr', 'inox', 'cinepolis', 'carnival', 'bookmyshow', 'paytm movies',
                    'movie', 'cinema', 'multiplex', 'theatre', 'film'
                ],
                'patterns': [r'.*pvr.*', r'.*inox.*', r'.*bookmyshow.*', r'.*movie.*']
            },
            'Gaming': {
                'keywords': [
                    'playstation', 'xbox', 'steam', 'epic games', 'game',
                    'gaming', 'pubg', 'valorant', 'google play games'
                ],
                'patterns': [r'.*playstation.*', r'.*xbox.*', r'.*steam.*']
            },
            'Events & Activities': {
                'keywords': [
                    'event', 'concert', 'show', 'exhibition', 'museum',
                    'amusement park', 'theme park', 'wonderla', 'imagica'
                ],
                'patterns': [r'.*concert.*', r'.*event.*ticket.*']
            }
        }
    },

    # Priority 12: Housing
    'Housing': {
        'priority': 12,
        'icon': '🏠',
        'color': '#8BC34A',
        'description': 'Rent, Maintenance, Society Fees',
        'subcategories': {
            'Rent': {
                'keywords': [
                    'rent', 'house rent', 'flat rent', 'room rent', 'pg rent',
                    'rental', 'monthly rent', 'landlord'
                ],
                'patterns': [r'.*rent.*', r'.*landlord.*']
            },
            'Maintenance': {
                'keywords': [
                    'maintenance', 'society', 'apartment', 'flat maintenance',
                    'building maintenance', 'society fee', 'maintenance charge'
                ],
                'patterns': [r'.*maintenance.*', r'.*society.*fee.*']
            },
            'Home Services': {
                'keywords': [
                    'urban company', 'urbanclap', 'housejoy', 'plumber',
                    'electrician', 'carpenter', 'pest control', 'cleaning',
                    'deep cleaning', 'ac service', 'appliance repair'
                ],
                'patterns': [r'.*urban.*company.*', r'.*home.*service.*']
            }
        }
    },

    # Priority 13: Other (catch-all)
    'Other': {
        'priority': 99,
        'icon': '📦',
        'color': '#795548',
        'description': 'Uncategorized transactions',
        'subcategories': {
            'ATM Withdrawal': {
                'keywords': ['atm', 'cash withdrawal', 'atw', 'atm/cash'],
                'patterns': [r'.*atm.*', r'.*cash.*withdrawal.*']
            },
            'Bank Charges': {
                'keywords': ['bank charge', 'service charge', 'annual fee', 'sms charge'],
                'patterns': [r'.*bank.*charge.*', r'.*service.*charge.*']
            },
            'Uncategorized': {
                'keywords': [],
                'patterns': []
            }
        }
    }
}


# ============================================================================
# QUICK LOOKUP FOR COMMON MERCHANTS (supplement to database)
# ============================================================================

# These are for very common merchants that need fast lookup
# Full list is in merchant_database.json
KNOWN_MERCHANTS = {
    # Stock Brokers
    'zerodha': ('Investments', 'Stocks & Trading'),
    'groww': ('Investments', 'Stocks & Trading'),
    'upstox': ('Investments', 'Stocks & Trading'),
    'razorpay': ('Investments', 'Stocks & Trading'),
    'razpbse': ('Investments', 'Stocks & Trading'),
    
    # Food Delivery
    'swiggy': ('Food & Dining', 'Food Delivery'),
    'zomato': ('Food & Dining', 'Food Delivery'),
    
    # Groceries
    'bigbasket': ('Food & Dining', 'Groceries'),
    'blinkit': ('Food & Dining', 'Groceries'),
    'dmart': ('Food & Dining', 'Groceries'),
    
    # Shopping
    'amazon': ('Shopping', 'Online Shopping'),
    'flipkart': ('Shopping', 'Online Shopping'),
    'myntra': ('Shopping', 'Online Shopping'),
    
    # Streaming
    'netflix': ('Entertainment', 'Streaming Services'),
    'hotstar': ('Entertainment', 'Streaming Services'),
    'spotify': ('Entertainment', 'Streaming Services'),
    
    # Transport
    'uber': ('Transportation', 'Taxi & Rideshare'),
    'ola cabs': ('Transportation', 'Taxi & Rideshare'),
    'rapido': ('Transportation', 'Taxi & Rideshare'),
}


# ============================================================================
# PERSONAL NAME DETECTION
# ============================================================================

# Common Indian name patterns that should NOT be matched as businesses
# These are used to detect personal transfers

# Common Indian first names (sample - not exhaustive)
COMMON_INDIAN_FIRST_NAMES = {
    # Female names
    'lakshmi', 'laksmi', 'priya', 'anjali', 'pooja', 'puja', 'divya', 'sneha',
    'kavitha', 'kavita', 'meena', 'sunita', 'anita', 'geeta', 'gita', 'rekha',
    'radha', 'sita', 'padma', 'kamala', 'shanti', 'savita', 'usha', 'lata',
    'asha', 'nisha', 'ritu', 'neha', 'swati', 'pallavi', 'shalini', 'deepa',
    'rani', 'devi', 'sarita', 'mamta', 'jyoti', 'shobha', 'vasudha', 'bhavna',
    'archana', 'supriya', 'sangita', 'sangeeta', 'rashmi', 'uma', 'vani',
    'vidya', 'maya', 'suman', 'kalpana', 'sarala', 'renuka', 'aruna',
    
    # Male names
    'ravi', 'kumar', 'raj', 'suresh', 'ramesh', 'mahesh', 'ganesh', 'naresh',
    'dinesh', 'rajesh', 'mukesh', 'rakesh', 'sunil', 'anil', 'vijay', 'sanjay',
    'ajay', 'amit', 'sumit', 'rohit', 'mohit', 'ankit', 'nikhil', 'rahul',
    'deepak', 'ashok', 'vinod', 'pramod', 'manoj', 'arun', 'varun', 'kiran',
    'mohan', 'sohan', 'gopal', 'shyam', 'krishna', 'venkat', 'srinivas',
    'satish', 'girish', 'harish', 'rajendra', 'surendra', 'narendra', 'devendra',
    'jitendra', 'mahendra', 'yogendra', 'birendra', 'upendra', 'ravindra',
    'sachin', 'vikas', 'vivek', 'alok', 'ashish', 'manish', 'puneet', 'lalit',
    'gaurav', 'pankaj', 'saurabh', 'prashant', 'neeraj', 'sandeep', 'kuldeep',
    'jagdish', 'satya', 'prakash', 'subhash', 'umesh', 'nilesh', 'hitesh',
    
    # Names that could be confused with businesses (Lakshmi, Ganesha, etc.)
    # but when alone (not with "jewellers", "stores", etc.) are personal names
}

# Business suffixes that indicate a company/shop, not a person
BUSINESS_SUFFIXES = {
    'jewellers', 'jewellery', 'jewelry', 'gold', 'silvers',
    'stores', 'store', 'shop', 'mart', 'bazaar', 'bazar',
    'enterprises', 'enterprise', 'pvt', 'ltd', 'limited', 'private',
    'industries', 'industry', 'traders', 'trading', 'trade',
    'services', 'service', 'solutions', 'systems',
    'hospital', 'clinic', 'pharmacy', 'medical', 'medicals',
    'restaurant', 'hotel', 'cafe', 'foods', 'food',
    'electronics', 'electric', 'electricals',
    'automobiles', 'motors', 'auto',
    'textiles', 'textile', 'fabrics',
    'agencies', 'agency', 'consultants', 'consulting',
    'academy', 'institute', 'school', 'college', 'university',
    'bank', 'finance', 'financial', 'insurance',
    'builders', 'constructions', 'realty', 'properties',
    'communications', 'telecom', 'mobile', 'mobiles',
    'labs', 'laboratory', 'laboratories', 'diagnostic', 'diagnostics',
    'chemist', 'druggist', 'pharma',
    'supermarket', 'hypermarket', 'retail', 'wholesale',
    'international', 'national', 'global', 'india',
    'corp', 'corporation', 'inc', 'co', 'company',
}


def _is_personal_name(text: str) -> bool:
    """
    Check if the text appears to be a personal name rather than a business.
    
    Rules:
    1. If text contains business suffixes → NOT a personal name
    2. If text is a known merchant → NOT a personal name
    3. If text matches common Indian name patterns → IS a personal name
    4. Single word that's not in merchant database → likely personal name
    """
    text_lower = text.lower().strip()
    words = text_lower.split()
    
    # Check for business suffixes
    for word in words:
        if word in BUSINESS_SUFFIXES:
            return False
    
    # Check if it's a known merchant from database
    for merchant in KNOWN_MERCHANT_NAMES:
        if merchant in text_lower:
            return False
    
    # Check quick lookup merchants
    for merchant in KNOWN_MERCHANTS.keys():
        if merchant in text_lower:
            return False
    
    # Check if any word is a common Indian first name
    for word in words:
        # Remove common prefixes like "mr", "mrs", "dr", etc.
        clean_word = word.replace('mr', '').replace('mrs', '').replace('ms', '').replace('dr', '').strip()
        if clean_word in COMMON_INDIAN_FIRST_NAMES:
            return True
    
    # If it's a short phrase (1-3 words) without business indicators, might be a name
    if len(words) <= 3 and not any(w in BUSINESS_SUFFIXES for w in words):
        # Additional check: no numbers, no special patterns
        if not any(char.isdigit() for char in text_lower):
            # Could be a personal name, but we're not 100% sure
            # Return True only if it looks like a name pattern
            # Pattern: "Firstname" or "Firstname Lastname" 
            if len(words) == 1 and len(words[0]) >= 3:
                return True
            if len(words) == 2 and all(len(w) >= 2 for w in words):
                return True
    
    return False


# Patterns to identify personal transfers (not business payments)
PERSONAL_TRANSFER_PATTERNS = [
    r'.*neft[-/\s].*to\s+[A-Z][a-z]+\s*[A-Z]?.*',  # NEFT to Person Name
    r'.*imps[-/\s].*to\s+[A-Z][a-z]+\s*[A-Z]?.*',  # IMPS to Person Name
    r'.*transfer\s+to\s+[A-Z][a-z]+.*',  # Transfer to Person
    r'.*upi[-/].*@[a-z]+bank.*',  # UPI with personal bank handle
    r'.*upi[-/].*@oksbi.*',  # SBI personal
    r'.*upi[-/].*@okicici.*',  # ICICI personal  
    r'.*upi[-/].*@okhdfc.*',  # HDFC personal
    r'.*upi[-/].*@okhdfcbank.*',  # HDFC personal
    r'.*upi[-/].*@axl.*',  # Axis personal
    r'.*mb[-/].*neft.*',  # Mobile Banking NEFT
]

# Patterns to identify business/merchant UPI payments
BUSINESS_UPI_PATTERNS = [
    r'.*@paytm.*',
    r'.*@ybl.*',  # PhonePe merchants often use @ybl
    r'.*@razorpay.*',
    r'.*@airtel.*',
    r'.*@jio.*',
    r'.*merchant.*',
    r'.*store.*',
    r'.*shop.*',
    r'.*retail.*',
    r'.*@icici$',  # Business ICICI (not okicici)
    r'.*@hdfc$',   # Business HDFC (not okhdfc)
]


# ============================================================================
# CATEGORIZATION ENGINE
# ============================================================================

class RefinedCategorizer:
    """Smart transaction categorizer with refined rules and merchant database."""
    
    def __init__(self, user_mappings_file: str = 'user_category_mappings.json'):
        self.user_mappings_file = user_mappings_file
        self.user_mappings = self._load_user_mappings()
        self.categories = REFINED_CATEGORIES
        self.known_merchants = KNOWN_MERCHANTS
        self.merchant_lookup = MERCHANT_LOOKUP
    
    def _load_user_mappings(self) -> Dict[str, Any]:
        """Load user-defined category mappings."""
        try:
            if os.path.exists(self.user_mappings_file):
                with open(self.user_mappings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load user mappings: {e}")
        return {'exact_matches': {}, 'keywords': {}, 'patterns': {}}
    
    def _save_user_mappings(self):
        """Save user mappings to file."""
        try:
            with open(self.user_mappings_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_mappings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save user mappings: {e}")
    
    def _check_merchant_database(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Check if description matches any merchant in the database.
        Returns category info if found, None otherwise.
        
        Uses word boundary matching to avoid false positives like:
        - "RAVI KUMAR" matching "vi" (telecom)
        - "LAKSHMI" matching parts of jewelry shop names
        """
        desc_lower = description.lower()
        
        # Check merchant database (longer matches first for accuracy)
        sorted_merchants = sorted(self.merchant_lookup.keys(), key=len, reverse=True)
        for merchant in sorted_merchants:
            # Skip very short merchant names (2 chars or less) - they cause false positives
            if len(merchant) <= 2:
                continue
                
            # Use word boundary matching for short names (3-4 chars)
            if len(merchant) <= 4:
                # Must be a whole word match
                pattern = r'\b' + re.escape(merchant) + r'\b'
                if re.search(pattern, desc_lower):
                    cat, subcat = self.merchant_lookup[merchant]
                    return {
                        'category': cat,
                        'subcategory': subcat,
                        'confidence': 'high',
                        'reason': f'Merchant database: {merchant}'
                    }
            else:
                # Longer names can use substring match
                if merchant in desc_lower:
                    cat, subcat = self.merchant_lookup[merchant]
                    return {
                        'category': cat,
                        'subcategory': subcat,
                        'confidence': 'high',
                        'reason': f'Merchant database: {merchant}'
                    }
        
        return None
    
    def _extract_payee_name(self, description: str) -> Optional[str]:
        """
        Extract the payee/recipient name from a transfer description.
        Examples:
        - "NEFT/123456/TO LAKSHMI" -> "LAKSHMI"
        - "UPI/123456789/RAVI KUMAR" -> "RAVI KUMAR"
        - "IMPS/REF123/TO SURESH" -> "SURESH"
        """
        desc_upper = description.upper()
        
        # Pattern: "TO <NAME>" at the end
        to_match = re.search(r'\bTO\s+([A-Z][A-Z\s]+)$', desc_upper)
        if to_match:
            return to_match.group(1).strip()
        
        # Pattern: After last "/" 
        if '/' in desc_upper:
            parts = desc_upper.split('/')
            last_part = parts[-1].strip()
            # Check if it looks like a name (not a number or code)
            if last_part and not last_part.isdigit() and len(last_part) > 2:
                return last_part
        
        return None
    
    def categorize(self, description: str, amount: float) -> Dict[str, Any]:
        """
        Categorize a transaction.
        
        Order of checks:
        1. User-defined exact matches (highest priority)
        2. User-defined keywords
        3. Income transactions (positive amounts)
        4. Merchant database lookup (GRT, Bhima, Apollo, etc.)
        5. Quick merchant lookup (Swiggy, Zomato, etc.)
        6. Money transfer detection (NEFT/IMPS to personal names)
        7. Category keyword/pattern matching
        
        Returns:
            Dict with category, subcategory, confidence, and reason
        """
        desc_lower = description.lower().strip()
        desc_upper = description.upper().strip()
        
        # Step 1: Check user-defined exact matches (highest priority)
        if desc_lower in self.user_mappings.get('exact_matches', {}):
            mapping = self.user_mappings['exact_matches'][desc_lower]
            return {
                'category': mapping['category'],
                'subcategory': mapping['subcategory'],
                'confidence': 'high',
                'reason': 'User-defined exact match'
            }
        
        # Step 2: Check user-defined keywords
        for keyword, mapping in self.user_mappings.get('keywords', {}).items():
            if keyword in desc_lower:
                return {
                    'category': mapping['category'],
                    'subcategory': mapping['subcategory'],
                    'confidence': 'high',
                    'reason': f'User-defined keyword: {keyword}'
                }
        
        # Step 3: Handle income transactions
        if amount > 0:
            return self._categorize_income(desc_lower)
        
        # Step 4: Check merchant database FIRST (this catches GRT, Bhima, Apollo, etc.)
        merchant_result = self._check_merchant_database(desc_lower)
        if merchant_result:
            return merchant_result
        
        # Step 5: Check quick lookup merchants
        for merchant, (cat, subcat) in self.known_merchants.items():
            if merchant in desc_lower:
                return {
                    'category': cat,
                    'subcategory': subcat,
                    'confidence': 'high',
                    'reason': f'Known merchant: {merchant}'
                }
        
        # Step 6: Check if this is a money transfer to a person
        # Extract payee name and check if it's a personal name
        payee_name = self._extract_payee_name(description)
        if payee_name and _is_personal_name(payee_name):
            # This is a transfer to a person
            return self._categorize_transfer(desc_lower, desc_upper)
        
        # Also check general transfer patterns
        if self._is_money_transfer(desc_lower, desc_upper):
            return self._categorize_transfer(desc_lower, desc_upper)
        
        # Step 6: Systematic category matching by priority
        return self._categorize_expense(desc_lower, amount)
    
    def _categorize_income(self, description: str) -> Dict[str, Any]:
        """Categorize income transactions."""
        income_cat = self.categories['Income']
        
        for subcat_name, subcat_info in income_cat['subcategories'].items():
            for keyword in subcat_info.get('keywords', []):
                if keyword in description:
                    return {
                        'category': 'Income',
                        'subcategory': subcat_name,
                        'confidence': 'high',
                        'reason': f'Income keyword: {keyword}'
                    }
            
            for pattern in subcat_info.get('patterns', []):
                if re.search(pattern, description, re.IGNORECASE):
                    return {
                        'category': 'Income',
                        'subcategory': subcat_name,
                        'confidence': 'medium',
                        'reason': f'Income pattern match'
                    }
        
        return {
            'category': 'Income',
            'subcategory': 'Other Income',
            'confidence': 'low',
            'reason': 'Default income category'
        }
    
    
    def _is_money_transfer(self, desc_lower: str, desc_upper: str) -> bool:
        """
        Determine if a transaction is a money transfer (not a purchase).
        
        Key indicators of money transfer:
        - Contains NEFT/IMPS/RTGS 
        - NOT to a known merchant from database
        - Personal name pattern detected
        """
        transfer_keywords = ['neft', 'imps', 'rtgs', 'fund transfer', 'net banking']
        
        if not any(kw in desc_lower for kw in transfer_keywords):
            return False
        
        # Check if it's to a known merchant (from database or quick lookup)
        if self._check_merchant_database(desc_lower):
            return False
        
        for merchant in self.known_merchants.keys():
            if merchant in desc_lower:
                return False
        
        # If it has NEFT/IMPS and no merchant match, likely a personal transfer
        return True
    
    def _categorize_transfer(self, desc_lower: str, desc_upper: str) -> Dict[str, Any]:
        """Categorize money transfer transactions."""
        if 'neft' in desc_lower:
            subcat = 'NEFT Transfer'
        elif 'imps' in desc_lower:
            subcat = 'IMPS Transfer'
        elif 'rtgs' in desc_lower:
            subcat = 'RTGS Transfer'
        else:
            subcat = 'Bank Transfer'
        
        return {
            'category': 'Money Transfer',
            'subcategory': subcat,
            'confidence': 'high',
            'reason': 'Identified as personal money transfer'
        }
    
    def _categorize_expense(self, description: str, amount: float) -> Dict[str, Any]:
        """Categorize expense transactions by checking categories in priority order."""
        
        # Sort categories by priority
        sorted_categories = sorted(
            self.categories.items(),
            key=lambda x: x[1].get('priority', 99)
        )
        
        for cat_name, cat_info in sorted_categories:
            if cat_name in ['Income', 'Money Transfer', 'Other']:
                continue
            
            for subcat_name, subcat_info in cat_info.get('subcategories', {}).items():
                # Check keywords
                for keyword in subcat_info.get('keywords', []):
                    if keyword in description:
                        return {
                            'category': cat_name,
                            'subcategory': subcat_name,
                            'confidence': 'high',
                            'reason': f'Keyword match: {keyword}'
                        }
                
                # Check patterns
                for pattern in subcat_info.get('patterns', []):
                    if re.search(pattern, description, re.IGNORECASE):
                        return {
                            'category': cat_name,
                            'subcategory': subcat_name,
                            'confidence': 'medium',
                            'reason': f'Pattern match'
                        }
        
        # Check for ATM withdrawal
        if 'atm' in description or 'cash withdrawal' in description:
            return {
                'category': 'Other',
                'subcategory': 'ATM Withdrawal',
                'confidence': 'high',
                'reason': 'ATM/Cash withdrawal detected'
            }
        
        # Default to Other
        return {
            'category': 'Other',
            'subcategory': 'Uncategorized',
            'confidence': 'low',
            'reason': 'No category match found'
        }
    
    def learn(self, description: str, category: str, subcategory: str, 
              match_type: str = 'keyword') -> bool:
        """
        Learn from user corrections.
        
        Args:
            description: Transaction description
            category: Correct category
            subcategory: Correct subcategory
            match_type: 'exact' or 'keyword'
        """
        try:
            desc_lower = description.lower().strip()
            
            if match_type == 'exact':
                self.user_mappings.setdefault('exact_matches', {})[desc_lower] = {
                    'category': category,
                    'subcategory': subcategory,
                    'learned_at': datetime.now().isoformat()
                }
            else:
                # Extract a keyword from the description
                words = desc_lower.split()
                keyword = max(words, key=len) if words else desc_lower
                self.user_mappings.setdefault('keywords', {})[keyword] = {
                    'category': category,
                    'subcategory': subcategory,
                    'learned_at': datetime.now().isoformat()
                }
            
            self._save_user_mappings()
            return True
        except Exception as e:
            print(f"Error learning mapping: {e}")
            return False
    
    def get_all_categories(self) -> Dict[str, List[str]]:
        """Get all categories with their subcategories."""
        return {
            cat_name: list(cat_info['subcategories'].keys())
            for cat_name, cat_info in self.categories.items()
        }
    
    def get_category_info(self, category: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a category."""
        return self.categories.get(category)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def categorize_transaction(description: str, amount: float) -> Dict[str, str]:
    """
    Quick categorization function for backward compatibility.
    """
    categorizer = RefinedCategorizer()
    result = categorizer.categorize(description, amount)
    return {
        'category': result['category'],
        'subcategory': result['subcategory']
    }


def get_all_categories() -> Dict[str, List[str]]:
    """Get all available categories."""
    categorizer = RefinedCategorizer()
    return categorizer.get_all_categories()


def get_category_colors() -> Dict[str, str]:
    """Get color mapping for all categories."""
    return {
        cat_name: cat_info['color']
        for cat_name, cat_info in REFINED_CATEGORIES.items()
    }


def get_category_icons() -> Dict[str, str]:
    """Get icon mapping for all categories."""
    return {
        cat_name: cat_info['icon']
        for cat_name, cat_info in REFINED_CATEGORIES.items()
    }


# Export for use
__all__ = [
    'RefinedCategorizer',
    'REFINED_CATEGORIES',
    'categorize_transaction',
    'get_all_categories',
    'get_category_colors',
    'get_category_icons'
]
