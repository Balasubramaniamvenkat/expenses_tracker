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
9. TRAVEL - Rail, flights, accommodation, and travel bookings
10. TRANSPORTATION - Fuel, Taxi, Local Public Transport
11. TELECOM - Mobile, Internet, and TV services
12. UTILITIES - Electricity, Water, and Gas
13. ENTERTAINMENT - Streaming, Movies, Games
14. HOUSING - Rent, Maintenance, Society Fees
15. OTHER - Uncategorized transactions

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
        if (category, subcategory) == ('Utilities', 'Government Services'):
            category = 'Taxes & Government'
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
            # Payouts credited by brokers / mutual funds (assigned by the
            # incoming-credit rules, not by keywords)
            'Investment Returns': {
                'keywords': [],
                'patterns': []
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
        'description': 'School, College, Tuition, Entrance Exams, Training, Courses, Books',
        'subcategories': {
            'Entrance Exams & Applications': {
                'keywords': [
                    'entrance exam', 'entrance test', 'exam fee', 'examination fee',
                    'application fee', 'admission test', 'jee', 'kcet', 'comedk',
                    'viteee', 'pessat', 'bitsat', 'neet'
                ],
                'patterns': []
            },
            'College & University': {
                'keywords': [
                    'college', 'university', 'semester fee', 'admission fee',
                    'convocation', 'degree', 'graduation', 'post graduation',
                    'mba', 'engineering', 'medical college', 'institute',
                    'iit', 'iim', 'nit', 'bits', 'vit', 'pes', 'dsu',
                    'dayananda sagar university', 'dayananda sagar',
                    'dayanand sagar', 'dayanad sagar',
                    'amrita vishwa vidyapeetham', 'amrita vishwa vidyapeeth',
                    'amrita vishwa vidyape', 'amrita vishwa vidyap',
                    'amrita vishwa vidya', 'amritha vishwa vidyapeetham',
                    'amritha vishwa vidya', 'avv',
                    'aoap amrita', 'aoapamrita'
                ],
                'patterns': [r'.*college.*fee.*', r'.*university.*', r'.*semester.*']
            },
            'School Fees': {
                'keywords': [
                    'school', 'school fee', 'school fees',
                    'vidyalaya', 'academy', 'cbse', 'icse', 'state board',
                    'primary school', 'high school', 'pre-school', 'nursery',
                    'kindergarten', 'play school'
                ],
                'patterns': [r'.*school.*fee.*', r'.*school.*']
            },
            'Coaching & Tuition': {
                'keywords': [
                    'coaching', 'tuition', 'math', 'maths', 'mathematics',
                    'physics', 'chemistry', 'biology', 'science', 'mathsgym',
                    'byjus', 'byju', 'unacademy', 'vedantu', 'aakash', 'allen',
                    'fiitjee', 'resonance', 'physics wallah', 'whitehat', 'toppr',
                    'extra class'
                ],
                'patterns': [r'.*coaching.*', r'.*byjus.*', r'.*unacademy.*']
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
            'Books & Materials': {
                'keywords': [
                    'book', 'books', 'textbook', 'stationery', 'notebook',
                    'study material', 'kindle', 'amazon kindle', 'audible'
                ],
                'patterns': [r'.*\bbooks?\b.*', r'.*\btextbook.*', r'.*stationery.*']
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
                'patterns': [r'.*\blabs?\b.*', r'.*\blaboratory\b.*', r'.*diagnostic.*', r'.*thyrocare.*', r'.*pathology.*']
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
                    'restaurant', 'cafe', 'dhaba', 'food court',
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

    # Priority 8.5: Travel
    'Travel': {
        'priority': 8.5,
        'icon': '🧳',
        'color': '#5C6BC0',
        'description': 'Rail, flights, accommodation, and travel bookings',
        'subcategories': {
            'Rail & Train': {
                'keywords': ['irctc', 'railway', 'train ticket', 'train booking', 'rail ticket'],
                'patterns': [r'.*\birctc\b.*', r'.*\btrain\s+(ticket|booking)\b.*', r'.*\brailway\b.*']
            },
            'Flights': {
                'keywords': [
                    'flight', 'airfare', 'air india', 'indigo', 'spicejet',
                    'vistara', 'akasa air', 'air asia'
                ],
                'patterns': [r'.*\bflight\b.*', r'.*\bairfare\b.*']
            },
            'Hotels & Accommodation': {
                'keywords': [
                    'hotel booking', 'hotel reservation', 'hotel stay',
                    'room booking', 'accommodation', 'lodging', 'homestay',
                    'resort', 'oyo', 'treebo', 'fabhotels', 'airbnb'
                ],
                'patterns': [
                    r'.*\bhotel\s+(booking|reservation|stay)\b.*',
                    r'.*\b(room|accommodation)\s+booking\b.*',
                    r'.*\b(lodging|homestay|resort)\b.*'
                ]
            },
            'Intercity Bus': {
                'keywords': ['redbus', 'abhibus', 'bus booking', 'coach booking'],
                'patterns': [r'.*\b(bus|coach)\s+booking\b.*']
            },
            'Travel Booking': {
                'keywords': ['makemytrip', 'goibibo', 'cleartrip', 'yatra', 'ixigo', 'easemytrip'],
                'patterns': [r'.*\b(travel|tour)\s+(booking|agency)\b.*']
            },
            'Tours & Activities': {
                'keywords': ['tour package', 'sightseeing', 'travel agency', 'guided tour'],
                'patterns': [r'.*\b(tour|travel)\s+(package|agency)\b.*']
            }
        }
    },

    # Priority 9: Transportation
    'Transportation': {
        'priority': 9,
        'icon': '🚗',
        'color': '#FFCE56',
        'description': 'Local transport, fuel, and vehicle expenses',
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
                    'metro', 'bmtc', 'best', 'dtc', 'travel card'
                ],
                'patterns': [r'.*\bmetro\b.*', r'.*\b(bmtc|best|dtc)\b.*']
            },
            'Parking & Toll': {
                'keywords': [
                    'parking', 'toll', 'fastag', 'nhai', 'expressway', 'highway'
                ],
                'patterns': [r'.*parking.*', r'.*toll.*', r'.*fastag.*']
            },
        }
    },

    # Priority 9.5: Telecom
    'Telecom': {
        'priority': 9.5,
        'icon': '📱',
        'color': '#26A69A',
        'description': 'Mobile, internet, and television services',
        'subcategories': {
            'Mobile & Phone': {
                'keywords': ['airtel', 'jio', 'vodafone', 'vi', 'bsnl', 'mtnl', 'mobile bill', 'phone bill', 'recharge', 'prepaid', 'postpaid'],
                'patterns': [
                    r'.*\b(mobile|phone)\s+bill\b.*',
                    r'.*\b(recharge|prepaid|postpaid)\b.*'
                ]
            },
            'Internet & Broadband': {
                'keywords': [
                    'internet', 'broadband', 'wifi', 'act fibernet', 'jio fiber',
                    'airtel xstream', 'hathway', 'tikona', 'you broadband',
                    'excitel', 'spectra', 'alliance broadband', 'asianet'
                ],
                'patterns': [r'.*\binternet\b.*', r'.*\bbroadband\b.*', r'.*\bwifi\b.*']
            },
            'DTH & Cable': {
                'keywords': [
                    'dth', 'tata sky', 'dish tv', 'airtel dth', 'videocon d2h',
                    'sun direct', 'cable tv', 'tv recharge'
                ],
                'patterns': [r'.*\bdth\b.*', r'.*\bcable\s+tv\b.*']
            }
        }
    },

    # Priority 10: Utilities
    'Utilities': {
        'priority': 10,
        'icon': '💡',
        'color': '#4BC0C0',
        'description': 'Electricity, water, and gas',
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
            'Gas & LPG': {
                'keywords': [
                    'gas', 'lpg', 'indane', 'bharat gas', 'hp gas', 'piped gas',
                    'png', 'igl', 'mahanagar gas', 'cooking gas', 'cylinder'
                ],
                'patterns': [r'.*\blpg\b.*', r'.*\b(gas\s*(cylinder|booking|agency|connection))\b.*', r'.*indane.*', r'.*piped.*gas.*']
            },
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

    # Priority 12: Subscriptions (recurring digital services)
    'Subscriptions': {
        'priority': 12,
        'icon': '🔄',
        'color': '#AB47BC',
        'description': 'Apple, Google, recurring digital service subscriptions',
        'subcategories': {
            'App Subscriptions': {
                'keywords': [
                    'apple services', 'apple.com', 'apple icloud', 'google storage',
                    'google one', 'google cloud', 'microsoft 365', 'office 365',
                    'adobe', 'creative cloud', 'canva', 'notion', 'evernote',
                    'dropbox', 'icloud', 'telegram premium'
                ],
                'patterns': [r'.*apple.*services.*', r'.*google.*cloud.*', r'.*microsoft.*365.*']
            },
            'Cloud & Storage': {
                'keywords': [
                    'aws', 'azure', 'google cloud platform', 'cloud storage',
                    'hosting', 'domain', 'godaddy', 'namecheap'
                ],
                'patterns': [r'.*cloud.*storage.*', r'.*hosting.*']
            },
            'Membership': {
                'keywords': [
                    'membership', 'subscription', 'annual plan', 'monthly plan',
                    'premium plan', 'pro plan'
                ],
                'patterns': [r'.*membership.*', r'.*subscription.*']
            }
        }
    },

    # Priority 13: Housing
    'Housing': {
        'priority': 13,
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

    # Priority 14: Individual Transfers (UPI to persons without context)
    'Individual Transfers': {
        'priority': 14,
        'icon': '👤',
        'color': '#78909C',
        'description': 'UPI payments to individuals (domestic help, personal payments)',
        'subcategories': {
            'Domestic Help': {
                'keywords': [],
                'patterns': []
            },
            'Personal Payment': {
                'keywords': [],
                'patterns': []
            }
        }
    },

    # Priority 99: Other (catch-all)
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
# INDIA TAXONOMY REVISION
# ----------------------------------------------------------------------------
# Every category belongs to exactly one GROUP so that day-to-day expenses are
# never mixed with investment, planned, or plain money movement categories.
#   Income       - money coming in
#   Investment   - wealth building and education (stocks, MF, gold, education ...)
#   Planned      - big planned outflows (insurance, loans/EMI, taxes)
#   Expense      - everyday living costs
#   Transfer     - money moved to people / cash (not a spend by itself)
# ============================================================================

# Dead category: nothing ever produced it (NEFT/IMPS go to Individual Transfers)
REFINED_CATEGORIES.pop('Money Transfer', None)

# ATM cash gets its own category (it is cash-out, not an uncategorized expense)
REFINED_CATEGORIES['Other']['subcategories'].pop('ATM Withdrawal', None)

REFINED_CATEGORIES['Investments']['subcategories']['Other Investments'] = {
    'keywords': ['investment', 'investme', 'nsc', 'kisan vikas', 'bonds', 'ncd', 'reit'],
    'patterns': []
}
REFINED_CATEGORIES['Transportation']['subcategories']['Vehicle Service & Repair'] = {
    'keywords': ['garage', 'service centre', 'service center', 'car wash', 'tyre', 'tire',
                 'puncture', 'battery', 'spare parts', 'automobile'],
    'patterns': []
}
REFINED_CATEGORIES['Shopping']['subcategories']['Local Shops & Vendors'] = {
    'keywords': [],
    'patterns': []
}
REFINED_CATEGORIES['Individual Transfers']['subcategories']['Family & Friends'] = {
    'keywords': [],
    'patterns': []
}
REFINED_CATEGORIES['Individual Transfers']['subcategories'].update({
    'NEFT Transfer': {'keywords': [], 'patterns': []},
    'IMPS Transfer': {'keywords': [], 'patterns': []},
    'RTGS Transfer': {'keywords': [], 'patterns': []},
    'Bank Transfer': {'keywords': [], 'patterns': []},
})

REFINED_CATEGORIES['Recurring Commitments'] = {
    'priority': 3.5,
    'icon': '📅',
    'color': '#5D4037',
    'description': 'Standing instructions and recurring financial commitments',
    'subcategories': {
        'Standing Instruction (EMI/SIP)': {
            'keywords': [],
            'patterns': []
        }
    }
}

REFINED_CATEGORIES.update({
    'Loans & EMI': {
        'priority': 3,
        'icon': '🏦',
        'color': '#5D4037',
        'description': 'Home/car/personal loan EMIs, credit card bill payments',
        'subcategories': {
            'Home Loan EMI': {
                'keywords': ['home loan', 'housing loan', 'lic housing', 'hdfc ltd', 'pnb housing',
                             'bajaj housing', 'can fin homes'],
                'patterns': []
            },
            'Vehicle Loan EMI': {
                'keywords': ['car loan', 'auto loan', 'vehicle loan', 'two wheeler loan',
                             'bike loan', 'tvs credit', 'mahindra finance', 'hero fincorp'],
                'patterns': []
            },
            'Personal & Consumer Loan': {
                'keywords': ['personal loan', 'bajaj finance', 'bajaj finserv', 'loan repay',
                             'loan emi', 'moneyview', 'kreditbee', 'navi loan', 'fullerton',
                             'muthoot finance', 'manappuram', 'cred club'],
                'patterns': [r'.*\bemi\b.*', r'.*\bnach\b.*loan.*']
            },
            'Credit Card Payment': {
                'keywords': ['credit card', 'cc payment', 'cardpayment', 'billdesk cc', 'cred.club',
                             'cred club', 'creditcard'],
                'patterns': [r'.*\bcc\s*bill.*']
            }
        }
    },
    'Taxes & Government': {
        'priority': 4.5,
        'icon': '🏛️',
        'color': '#455A64',
        'description': 'Income tax, GST, property tax, challans, government fees',
        'subcategories': {
            'Income Tax': {
                'keywords': ['cbdt', 'income tax', 'incometax', 'advance tax', 'tds payment'],
                'patterns': []
            },
            'GST & Other Taxes': {
                'keywords': ['gst payment', 'gstn', 'professional tax', 'pt payment'],
                'patterns': []
            },
            'Property & Municipal Tax': {
                'keywords': ['property tax', 'bbmp', 'municipal', 'corporation tax', 'panchayat',
                             'water tax', 'bda', 'khata'],
                'patterns': []
            },
            'Government Services': {
                'keywords': ['hsrp', 'passport', 'rto', 'parivahan', 'challan', 'e-challan',
                             'traffic police', 'stamp duty', 'registration fee', 'sub registrar',
                             'aadhaar', 'digilocker', 'echallan'],
                'patterns': []
            }
        }
    },
    'Donations & Charity': {
        'priority': 5.5,
        'icon': '🙏',
        'color': '#FF7043',
        'description': 'Temples, trusts, ashrams, NGOs, religious and charitable giving',
        'subcategories': {
            'Temple & Religious': {
                'keywords': ['temple', 'mandir', 'devasthanam', 'ashram', 'ashramam', 'mutt',
                             'math ', 'gurudwara', 'church', 'mosque', 'dargah', 'tirumala',
                             'tirupati', 'ttd ', 'iskcon', 'anugraha', 'sabha', 'seva'],
                'patterns': []
            },
            'Trust & NGO': {
                'keywords': [' trust', 'foundation', 'charitable', 'charity', 'ngo', 'relief fund',
                             'pm cares', 'cmrf', 'donation', 'ketto', 'giveindia', 'goonj'],
                'patterns': [r'.*\btrust\b.*']
            }
        }
    },
    'Personal Care': {
        'priority': 11.5,
        'icon': '💇',
        'color': '#EC407A',
        'description': 'Salon, beauty, grooming, cosmetics',
        'subcategories': {
            'Salon & Grooming': {
                'keywords': ['salon', 'parlour', 'parlor', 'barber', 'haircut', 'beauty', 'unisex',
                             'looks salon', 'naturals', 'lakme', 'jawed habib', 'green trends'],
                'patterns': []
            },
            'Cosmetics': {
                'keywords': ['nykaa', 'sugar cosmetics', 'mamaearth', 'purplle', 'cosmetic',
                             'body shop'],
                'patterns': []
            }
        }
    },
    'Cash & ATM': {
        'priority': 13.5,
        'icon': '🏧',
        'color': '#90A4AE',
        'description': 'ATM and branch cash withdrawals',
        'subcategories': {
            'ATM Withdrawal': {
                'keywords': ['atm-cash', 'atm cash', 'cash withdrawal', 'atw-', 'nwd-', 'cash wdl'],
                'patterns': [r'.*\batm\b.*']
            }
        }
    },
})

# Group of every category (see header above)
CATEGORY_GROUPS = {
    'Income': 'Income',
    'Investments': 'Investment',
    'Insurance': 'Planned',
    'Loans & EMI': 'Planned',
    'Education': 'Investment',
    'Taxes & Government': 'Planned',
    'Healthcare': 'Expense',
    'Food & Dining': 'Expense',
    'Shopping': 'Expense',
    'Transportation': 'Expense',
    'Travel': 'Expense',
    'Telecom': 'Expense',
    'Utilities': 'Expense',
    'Entertainment': 'Expense',
    'Subscriptions': 'Expense',
    'Housing': 'Expense',
    'Personal Care': 'Expense',
    'Donations & Charity': 'Expense',
    'Individual Transfers': 'Transfer',
    'Cash & ATM': 'Transfer',
    'Recurring Commitments': 'Planned',
    'Other': 'Expense',
}
for _name, _info in REFINED_CATEGORIES.items():
    _info['group'] = CATEGORY_GROUPS.get(_name, 'Expense')

# Housing/Utilities items that moved to the Taxes & Government category
REFINED_CATEGORIES['Utilities']['subcategories'].pop('Government Services', None)


def get_category_group(category: str) -> str:
    """Return Income / Investment / Planned / Expense / Transfer for a category."""
    return CATEGORY_GROUPS.get(category, 'Expense')


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
    'swiggy instamart': ('Food & Dining', 'Groceries'),
    
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
    
    # Subscriptions (recurring digital services)
    'apple services': ('Subscriptions', 'App Subscriptions'),
    'appleservices': ('Subscriptions', 'App Subscriptions'),
    'google cloud': ('Subscriptions', 'Cloud & Storage'),
    'googlecloud': ('Subscriptions', 'Cloud & Storage'),
    'google one': ('Subscriptions', 'App Subscriptions'),
    'microsoft 365': ('Subscriptions', 'App Subscriptions'),
    
    # Shopping - missing merchants from real data
    'innovative retail': ('Food & Dining', 'Groceries'),
    'bbnow': ('Food & Dining', 'Groceries'),
    'bb now': ('Food & Dining', 'Groceries'),
    'jk enterprises': ('Shopping', 'Online Shopping'),
    'j k enterprises': ('Shopping', 'Online Shopping'),
    
    # Education — specific institutions
    'national centre for': ('Education', 'School Fees'),
    'nationalcentreforexcellence': ('Education', 'School Fees'),
    'pes university': ('Education', 'College & University'),
    'pes': ('Education', 'College & University'),
    'dayananda sagar': ('Education', 'College & University'),
    'dsu': ('Education', 'College & University'),
    
    # Astrology consultations
    'astrotalk': ('Entertainment', 'Events & Activities'),
    
    # Investment — brokerage/securities firms
    'axissecurities': ('Investments', 'Stocks & Trading'),
    'axis securities': ('Investments', 'Stocks & Trading'),
    'billdkaxissecurities': ('Investments', 'Stocks & Trading'),
    'icicidirect': ('Investments', 'Stocks & Trading'),
    'icici direct': ('Investments', 'Stocks & Trading'),
    'angel broking': ('Investments', 'Stocks & Trading'),
    'angelone': ('Investments', 'Stocks & Trading'),
    'kotak securities': ('Investments', 'Stocks & Trading'),
    'hdfc securities': ('Investments', 'Stocks & Trading'),
    
    # Food - specific stores from real data
    'cococart': ('Food & Dining', 'Groceries'),
    'natures basket': ('Food & Dining', 'Groceries'),
    'hopcoms': ('Food & Dining', 'Groceries'),
    'swiggyinstamart': ('Food & Dining', 'Groceries'),
    'swiggy instamart': ('Food & Dining', 'Groceries'),
    'instamart': ('Food & Dining', 'Groceries'),
    
    # Home services
    'ctb upvc': ('Housing', 'Home Services'),
    'upvc': ('Housing', 'Home Services'),
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
    'ramya', 'prema', 'ramalakshmi', 'sharada', 'vasantha', 'pushpa',
    'geetha', 'saroja', 'chandra', 'indira', 'gangabai', 'yamuna',
    
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
    # Additional names from real transaction data
    'mohammed', 'mohamed', 'mohammad', 'anbu', 'pasha', 'mahaboob',
    'prema', 'subramani', 'saravanan', 'bethupandi', 'udhayakumar',
    'roshan', 'ramya', 'shaik', 'abdulla', 'dilbar', 'raza', 'mushraf',
    'affan', 'pavan', 'praveen', 'jayateerth', 'ananthan', 'shubham',
    'krishnamoorthy', 'ramalakshmi', 'venkatesh', 'bahadur', 'bist',
    'surathkuma', 'dagdi', 'waji', 'kulkarni', 'biradar', 'suryawanshi',
    'dhirendra', 'saravanakkumar', 'arumugam', 'murugan', 'selvam',
    'palani', 'senthil', 'kathir', 'velu', 'mani', 'ramu',
    'raja', 'rani', 'krishna', 'lakshman', 'bharath', 'karthik',
    'naveen', 'chetan', 'vishal', 'sudhir', 'raghu', 'venkatanarayanan',
    'balasubramaniam', 'jaya', 'daya', 'ganga', 'naga', 'hari', 'bala',
    'veena', 'meera', 'hema', 'mala', 'lata', 'gita', 'sita', 'rita',
    
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


# Context tags in UPI descriptions that hint at the actual business category
# When a UPI payment goes to a personal name BUT contains these clues,
# we categorize by the context instead of marking as "Individual Transfers"
UPI_CONTEXT_TAGS = {
    # Food & Dining context
    'bakery': ('Food & Dining', 'Restaurants'),
    'sweet': ('Food & Dining', 'Restaurants'),
    'sweets': ('Food & Dining', 'Restaurants'),
    'food': ('Food & Dining', 'Restaurants'),
    'foods': ('Food & Dining', 'Restaurants'),
    'restaurant': ('Food & Dining', 'Restaurants'),
    'cafe': ('Food & Dining', 'Cafe & Coffee'),
    'coffee': ('Food & Dining', 'Cafe & Coffee'),
    'tea': ('Food & Dining', 'Cafe & Coffee'),
    'biryani': ('Food & Dining', 'Restaurants'),
    'chicken': ('Food & Dining', 'Restaurants'),
    'mutton': ('Food & Dining', 'Restaurants'),
    'fish': ('Food & Dining', 'Restaurants'),
    'vegetables': ('Food & Dining', 'Groceries'),
    'vegetable': ('Food & Dining', 'Groceries'),
    'fruit': ('Food & Dining', 'Groceries'),
    'fruits': ('Food & Dining', 'Groceries'),
    'grocery': ('Food & Dining', 'Groceries'),
    'provision': ('Food & Dining', 'Groceries'),
    'provisions': ('Food & Dining', 'Groceries'),
    'kirana': ('Food & Dining', 'Groceries'),
    'milk': ('Food & Dining', 'Groceries'),
    'dairy': ('Food & Dining', 'Groceries'),
    'mess': ('Food & Dining', 'Restaurants'),
    'tiffin': ('Food & Dining', 'Restaurants'),
    'juice': ('Food & Dining', 'Cafe & Coffee'),
    'snacks': ('Food & Dining', 'Restaurants'),
    'chaat': ('Food & Dining', 'Restaurants'),
    'paan': ('Food & Dining', 'Restaurants'),
    'rice': ('Food & Dining', 'Groceries'),
    'atta': ('Food & Dining', 'Groceries'),
    'flour': ('Food & Dining', 'Groceries'),
    'oil': ('Food & Dining', 'Groceries'),
    'meat': ('Food & Dining', 'Groceries'),
    'egg': ('Food & Dining', 'Groceries'),
    'eggs': ('Food & Dining', 'Groceries'),
    'dhaba': ('Food & Dining', 'Restaurants'),
    'canteen': ('Food & Dining', 'Restaurants'),

    # Travel and accommodation context
    'hotel booking': ('Travel', 'Hotels & Accommodation'),
    'hotel reservation': ('Travel', 'Hotels & Accommodation'),
    'hotel stay': ('Travel', 'Hotels & Accommodation'),
    'accommodation': ('Travel', 'Hotels & Accommodation'),
    'homestay': ('Travel', 'Hotels & Accommodation'),
    'irctc': ('Travel', 'Rail & Train'),
    'railway': ('Travel', 'Rail & Train'),
    'flight': ('Travel', 'Flights'),
    'redbus': ('Travel', 'Intercity Bus'),
    
    # Healthcare context
    'pharmacy': ('Healthcare', 'Pharmacy'),
    'pharma': ('Healthcare', 'Pharmacy'),
    'chemist': ('Healthcare', 'Pharmacy'),
    'medical': ('Healthcare', 'Pharmacy'),
    'medicals': ('Healthcare', 'Pharmacy'),
    'medicine': ('Healthcare', 'Pharmacy'),
    'hospital': ('Healthcare', 'Hospital'),
    'clinic': ('Healthcare', 'Clinic & Doctor'),
    'dental': ('Healthcare', 'Dental'),
    'physiotherapy': ('Healthcare', 'Wellness & Fitness'),
    'physio': ('Healthcare', 'Wellness & Fitness'),
    'diagnostic': ('Healthcare', 'Diagnostic & Labs'),
    'lab': ('Healthcare', 'Diagnostic & Labs'),
    'pathology': ('Healthcare', 'Diagnostic & Labs'),
    'opticals': ('Healthcare', 'Clinic & Doctor'),
    'optical': ('Healthcare', 'Clinic & Doctor'),
    'eye': ('Healthcare', 'Clinic & Doctor'),
    
    # Shopping context
    'store': ('Shopping', 'Local Shops & Vendors'),
    'stores': ('Shopping', 'Local Shops & Vendors'),
    'shop': ('Shopping', 'Local Shops & Vendors'),
    'mart': ('Shopping', 'Local Shops & Vendors'),
    'retail': ('Shopping', 'Local Shops & Vendors'),
    'emporium': ('Shopping', 'Local Shops & Vendors'),
    'supermarket': ('Food & Dining', 'Groceries'),
    'hypermarket': ('Food & Dining', 'Groceries'),
    'electronics': ('Shopping', 'Electronics'),
    'mobile': ('Shopping', 'Electronics'),
    'mobiles': ('Shopping', 'Electronics'),
    'computer': ('Shopping', 'Electronics'),
    'textiles': ('Shopping', 'Clothing & Fashion'),
    'textile': ('Shopping', 'Clothing & Fashion'),
    'garments': ('Shopping', 'Clothing & Fashion'),
    'tailoring': ('Shopping', 'Clothing & Fashion'),
    'tailor': ('Shopping', 'Clothing & Fashion'),
    'fashion': ('Shopping', 'Clothing & Fashion'),
    'silks': ('Shopping', 'Clothing & Fashion'),
    'silk': ('Shopping', 'Clothing & Fashion'),
    'sarees': ('Shopping', 'Clothing & Fashion'),
    'saree': ('Shopping', 'Clothing & Fashion'),
    
    # Generic business context — when no other tag matches
    'enterprises': ('Shopping', 'Local Shops & Vendors'),
    'enterprise': ('Shopping', 'Local Shops & Vendors'),
    'agency': ('Shopping', 'Local Shops & Vendors'),
    'agencies': ('Shopping', 'Local Shops & Vendors'),
    'corporation': ('Shopping', 'Local Shops & Vendors'),
    
    # Travel context
    'portico': ('Travel', 'Hotels & Accommodation'),
    'sarovar': ('Travel', 'Hotels & Accommodation'),
    'resort': ('Travel', 'Hotels & Accommodation'),
    'lodge': ('Travel', 'Hotels & Accommodation'),
    'homestay': ('Travel', 'Hotels & Accommodation'),
    'tours': ('Travel', 'Tours & Activities'),
    'tour': ('Travel', 'Tours & Activities'),
    'travels': ('Travel', 'Travel Booking'),
    'travel': ('Travel', 'Travel Booking'),
    'taxi': ('Transportation', 'Taxi & Rideshare'),
    'auto': ('Transportation', 'Taxi & Rideshare'),
    'garage': ('Transportation', 'Vehicle Service & Repair'),
    'workshop': ('Transportation', 'Vehicle Service & Repair'),
    'petrol': ('Transportation', 'Fuel'),
    'filling': ('Transportation', 'Fuel'),
    'nissan': ('Transportation', 'Vehicle Service & Repair'),
    'honda': ('Transportation', 'Vehicle Service & Repair'),
    'toyota': ('Transportation', 'Vehicle Service & Repair'),
    'hyundai': ('Transportation', 'Vehicle Service & Repair'),
    'maruti': ('Transportation', 'Vehicle Service & Repair'),
    'suzuki': ('Transportation', 'Vehicle Service & Repair'),
    'automobile': ('Transportation', 'Vehicle Service & Repair'),
    'motors': ('Transportation', 'Vehicle Service & Repair'),
    
    # Education context
    'school': ('Education', 'School Fees'),
    'academy': ('Education', 'Training & Courses'),
    'coaching': ('Education', 'Coaching & Tuition'),
    'tuition': ('Education', 'Coaching & Tuition'),
    'institute': ('Education', 'College & University'),
    'college': ('Education', 'College & University'),
    
    # Utilities context
    'electricity': ('Utilities', 'Electricity'),
    'plumber': ('Housing', 'Home Services'),
    'carpenter': ('Housing', 'Home Services'),
    'electrician': ('Housing', 'Home Services'),
    
    # Housing context
    'maintenance': ('Housing', 'Maintenance'),
    'painting': ('Housing', 'Home Services'),
    'construction': ('Housing', 'Home Services'),
    'builder': ('Housing', 'Home Services'),
    
    # Salon / Personal Care
    'salon': ('Personal Care', 'Salon & Grooming'),
    'parlour': ('Personal Care', 'Salon & Grooming'),
    'parlor': ('Personal Care', 'Salon & Grooming'),
    'beauty': ('Personal Care', 'Salon & Grooming'),
    'barber': ('Personal Care', 'Salon & Grooming'),
    'spa': ('Healthcare', 'Wellness & Fitness'),
    'gym': ('Healthcare', 'Wellness & Fitness'),
    'fitness': ('Healthcare', 'Wellness & Fitness'),
    
    # Jewelry & Gold — classify under Investments
    'thangamaligai': ('Investments', 'Gold & Jewelry'),
    'thangamalig': ('Investments', 'Gold & Jewelry'),
    'jewel': ('Investments', 'Gold & Jewelry'),
    'jewellers': ('Investments', 'Gold & Jewelry'),
    'jewellery': ('Investments', 'Gold & Jewelry'),
    'jewelry': ('Investments', 'Gold & Jewelry'),
    'gold': ('Investments', 'Gold & Jewelry'),
    
    # Government / Regulatory
    'hsrp': ('Taxes & Government', 'Government Services'),

    # Donations / religious / trusts (INB/IFT/<NAME> TRUST, IMPS to ASHRAMAM ...)
    'ashramam': ('Donations & Charity', 'Temple & Religious'),
    'ashram': ('Donations & Charity', 'Temple & Religious'),
    'temple': ('Donations & Charity', 'Temple & Religious'),
    'mandir': ('Donations & Charity', 'Temple & Religious'),
    'devasthanam': ('Donations & Charity', 'Temple & Religious'),
    'anugraha': ('Donations & Charity', 'Temple & Religious'),
    'trust': ('Donations & Charity', 'Trust & NGO'),
    'foundation': ('Donations & Charity', 'Trust & NGO'),

    # Small-shop / local vendor words seen on P2M QR payments
    'ice crea': ('Food & Dining', 'Cafe & Coffee'),
    'icecream': ('Food & Dining', 'Cafe & Coffee'),
    'cake': ('Food & Dining', 'Restaurants'),
    'brownie': ('Food & Dining', 'Restaurants'),
    'pizza': ('Food & Dining', 'Restaurants'),
    'burger': ('Food & Dining', 'Restaurants'),
    'kitchen': ('Food & Dining', 'Restaurants'),
    'cloth': ('Shopping', 'Clothing & Fashion'),
    'readymade': ('Shopping', 'Clothing & Fashion'),
    'footwear': ('Shopping', 'Clothing & Fashion'),
    'stationery': ('Education', 'Books & Materials'),
    'streamflix': ('Entertainment', 'Streaming Services'),
    'google india digital': ('Subscriptions', 'Cloud & Storage'),
    'google play': ('Subscriptions', 'App Subscriptions'),
    'tyre': ('Transportation', 'Vehicle Service & Repair'),
    'puncture': ('Transportation', 'Vehicle Service & Repair'),
    'investme': ('Investments', 'Other Investments'),
    
    # Specific Indian retail chains
    'hopcoms': ('Food & Dining', 'Groceries'),
    'natures basket': ('Food & Dining', 'Groceries'),
    'cococart': ('Food & Dining', 'Groceries'),
    'bigbasket': ('Food & Dining', 'Groceries'),
    'dmart': ('Food & Dining', 'Groceries'),
    'reliance fresh': ('Food & Dining', 'Groceries'),
    'spencer': ('Food & Dining', 'Groceries'),
    'more': ('Shopping', 'Online Shopping'),
    'adidas': ('Shopping', 'Clothing & Fashion'),
    'nike': ('Shopping', 'Clothing & Fashion'),
    'puma': ('Shopping', 'Clothing & Fashion'),
    'flavors': ('Food & Dining', 'Restaurants'),
    'element3': ('Food & Dining', 'Restaurants'),
}


def _merchant_matches(merchant: str, text: str) -> bool:
    """
    Match a merchant name inside text. Names up to 8 chars must not be glued to
    other letters, so 'narayana' does not match inside 'VENKATANARAYANAN'.
    """
    if len(merchant) <= 2:
        return False
    if len(merchant) <= 8:
        return re.search(r'(?<![a-z])' + re.escape(merchant) + r'(?![a-z])', text) is not None
    return merchant in text


def _keyword_matches(keyword: str, text: str) -> bool:
    """Match a category keyword as a whole word or phrase, not a substring."""
    return re.search(
        r'(?<![a-z0-9])' + re.escape(keyword.strip()) + r'(?![a-z0-9])',
        text,
        re.IGNORECASE,
    ) is not None


_IFSC_RE = re.compile(r'\b[a-z]{4}0[a-z0-9]{6}\b')
_PAYU_BANK_BILL_RE = re.compile(
    r'/payu(icici|hdfc|axis|sbi|kotak|idfc|indusind|yes|rbl|citi|amex|hsbc|au)(bank|card)?\s*$'
)


def _extract_upi_payee_name(description: str) -> Optional[str]:
    """
    Extract the payee/recipient name from a UPI transaction description.
    
    UPI format: UPI-{PAYEE NAME}-{handle@bank}-{IFSC}-{refnum}-{remark}
    Examples:
        UPI-RAMYA-PAYTMQR5XTX4V@PTYS-YESB0PTMUPI-358510114445-PAYMENT FROM PHONE
        → "RAMYA"
        UPI-JAYARAM BAKERY-PAYTMQR2810@PAYTM-YESB0PTMUPI-423211-PAYMENT FROM PHONE
        → "JAYARAM BAKERY"
        UPI-APPLE SERVICES-APPLESERVICES.BDSI@ICICI-ICIC0DC0099-501433-MANDATEREQUEST
        → "APPLE SERVICES"
    """
    desc_upper = description.upper().strip()
    
    if desc_upper.startswith('UPI/'):
        parts = [part.strip() for part in description.split('/')]
        if len(parts) >= 4 and parts[1].upper() in ('P2A', 'P2M', 'P2P'):
            payee = parts[3]
            return payee if len(payee) >= 2 else None

    # UPI format: UPI-PAYEE_NAME-handle@bank-IFSC-refnum-remark
    if desc_upper.startswith('UPI-'):
        parts = description.split('-')
        if len(parts) >= 3:
            payee_index = 3 if parts[1].strip().upper() in ('P2A', 'P2M', 'P2P') else 1
            # UPI-AUTOPAY-<MERCHANT>-... : AUTOPAY is the mandate type, not the payee
            if parts[1].strip().upper() == 'AUTOPAY' and len(parts) > 3:
                payee_index = 2
            if len(parts) > payee_index:
                payee = parts[payee_index].strip()
                if payee and len(payee) >= 2:
                    return payee
    
    return None


def _extract_upi_vpa_identifier(description: str) -> Optional[str]:
    """Extract the UPI VPA local-part, excluding the bank handle and suffix fields."""
    if not description.upper().startswith('UPI-'):
        return None
    parts = description.split('-')
    if len(parts) < 3:
        return None
    vpa_index = 4 if parts[1].strip().upper() in ('P2A', 'P2M', 'P2P') else 2
    if parts[1].strip().upper() == 'AUTOPAY' and len(parts) > 3:
        vpa_index = 3
    if len(parts) <= vpa_index or '@' not in parts[vpa_index]:
        return None
    identifier = parts[vpa_index].split('@', 1)[0].strip()
    return identifier or None


def _extract_payee_name_general(description: str) -> Optional[str]:
    """
    Extract the payee/recipient name from non-UPI descriptions.
    Handles NEFT, IMPS, and other formats.
    Examples:
        NEFT/123456/TO LAKSHMI → "LAKSHMI"
        IMPS/REF123/TO SURESH → "SURESH"
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
        if last_part and not last_part.isdigit() and len(last_part) > 2:
            return last_part
    
    return None


def _check_upi_context_tags(description: str) -> Optional[Dict[str, Any]]:
    """
    Check if a UPI description contains context tags that indicate
    the type of business, even when the payee is a personal name.
    
    For example:
        "UPI-JAYARAM BAKERY-..." → bakery → Food & Dining
        "UPI-SHREE MARUTHI CHEMIST-..." → chemist → Healthcare/Pharmacy
        "UPI-ANAGHA TOURS-..." → tours → Transportation/Travel
        "UPI-RAJA NISSAN-..." → nissan → Transportation
    
    Returns category dict if a context tag is found, None otherwise.
    """
    desc_lower = description.lower()
    
    # Check context tags (longer tags first for precision)
    sorted_tags = sorted(UPI_CONTEXT_TAGS.keys(), key=len, reverse=True)
    for tag in sorted_tags:
        # Use word boundary matching for short tags (<=3 chars)
        if len(tag) <= 3:
            pattern = r'\b' + re.escape(tag) + r'\b'
            if re.search(pattern, desc_lower):
                cat, subcat = UPI_CONTEXT_TAGS[tag]
                return {
                    'category': cat,
                    'subcategory': subcat,
                    'confidence': 'medium',
                    'reason': f'UPI context tag: {tag}'
                }
        else:
            if tag in desc_lower:
                cat, subcat = UPI_CONTEXT_TAGS[tag]
                return {
                    'category': cat,
                    'subcategory': subcat,
                    'confidence': 'medium',
                    'reason': f'UPI context tag: {tag}'
                }
    
    return None


def _is_personal_name(text: str) -> bool:
    """
    Check if the text appears to be a personal name rather than a business.
    
    This version is more conservative to avoid false positives.
    
    Rules:
    1. If text contains business suffixes → NOT a personal name
    2. If text is a known merchant → NOT a personal name  
    3. If text contains UPI context tags (bakery, pharmacy, etc.) → NOT a personal name
    4. If text matches common Indian name patterns → IS a personal name
    5. If text has honorifics (MR, MRS, MS) → IS a personal name
    6. Multi-word short text with NO business/context indicators → likely personal name
       (but NOT single unknown words — those could be anything)
    """
    text_lower = text.lower().strip()
    words = text_lower.split()
    
    if not words:
        return False
    
    # Exclude common banking/transaction terms that are NOT personal names
    banking_terms = {
        'cash', 'withdrawal', 'deposit', 'transfer', 'payment', 'refund',
        'reversal', 'charge', 'fee', 'interest', 'emi', 'loan', 'insurance',
        'premium', 'tax', 'gst', 'tds', 'credit', 'debit', 'balance',
        'atm', 'pos', 'neft', 'imps', 'rtgs', 'upi', 'ach', 'ecs',
        'bill', 'recharge', 'topup', 'electricity', 'water', 'gas',
        'mobile', 'broadband', 'internet', 'telephone',
        'account', 'bank', 'branch', 'cheque', 'draft',
    }
    if any(word in banking_terms for word in words):
        return False
    
    # Check for business suffixes
    for word in words:
        if word in BUSINESS_SUFFIXES:
            return False
    
    # Check if it's a known merchant from database
    # Skip very short merchant names (<=2 chars) to avoid false substring matches
    # e.g., "du" (Delhi University) should NOT match inside "abdulla" or "mdu"
    for merchant in KNOWN_MERCHANT_NAMES:
        if len(merchant) <= 2:
            continue
        if len(merchant) <= 4:
            pattern = r'\b' + re.escape(merchant) + r'\b'
            if re.search(pattern, text_lower):
                return False
        elif merchant in text_lower:
            return False
    
    # Check quick lookup merchants (same length-based filtering)
    for merchant in KNOWN_MERCHANTS.keys():
        if len(merchant) <= 2:
            continue
        if len(merchant) <= 4:
            pattern = r'\b' + re.escape(merchant) + r'\b'
            if re.search(pattern, text_lower):
                return False
        elif merchant in text_lower:
            return False
    
    # Check if text contains any UPI context tags (bakery, tours, pharmacy, etc.)
    # If so, this is a business, not a personal name
    for tag in UPI_CONTEXT_TAGS.keys():
        if len(tag) <= 3:
            pattern = r'\b' + re.escape(tag) + r'\b'
            if re.search(pattern, text_lower):
                return False
        elif tag in text_lower:
            return False
    
    # Check for honorifics — strong indicator of personal name
    honorifics = {'mr', 'mrs', 'ms', 'dr', 'shri', 'smt', 'sri', 'kumari'}
    clean_words = []
    has_honorific = False
    for word in words:
        if word in honorifics:
            has_honorific = True
        else:
            clean_words.append(word)
    
    if has_honorific and clean_words:
        return True
    
    # Check if any word is a common Indian first name
    name_word_count = 0
    for word in clean_words:
        if word in COMMON_INDIAN_FIRST_NAMES:
            name_word_count += 1
    
    # If at least one word is a known name → personal name
    if name_word_count > 0:
        return True
    
    # ------------------------------------------------------------------
    # INDIAN NAME + INITIAL PATTERN (Layer 3: Dynamic Detection)
    # ------------------------------------------------------------------
    # Indian UPI payee names commonly appear as:
    #   "PACHIYAPPAN K"   → name + initial
    #   "MUTHUKRISHNAN P K" → name + two initials
    #   "C ANBU"          → initial + name
    #   "S SARAVANAKUMAR"  → initial + name
    #   "NIVRITH C M"     → name + initials
    #   "BETHUPANDI M"    → name + initial
    # Pattern: at least one long word (5+ chars) + rest are single-char initials
    # This is very common in South Indian names especially
    # ------------------------------------------------------------------
    if len(words) >= 2:
        all_alpha = all(word.isalpha() for word in words)
        if all_alpha:
            long_words = [w for w in words if len(w) >= 4]
            initials = [w for w in words if len(w) == 1]
            short_words = [w for w in words if 2 <= len(w) <= 3]
            
            # Pattern 1: "LONGNAME K" or "K LONGNAME" or "LONGNAME P K"
            # At least 1 long word + remaining are all initials
            if len(long_words) >= 1 and (len(long_words) + len(initials)) == len(words):
                return True

            # South Indian UPI names can include both a short name and an
            # initial, e.g. "ARIF ALI P".
            if (
                len(long_words) >= 1
                and len(short_words) >= 1
                and len(initials) >= 1
                and (len(long_words) + len(short_words) + len(initials)) == len(words)
            ):
                return True
            
            # Pattern 2: "LONGNAME SHORTNAME" — e.g., "MAHABOOB PASHA", "SHAIK ABDULLA"
            # 2-4 words, all alphabetic, all at least 2 chars
            if 2 <= len(words) <= 4 and all(len(w) >= 2 for w in words):
                return True
    
    # Single-word check: If it's a single long alphabetic word (5+ chars),
    # no digits, not a known merchant, not a context tag — this COULD be a name.
    # But we only allow this from UPI-extracted payee context (caller decides).
    # Here we remain conservative: single unknown words → NOT a name.
    
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
            if _merchant_matches(merchant, desc_lower):
                cat, subcat = self.merchant_lookup[merchant]
                return {
                    'category': cat,
                    'subcategory': subcat,
                    'confidence': 'high',
                    'reason': f'Merchant database: {merchant}'
                }
        
        return None

    def _categorize_education(self, description: str) -> Optional[Dict[str, Any]]:
        """Match education-specific terms before broad UPI merchant fallbacks."""
        education_category = self.categories.get('Education', {})
        for subcategory, subcategory_info in education_category.get('subcategories', {}).items():
            for keyword in subcategory_info.get('keywords', []):
                if _keyword_matches(keyword, description):
                    return {
                        'category': 'Education',
                        'subcategory': subcategory,
                        'confidence': 'high',
                        'reason': f'Education keyword match: {keyword}'
                    }

            for pattern in subcategory_info.get('patterns', []):
                if re.search(pattern, description, re.IGNORECASE):
                    return {
                        'category': 'Education',
                        'subcategory': subcategory,
                        'confidence': 'medium',
                        'reason': 'Education pattern match'
                    }

        return None
    
    def categorize(self, description: str, amount: float) -> Dict[str, Any]:
        """
        Categorize a transaction.
        
        Order of checks:
        1. User-defined exact matches (highest priority)
        2. User-defined keywords
        3. Income transactions (positive amounts)
        4. Merchant database lookup (GRT, Bhima, Apollo, etc.)
        5. Quick merchant lookup (Swiggy, Zomato, Apple Services, etc.)
        6. UPI context-tag detection (bakery, pharmacy, tours, etc.)
        7. UPI personal name → Individual Transfers
        8. NEFT/IMPS money transfer detection
        9. Category keyword/pattern matching
        
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
        
        # Bank IFSC codes (e.g. HDFC0MERUPI) must not trigger keyword matches
        desc_lower = _IFSC_RE.sub(' ', desc_lower)
        
        # Step 3: Handle income transactions
        if amount > 0:
            incoming_transfer = self._categorize_incoming_transfer(description, desc_lower)
            if incoming_transfer:
                return incoming_transfer
            return self._categorize_income(desc_lower)
        
        # Step 3.5: Bank-specific transaction code detection (Layer 2)
        # This handles HDFC-specific codes like SI, ATW, NWD, CBDT, etc.
        # These codes are NOT universal — they are bank-format-specific.
        bank_result = self._check_bank_specific_codes(desc_lower, desc_upper)
        if bank_result:
            return bank_result
        
        # Step 3.55: Slash-format UPI (UPI/P2A|P2M/<ref>/<NAME>/<remark>/<BANK>)
        slash_result = self._categorize_upi_slash(description)
        if slash_result:
            return slash_result
        
        # Step 3.56: ATM cash (ATM-CASH/<location>/<city>/<date>)
        if re.match(r'^(atm|cash)[-/\s]', desc_lower) and 'atm' in desc_lower[:5]:
            return {
                'category': 'Cash & ATM',
                'subcategory': 'ATM Withdrawal',
                'confidence': 'high',
                'reason': 'ATM cash withdrawal'
            }
        
        # Step 3.6: UPI with masked account numbers (XXXXXX) → Individual Transfers
        # Format: UPI-XXXXXX7198-UCBA0000001-403893950448-PAYMENT FROM PHONE
        if desc_upper.startswith('UPI') and 'XXXXXX' in desc_upper:
            return {
                'category': 'Individual Transfers',
                'subcategory': 'Personal Payment',
                'confidence': 'high',
                'reason': 'UPI to masked account number'
            }
        
        # Step 3.7: POS (Point of Sale) transactions — check context tags
        # Format: POS 416021XXXXXX0788 G R THANGAMALIGA
        if desc_upper.startswith('POS '):
            pos_desc = desc_lower[4:]  # Remove "POS " prefix
            # Also strip the card number prefix (e.g., "416021XXXXXX0788 ")
            pos_stripped = re.sub(r'^[\dX]+\s+', '', pos_desc)
            # Check context tags on the merchant name part
            context_result = _check_upi_context_tags(pos_stripped)
            if context_result:
                return context_result
            # Also check context tags on full POS description
            context_result = _check_upi_context_tags(pos_desc)
            if context_result:
                return context_result
        
        # Match UPI merchants against the payee, not bank/provider text in the
        # rest of the narration.
        upi_payee = _extract_upi_payee_name(description)
        merchant_text = upi_payee.lower() if upi_payee else desc_lower
        upi_vpa = _extract_upi_vpa_identifier(description)
        if upi_payee and upi_vpa:
            payee_lower = upi_payee.lower()
            vpa_lower = upi_vpa.lower()
            if 'bundl technologies' in payee_lower and 'swiggy' in vpa_lower:
                merchant_text += ' swiggyinstamart' if 'instamart' in vpa_lower else ' swiggy'
            elif not any(marker in vpa_lower for marker in ('payu', 'razorpay', '.rzp', 'payment', 'bank')):
                merchant_text += ' ' + vpa_lower

        education_result = self._categorize_education(merchant_text)
        if education_result:
            return education_result

        # Step 4: Check merchant database FIRST (this catches GRT, Bhima, Apollo, etc.)
        merchant_result = self._check_merchant_database(merchant_text)
        if merchant_result:
            return merchant_result
        
        # Step 5: Check quick lookup merchants (Apple Services, Google, etc.)
        for merchant, (cat, subcat) in self.known_merchants.items():
            if _merchant_matches(merchant, merchant_text):
                return {
                    'category': cat,
                    'subcategory': subcat,
                    'confidence': 'high',
                    'reason': f'Known merchant: {merchant}'
                }
        
        # Step 6: For UPI transactions, check context tags in the description
        # This catches "JAYARAM BAKERY" (bakery→Food), "ANAGHA TOURS" (tours→Travel),
        # "SHREE MARUTHI CHEMIST" (chemist→Healthcare), etc.
        context_result = _check_upi_context_tags(merchant_text)
        if context_result:
            return context_result
        
        # Step 7: Extract UPI payee name and check if it's a personal name
        # If it IS a personal name with no context tags → Individual Transfers
        if upi_payee:
            if _is_personal_name(upi_payee):
                return {
                    'category': 'Individual Transfers',
                    'subcategory': 'Personal Payment',
                    'confidence': 'medium',
                    'reason': f'UPI payment to individual: {upi_payee}'
                }
            # Layer 3 (Dynamic): Single-word UPI payee names
            # If extracted from UPI payee position and it's a single long
            # alphabetic word (5+ chars), no digits, not a known merchant —
            # this is very likely a personal name (e.g., LAXMI, UDHAYAKUMAR).
            # The _is_personal_name() function is conservative about single words,
            # but in UPI payee context we can be more confident.
            payee_lower = upi_payee.lower().strip()
            payee_words = payee_lower.split()
            if (len(payee_words) == 1 
                and payee_words[0].isalpha() 
                and len(payee_words[0]) >= 5
                and payee_lower not in KNOWN_MERCHANTS
                and not any(tag in payee_lower for tag in UPI_CONTEXT_TAGS if len(tag) > 3)):
                return {
                    'category': 'Individual Transfers',
                    'subcategory': 'Personal Payment',
                    'confidence': 'low',
                    'reason': f'UPI payment to likely individual: {upi_payee}'
                }
        
        # Step 8: Check if this is a NEFT/IMPS/RTGS money transfer
        if self._is_money_transfer(desc_lower, desc_upper):
            return self._categorize_transfer(desc_lower, desc_upper)
        
        # Also check non-UPI payee names for transfers
        general_payee = _extract_payee_name_general(description)
        if general_payee and _is_personal_name(general_payee):
            return self._categorize_transfer(desc_lower, desc_upper)
        
        # Step 9: Systematic category matching by priority
        result = self._categorize_expense(merchant_text, amount)
        if result['category'] == 'Other' and upi_payee:
            return self._categorize_unidentified_upi(desc_lower, upi_payee, result)
        return result
    
    def _categorize_unidentified_upi(self, desc_lower: str, payee: str,
                                     default: Dict[str, Any]) -> Dict[str, Any]:
        """Best-effort buckets for UPI payees that no keyword matched."""
        payee_lower = payee.lower()
        if payee_lower.startswith('payu'):
            if 'airtel' in desc_lower:
                return {'category': 'Telecom', 'subcategory': 'Mobile & Phone',
                        'confidence': 'low', 'reason': 'PayU gateway payment to Airtel'}
            return {'category': 'Shopping', 'subcategory': 'Online Shopping',
                    'confidence': 'low', 'reason': 'Payment gateway (PayU) online checkout'}
        # A payee with digits (e.g. "4PS 4", "1947") is a merchant account, not a person
        if any(ch.isdigit() for ch in payee):
            return {'category': 'Shopping', 'subcategory': 'Local Shops & Vendors',
                    'confidence': 'low', 'reason': f'UPI merchant account: {payee}'}
        return default
    
    def _categorize_upi_slash(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Handle slash-delimited UPI narrations used by Canara/Indian-style statements:
            UPI/P2A/645776967353/MAHESH V   /UPI/CANARA BANK
            UPI/P2M/645339091669/CORNER HOUSE ICE CREA/UPI/HDFC BANK LTD
        Only the payee and remark are inspected, never the bank name, so words
        in the bank name cannot trigger a false merchant match.
        P2A = person to account -> Individual Transfers
        P2M = person to merchant -> a purchase (Shopping / Local Shops & Vendors
              unless the name tells us more).
        """
        parts = [p.strip() for p in description.split('/')]
        if len(parts) < 4 or parts[0].upper() != 'UPI' or parts[1].upper() not in ('P2A', 'P2M', 'P2P'):
            return None
        
        kind = parts[1].upper()
        payee = parts[3]
        remark = parts[4] if len(parts) > 4 and parts[4].upper() != 'UPI' else ''
        text = f'{payee} {remark}'.lower().strip()

        education_result = self._categorize_education(text)
        if education_result:
            return education_result
        
        merchant_result = self._check_merchant_database(text)
        if merchant_result:
            return merchant_result
        for merchant, (cat, subcat) in self.known_merchants.items():
            if len(merchant) > 3 and merchant in text:
                return {'category': cat, 'subcategory': subcat, 'confidence': 'high',
                        'reason': f'Known merchant: {merchant}'}
        context_result = _check_upi_context_tags(text)
        if context_result:
            return context_result
        
        if kind == 'P2M':
            if payee.lower().startswith('web upi'):
                return {'category': 'Shopping', 'subcategory': 'Online Shopping',
                        'confidence': 'low', 'reason': 'UPI merchant (web checkout)'}
            return {'category': 'Shopping', 'subcategory': 'Local Shops & Vendors',
                    'confidence': 'low', 'reason': f'UPI merchant payment: {payee}'}
        return {'category': 'Individual Transfers', 'subcategory': 'Personal Payment',
                'confidence': 'medium', 'reason': f'UPI person-to-person: {payee}'}
    
    def _check_bank_specific_codes(self, desc_lower: str, desc_upper: str) -> Optional[Dict[str, Any]]:
        """
        Layer 2: Bank-specific transaction code detection.
        
        Different banks use different prefixes/codes for transaction types.
        This method currently handles HDFC Bank codes, but is designed to be
        extensible to other banks.
        
        HDFC Bank Codes:
          ATW-  : HDFC ATM withdrawal (own bank ATM)
          NWD-  : Non-HDFC ATM withdrawal (other bank ATM)
          SI    : Standing Instruction (auto-debit EMI, SIP, insurance, loan)
          CBDT  : Central Board of Direct Taxes (income tax payment)
          ACH   : Auto clearing house (recurring payments, mandates)
          POS   : Point-of-sale (card swipe) — partially universal
          REV-  : UPI reversal/refund
        
        SBI, ICICI, Axis would have their own codes — can be added later.
        """
        
        # ---- ATW: HDFC ATM Withdrawal ----
        # Format: ATW-416021XXXXXX0788-S1AWHS12-BANGALORE
        if desc_lower.startswith('atw-') or desc_lower.startswith('atw/'):
            return {
                'category': 'Cash & ATM',
                'subcategory': 'ATM Withdrawal',
                'confidence': 'high',
                'reason': 'HDFC ATM withdrawal (ATW code)'
            }
        
        # ---- NWD: Non-HDFC ATM cash withdrawal ----
        # Format: NWD-416021XXXXXX0788-01114625-BANGALORE
        if desc_lower.startswith('nwd-') or desc_lower.startswith('nwd/'):
            return {
                'category': 'Cash & ATM',
                'subcategory': 'ATM Withdrawal',
                'confidence': 'high',
                'reason': 'Non-HDFC ATM withdrawal (NWD code)'
            }
        
        # ---- EAW: card ATM cash withdrawal ----
        # Format: EAW-416021XXXXXX0788-DBL12076-KASAVANAHALL
        if desc_lower.startswith('eaw-') or desc_lower.startswith('eaw/'):
            return {
                'category': 'Cash & ATM',
                'subcategory': 'ATM Withdrawal',
                'confidence': 'high',
                'reason': 'ATM withdrawal (EAW code)'
            }
        
        # ---- Net-banking bill payment to a bank via PayU ----
        # Format: K4UHY5MLAN72HO6QD4/PAYUICICIBANK
        # PayU bill-pay to a bank is a credit-card (or loan) bill settlement.
        if _PAYU_BANK_BILL_RE.search(desc_lower):
            return {
                'category': 'Loans & EMI',
                'subcategory': 'Credit Card Payment',
                'confidence': 'medium',
                'reason': 'PayU bill payment to a bank (credit card bill)'
            }
        
        # ---- SI: Standing Instruction (EMI / SIP / Insurance / Loan repayment) ----
        # Format: SI HGAGP11BD70075488127 BANGALO-22/01/25
        # These are recurring auto-debits. Without more context, we categorize
        # as a recurring payment. The user can manually re-categorize if it's
        # specifically a home loan EMI vs car loan vs SIP.
        if desc_lower.startswith('si ') or desc_lower.startswith('si/'):
            return {
                'category': 'Recurring Commitments',
                'subcategory': 'Standing Instruction (EMI/SIP)',
                'confidence': 'medium',
                'reason': 'HDFC Standing Instruction — recurring auto-debit'
            }
        
        # ---- CBDT: Income Tax Payment ----
        # Format: CBDT/BANK REFERENCE NO:N2520936767265/CIN NO:...
        if 'cbdt' in desc_lower or 'income tax' in desc_lower:
            return {
                'category': 'Taxes & Government',
                'subcategory': 'Income Tax',
                'confidence': 'high',
                'reason': 'Income tax payment (CBDT)'
            }
        
        # ---- REV-UPI: UPI Reversal/Refund ----
        # Format: REV-UPI-...
        if desc_lower.startswith('rev-'):
            return {
                'category': 'Income',
                'subcategory': 'Refunds',
                'confidence': 'high',
                'reason': 'UPI reversal/refund'
            }
        
        return None
    
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
        
        # Reversals and credits from merchants/gateways are refunds, not earnings.
        # Credits from individuals were already routed to Individual Transfers.
        if description.startswith(('rev-', 'rev/')) or description.startswith('upi-'):
            return {
                'category': 'Income',
                'subcategory': 'Refunds',
                'confidence': 'medium',
                'reason': 'Reversal or credit from a merchant'
            }
        
        # ACH credits from a company are dividend / interest payouts
        if description.startswith('ach c-') or description.startswith('ach c '):
            return {
                'category': 'Income',
                'subcategory': 'Dividends',
                'confidence': 'medium',
                'reason': 'ACH credit from a company (dividend payout)'
            }
        
        return {
            'category': 'Income',
            'subcategory': 'Other Income',
            'confidence': 'low',
            'reason': 'Default income category'
        }

    def _categorize_incoming_transfer(
        self,
        description: str,
        desc_lower: str
    ) -> Optional[Dict[str, Any]]:
        """Keep received transfers and investment proceeds out of earned income."""
        desc_upper = description.upper().strip()
        if any(term in desc_lower for term in ('refund', 'reversal', 'cashback', 'salary', 'payroll', 'wages')):
            return None

        merchant_result = self._check_merchant_database(desc_lower)
        if merchant_result and get_category_group(merchant_result['category']) == 'Investment':
            # Broker / mutual-fund payouts are money received (gains and withdrawals),
            # so they count as income. Deposit maturities (FD, PPF, gold) stay in
            # Investments because they mostly return the principal.
            if merchant_result['subcategory'] in ('Stocks & Trading', 'Mutual Funds & SIP'):
                return {
                    'category': 'Income',
                    'subcategory': 'Investment Returns',
                    'confidence': merchant_result.get('confidence', 'high'),
                    'reason': f"Payout received from {merchant_result['subcategory'].lower()} provider"
                }
            return merchant_result

        if desc_upper.startswith('UPI/'):
            slash_result = self._categorize_upi_slash(description)
            if slash_result and get_category_group(slash_result['category']) == 'Transfer':
                return slash_result

        if desc_upper.startswith('UPI-'):
            payee = _extract_upi_payee_name(description)
            if payee and _is_personal_name(payee):
                return {
                    'category': 'Individual Transfers',
                    'subcategory': 'Personal Payment',
                    'confidence': 'medium',
                    'reason': f'Received UPI transfer from individual: {payee}'
                }

        if desc_upper.startswith(('IMPS-', 'IMPS/', 'NEFT CR-', 'NEFT CR/')):
            parts = re.split(r'[-/]', desc_upper)
            sender_index = 2
            if len(parts) > sender_index and _is_personal_name(parts[sender_index]):
                return {
                    'category': 'Individual Transfers',
                    'subcategory': 'IMPS Transfer' if desc_upper.startswith('IMPS') else 'NEFT Transfer',
                    'confidence': 'medium',
                    'reason': f'Received bank transfer from individual: {parts[sender_index]}'
                }

            if re.search(r'X{3,}\d{4,}', desc_upper):
                return {
                    'category': 'Individual Transfers',
                    'subcategory': 'IMPS Transfer' if desc_upper.startswith('IMPS') else 'NEFT Transfer',
                    'confidence': 'medium',
                    'reason': 'Received transfer to a masked account'
                }

        return None
    
    
    def _is_money_transfer(self, desc_lower: str, desc_upper: str) -> bool:
        """
        Determine if a transaction is a money transfer (not a purchase).
        
        Key indicators of money transfer:
        - Contains NEFT/IMPS/RTGS 
        - NOT to a known merchant from database
        - Personal name pattern detected
        """
        transfer_keywords = ['neft', 'imps', 'rtgs', 'fund transfer', 'net banking', 'inb/ift']
        
        if not any(kw in desc_lower for kw in transfer_keywords):
            return False
        
        # Check if it's to a known merchant (from database or quick lookup)
        if self._check_merchant_database(desc_lower):
            return False
        
        for merchant in self.known_merchants.keys():
            if _merchant_matches(merchant, desc_lower):
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
            'category': 'Individual Transfers',
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
            if cat_name in ['Income', 'Money Transfer', 'Individual Transfers', 'Other']:
                continue
            
            for subcat_name, subcat_info in cat_info.get('subcategories', {}).items():
                # Check keywords
                for keyword in subcat_info.get('keywords', []):
                    if _keyword_matches(keyword, description):
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
                'category': 'Cash & ATM',
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
                # Extract the payee name as keyword (much better than longest word)
                # Try UPI payee extraction first
                payee = _extract_upi_payee_name(description)
                if not payee:
                    payee = _extract_payee_name_general(description)
                
                if payee:
                    keyword = payee.lower().strip()
                else:
                    # Fallback: pick meaningful words, skip UPI junk
                    words = desc_lower.split('-')
                    # For UPI, the payee is at index 1
                    if len(words) > 1 and words[0].strip().startswith('upi'):
                        keyword = words[1].strip()
                    else:
                        # Filter out words that look like reference numbers/codes
                        meaningful = [w for w in desc_lower.split() 
                                     if w.isalpha() and len(w) >= 3
                                     and w not in ('upi', 'neft', 'imps', 'rtgs', 'payment', 'from', 'phone', 'sent', 'using', 'paytm')]
                        keyword = meaningful[0] if meaningful else desc_lower
                
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

# Singleton instance for performance (avoids re-reading user_mappings.json per call)
_CATEGORIZER_INSTANCE: Optional[RefinedCategorizer] = None

def _get_categorizer() -> RefinedCategorizer:
    """Get or create the singleton categorizer instance."""
    global _CATEGORIZER_INSTANCE
    if _CATEGORIZER_INSTANCE is None:
        _CATEGORIZER_INSTANCE = RefinedCategorizer()
    return _CATEGORIZER_INSTANCE


def categorize_transaction(description: str, amount: float) -> Dict[str, str]:
    """
    Quick categorization function for backward compatibility.
    Uses singleton instance to avoid repeated file reads.
    """
    categorizer = _get_categorizer()
    result = categorizer.categorize(description, amount)
    return {
        'category': result['category'],
        'subcategory': result['subcategory']
    }


def get_all_categories() -> Dict[str, List[str]]:
    """Get all available categories."""
    categorizer = _get_categorizer()
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
    'get_category_icons',
    'get_category_group',
    'CATEGORY_GROUPS'
]
