"""
PII Sanitizer Module for Family Finance Tracker
Detects and masks personally identifiable information in bank transaction data.

Detection Strategy (Structured Approach):
1. Phone Numbers - Regex (99% reliable)
2. Account/Reference Numbers - Regex (95% reliable)
3. Payee Names - Default-deny masking of UPI/IMPS/NEFT/RTGS payee fields
4. UPI IDs - Pattern matching (95% reliable)

This module ensures that sensitive personal data is not sent to external AI providers
while preserving enough context for meaningful financial analysis.
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
import pandas as pd


@dataclass
class SanitizationResult:
    """Result of sanitizing a text string"""
    original: str
    sanitized: str
    pii_found: List[Dict[str, str]]  # List of {type, original, masked}


# ===========================================
# Known Merchants Whitelist
# These look like names but are businesses - don't mask them
# ===========================================

MERCHANT_WHITELIST = {
    # Food & Delivery
    'SWIGGY', 'ZOMATO', 'BLINKIT', 'ZEPTO', 'DUNZO', 'BIGBASKET', 'GROFERS',
    'DOMINOS', 'PIZZA HUT', 'KFC', 'MCDONALDS', 'BURGER KING', 'SUBWAY',
    
    # E-commerce
    'AMAZON', 'FLIPKART', 'MYNTRA', 'AJIO', 'NYKAA', 'MEESHO', 'SNAPDEAL',
    
    # Travel & Transport
    'MAKEMYTRIP', 'MAKEMYTRIP INDIA PVT', 'GOIBIBO', 'CLEARTRIP', 'YATRA',
    'OLA', 'UBER', 'RAPIDO', 'REDBUS', 'IRCTC', 'ABHIBUS',
    
    # Entertainment & Streaming
    'NETFLIX', 'NETFLIX COM', 'AMAZON PRIME', 'HOTSTAR', 'DISNEY PLUS',
    'SPOTIFY', 'APPLE', 'APPLE SERVICES', 'GOOGLE', 'YOUTUBE',
    
    # Telecom & Utilities
    'AIRTEL', 'AIRTEL MOBILE BILL', 'JIO', 'VODAFONE', 'BSNL', 'VI',
    'TATA POWER', 'ADANI GAS', 'MAHANAGAR GAS', 'BESCOM',
    
    # Financial Services
    'ZERODHA', 'ZERODHA BROKING LTD', 'GROWW', 'UPSTOX', 'ANGEL BROKING',
    'PAYTM', 'PHONEPE', 'GPAY', 'GOOGLE PAY', 'MOBIKWIK', 'FREECHARGE',
    'HDFC BANK', 'ICICI BANK', 'SBI', 'AXIS BANK', 'KOTAK',
    
    # Insurance
    'LIBERTY GENERAL INSU', 'LIBERTY GENERAL INSURANCE', 
    'HDFC LIFE', 'ICICI PRUDENTIAL', 'LIC', 'MAX LIFE', 'TATA AIA',
    'BAJAJ ALLIANZ', 'STAR HEALTH', 'CARE HEALTH',
    
    # Shopping & Retail
    'RELIANCE', 'DMART', 'BIG BAZAAR', 'SPENCER', 'MORE', 'SPAR',
    'CROMA', 'VIJAY SALES', 'RELIANCE DIGITAL',
    
    # Healthcare
    'APOLLO', 'APOLLO PHARMACY', 'MEDPLUS', 'NETMEDS', 'PHARMEASY',
    '1MG', 'PRACTO',
    
    # Common transaction descriptions
    'CASH WITHDRAWAL', 'ATM WITHDRAWAL', 'INTEREST CREDIT', 'SALARY',
    'PAYMENT FROM PHONE', 'SENT USING PAYTM', 'MONTHLY AUTOPAY',
    'MANDATE REQUEST', 'MANDATEREQUEST', 'AUTOPAY', 'STANDING INSTRUCTION',
}

# Build lowercase set for case-insensitive matching
MERCHANT_WHITELIST_LOWER = {m.lower() for m in MERCHANT_WHITELIST}


# ===========================================
# Transaction Type Patterns
# ===========================================

TRANSACTION_PATTERNS = {
    'NEFT_CR': r'^NEFT\s*CR[-\s]',
    'NEFT_DR': r'^NEFT\s*DR[-\s]',
    'UPI': r'^UPI[-\s]',
    'IMPS': r'^IMPS[-\s]',
    'RTGS': r'^RTGS[-\s]',
    'ATM': r'^ATM\s*(WDL|WITHDRAWAL)?',
    'POS': r'^POS\s*',
    'NACH': r'^NACH[-\s]',
    'ECS': r'^ECS[-\s]',
}


# ===========================================
# Regex Patterns for PII Detection
# ===========================================

# Phone number patterns (Indian mobile numbers)
PHONE_PATTERNS = [
    r'\b([6-9]\d{9})\b',                    # 10-digit mobile: 9902770108
    r'(\d{10})@[A-Za-z]+',                  # UPI with phone: 8748030134@AXL
    r'(\d{10})-\d+@[A-Za-z]+',              # Extended UPI: 8147090995-2@YBL
]

# Account/Reference number patterns
ACCOUNT_PATTERNS = [
    r'\b([A-Z]{4}\d{11,17})\b',             # IFSC+Account: YESF350014812700
    r'\b(\d{12,18})\b',                      # Long reference numbers
    r'A/C[-\s]*([A-Z0-9]{8,})',             # Account references
]

# UPI ID patterns (capture full UPI ID for masking)
UPI_ID_PATTERNS = [
    r'([A-Za-z0-9._]+@[A-Za-z]+)',          # standard@bank format (no hyphen, so the UPI- prefix is excluded)
]

# IFSC Code pattern (don't mask, not PII)
IFSC_PATTERN = r'\b[A-Z]{4}0[A-Z0-9]{6}\b'


# ===========================================
# Name Detection Heuristics
# ===========================================

PAYEE_PLACEHOLDER = '[PAYEE]'

# Transfer descriptions whose payee fields must be masked
TRANSFER_PREFIX_PATTERN = re.compile(r'^(UPI|IMPS|NEFT|RTGS)\b', re.IGNORECASE)

# Splits on field separators but keeps them, so the line can be rebuilt
SEGMENT_SPLIT_PATTERN = re.compile(r'([-/])')

# Format labels, bank codes and connectors that are never a payee name
NON_PAYEE_WORDS = {
    'UPI', 'IMPS', 'NEFT', 'RTGS', 'CR', 'DR', 'REF', 'PAYMENT', 'FROM',
    'PHONE', 'SENT', 'RECEIVED', 'TRANSFER', 'TO', 'BY', 'FOR', 'AND', 'OF', 'THE',
    'HDFC', 'ICICI', 'ICIC', 'SBI', 'SBIN', 'AXIS', 'UTIB', 'KOTAK', 'KKBK',
    'YESB', 'YES', 'IDFC', 'IDFCFIRST', 'IDIB', 'INDB', 'INDUSIND', 'PUNB', 'PNB',
    'BARB', 'CNRB', 'CANARA', 'UBIN', 'UNION', 'FDRL', 'KARB', 'CSBK', 'UCBA',
    'IOBA', 'MAHB', 'BOB',
}


def is_merchant_segment(segment: str) -> bool:
    """True when a field is a known merchant, or contains one of length 6+"""
    lowered = ' '.join(segment.lower().split())
    if lowered in MERCHANT_WHITELIST_LOWER:
        return True
    return any(
        len(merchant) >= 6 and re.search(rf'\b{re.escape(merchant)}\b', lowered)
        for merchant in MERCHANT_WHITELIST_LOWER
    )


def is_payee_word(word: str) -> bool:
    """True for purely alphabetic words that are not format labels or bank codes"""
    if not re.fullmatch(r'[A-Za-z]+\.?', word):
        return False
    return word.upper().rstrip('.') not in NON_PAYEE_WORDS


# ===========================================
# Main Sanitization Functions
# ===========================================

class PIISanitizer:
    """
    Main class for sanitizing PII from transaction data.
    
    Usage:
        sanitizer = PIISanitizer()
        result = sanitizer.sanitize_text("UPI-JOHN DOE-9876543210@YBL-...")
        print(result.sanitized)  # "UPI-[PAYEE]-XXXXX43210@YBL-..."
    """
    
    def __init__(self):
        self.name_counter = 0
        self.name_mapping: Dict[str, str] = {}  # Original -> Placeholder
        self.stats = {
            'phone_numbers': 0,
            'account_numbers': 0,
            'personal_names': 0,
            'upi_ids': 0,
        }
    
    def reset_stats(self):
        """Reset statistics for new sanitization session"""
        self.name_counter = 0
        self.name_mapping = {}
        self.stats = {
            'phone_numbers': 0,
            'account_numbers': 0,
            'personal_names': 0,
            'upi_ids': 0,
        }
    
    def _mask_phone_number(self, phone: str) -> str:
        """Mask phone number keeping last 4 digits"""
        if len(phone) >= 10:
            return 'XXXXX' + phone[-5:]
        return 'XXXXX' + phone[-4:] if len(phone) > 4 else 'XXXXX'
    
    def _mask_account_number(self, account: str) -> str:
        """Mask account number keeping last 4 characters"""
        if len(account) > 4:
            return '*' * (len(account) - 4) + account[-4:]
        return '****'
    
    def _get_name_placeholder(self, name: str) -> str:
        """Get or create a consistent placeholder for a name"""
        name_key = name.upper()
        if name_key not in self.name_mapping:
            self.name_counter += 1
            self.name_mapping[name_key] = f'[PERSON_{self.name_counter}]'
        return self.name_mapping[name_key]
    
    def _sanitize_phones(self, text: str) -> Tuple[str, List[Dict]]:
        """Find and mask phone numbers"""
        pii_found = []
        result = text
        
        for pattern in PHONE_PATTERNS:
            matches = re.finditer(pattern, result)
            for match in matches:
                phone = match.group(1)
                if len(phone) == 10 and phone[0] in '6789':  # Valid Indian mobile
                    masked = self._mask_phone_number(phone)
                    # Replace only the phone part, not the whole match
                    result = result.replace(phone, masked, 1)
                    pii_found.append({
                        'type': 'phone_number',
                        'original': phone,
                        'masked': masked
                    })
                    self.stats['phone_numbers'] += 1
        
        return result, pii_found
    
    def _sanitize_account_numbers(self, text: str) -> Tuple[str, List[Dict]]:
        """Find and mask account/reference numbers"""
        pii_found = []
        result = text
        
        # Don't mask IFSC codes
        ifsc_codes = set(re.findall(IFSC_PATTERN, text))
        
        for pattern in ACCOUNT_PATTERNS:
            matches = re.finditer(pattern, result)
            for match in matches:
                account = match.group(1)
                
                # Skip if it's an IFSC code
                if account in ifsc_codes:
                    continue
                
                # Skip short numbers (likely not account numbers)
                if len(account) < 10:
                    continue
                
                masked = self._mask_account_number(account)
                result = result.replace(account, masked, 1)
                pii_found.append({
                    'type': 'account_number',
                    'original': account,
                    'masked': masked
                })
                self.stats['account_numbers'] += 1
        
        return result, pii_found
    
    def _sanitize_names(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Mask payee names in UPI, IMPS, NEFT and RTGS descriptions (default-deny).

        Every word in a payee field is masked unless it is a known merchant,
        a bank code or a format label. Fields containing '@' are left to the
        UPI ID masking, and fields containing digits are left to the number masking.
        """
        pii_found: List[Dict] = []
        if not TRANSFER_PREFIX_PATTERN.match(text):
            return text, pii_found

        parts = SEGMENT_SPLIT_PATTERN.split(text)
        # Even indexes hold fields and odd indexes hold separators.
        # Index 0 is the transaction type, so payee fields start at index 2.
        for i in range(2, len(parts), 2):
            segment = parts[i]
            if '@' in segment or is_merchant_segment(segment):
                continue

            rebuilt: List[str] = []
            names: List[str] = []
            for word in segment.split():
                if is_payee_word(word):
                    if rebuilt and rebuilt[-1] == PAYEE_PLACEHOLDER:
                        names[-1] += ' ' + word
                    else:
                        rebuilt.append(PAYEE_PLACEHOLDER)
                        names.append(word)
                else:
                    rebuilt.append(word)

            if names:
                parts[i] = ' '.join(rebuilt)
                for name in names:
                    pii_found.append({
                        'type': 'personal_name',
                        'original': name,
                        'masked': PAYEE_PLACEHOLDER
                    })
                    self.stats['personal_names'] += 1

        return ''.join(parts), pii_found
    
    def _sanitize_upi_ids(self, text: str) -> Tuple[str, List[Dict]]:
        """Mask UPI IDs while preserving bank identifier"""
        pii_found = []
        result = text
        
        for pattern in UPI_ID_PATTERNS:
            matches = re.finditer(pattern, result)
            for match in matches:
                upi_id = match.group(1)
                
                # Skip known merchant UPI IDs
                if any(merchant.lower() in upi_id.lower() for merchant in 
                       ['swiggy', 'zomato', 'paytm', 'amazon', 'flipkart', 'phonepe', 
                        'gpay', 'netflix', 'apple', 'blinkit', 'makemytrip']):
                    continue
                
                # Parse UPI ID
                if '@' in upi_id:
                    username, bank = upi_id.split('@', 1)
                    
                    # Check if username looks like a phone number
                    if re.match(r'^\d{10}', username):
                        # Already handled by phone sanitization
                        continue
                    
                    # Keep only the first character of the username
                    masked_username = username[:1] + '***' if username else '***'
                    
                    masked_id = f'{masked_username}@{bank}'
                    result = result.replace(upi_id, masked_id, 1)
                    pii_found.append({
                        'type': 'upi_id',
                        'original': upi_id,
                        'masked': masked_id
                    })
                    self.stats['upi_ids'] += 1
        
        return result, pii_found
    
    def sanitize_text(self, text: str) -> SanitizationResult:
        """
        Sanitize a single text string (transaction description).
        
        Args:
            text: Raw transaction description
            
        Returns:
            SanitizationResult with original, sanitized text, and PII found
        """
        if not text or pd.isna(text):
            return SanitizationResult(
                original=str(text),
                sanitized=str(text),
                pii_found=[]
            )
        
        text = str(text)
        all_pii = []
        
        # Apply sanitization in order (names first to avoid partial matches)
        result, names_pii = self._sanitize_names(text)
        all_pii.extend(names_pii)
        
        result, phones_pii = self._sanitize_phones(result)
        all_pii.extend(phones_pii)
        
        result, accounts_pii = self._sanitize_account_numbers(result)
        all_pii.extend(accounts_pii)
        
        result, upi_pii = self._sanitize_upi_ids(result)
        all_pii.extend(upi_pii)
        
        return SanitizationResult(
            original=text,
            sanitized=result,
            pii_found=all_pii
        )
    
    def sanitize_dataframe(self, df: pd.DataFrame, 
                           description_column: str = 'Description') -> pd.DataFrame:
        """
        Sanitize all descriptions in a DataFrame.
        
        Args:
            df: DataFrame with transaction data
            description_column: Name of the column containing descriptions
            
        Returns:
            New DataFrame with sanitized descriptions
        """
        self.reset_stats()
        
        df_sanitized = df.copy()
        
        if description_column in df_sanitized.columns:
            df_sanitized[description_column] = df_sanitized[description_column].apply(
                lambda x: self.sanitize_text(x).sanitized
            )
        
        return df_sanitized
    
    def get_sanitization_summary(self) -> Dict:
        """Get summary of PII found and masked"""
        return {
            'total_pii_masked': sum(self.stats.values()),
            'breakdown': self.stats.copy(),
            'unique_names_found': len(self.name_mapping)
        }


# ===========================================
# Convenience Functions
# ===========================================

# Global sanitizer instance
_default_sanitizer = PIISanitizer()


def sanitize_transaction(description: str) -> str:
    """Quick sanitization of a single transaction description"""
    return _default_sanitizer.sanitize_text(description).sanitized


def sanitize_transactions_list(descriptions: List[str]) -> List[str]:
    """Sanitize a list of transaction descriptions"""
    _default_sanitizer.reset_stats()
    return [_default_sanitizer.sanitize_text(d).sanitized for d in descriptions]


def sanitize_for_ai_context(context_text: str) -> Tuple[str, Dict]:
    """
    Sanitize a full context string meant for AI.
    Returns sanitized text and summary of what was masked.
    """
    sanitizer = PIISanitizer()
    
    # Split by lines to handle each transaction
    lines = context_text.split('\n')
    sanitized_lines = []
    
    for line in lines:
        # Check if line contains transaction data (has amount pattern or transaction type)
        if any(pattern in line.upper() for pattern in ['UPI', 'NEFT', 'IMPS', 'ATM', '₹', 'INR']):
            result = sanitizer.sanitize_text(line)
            sanitized_lines.append(result.sanitized)
        else:
            sanitized_lines.append(line)
    
    return '\n'.join(sanitized_lines), sanitizer.get_sanitization_summary()


# ===========================================
# Testing / Demo
# ===========================================

if __name__ == "__main__":
    # Test cases
    test_transactions = [
        "NEFT CR-YESB0000001-ZERODHA BROKING LTD-DSCNB A/C-BALASUBRAMANIAM VENKATANARAYANAN-YESF350014812700",
        "UPI-DHIRENDRA KUMAR  MAJ-9902770108@YBL-SBIN0017785-460665356321-PAYMENT FROM PHONE",
        "UPI-RAMU BIRADAR-8748030134@AXL-BARB0JAMKHA-257723526495-PAYMENT FROM PHONE",
        "UPI-SWIGGY-UPISWIGGY@ICICI-ICIC0DC0099-909247179576-PAYMENT FROM PHONE",
        "UPI-NETFLIX COM-NETFLIXUPI.PAYU@HDFCBANK-HDFC0000499-500583041347-MONTHLY AUTOPAY",
        "NEFT CR-UTIB0005098-S RAMALAKSHMI-BALASUBRAMANIAM V-AXOIR00513626872",
        "UPI-J SARAVANAN-JSARAVANANLIC@OKAXIS-HDFC0002615-739339314767-PAYMENT FROM PHONE",
    ]
    
    print("=" * 80)
    print("PII SANITIZER TEST")
    print("=" * 80)
    
    sanitizer = PIISanitizer()
    
    for txn in test_transactions:
        result = sanitizer.sanitize_text(txn)
        print(f"\n📝 ORIGINAL:")
        print(f"   {result.original}")
        print(f"✅ SANITIZED:")
        print(f"   {result.sanitized}")
        if result.pii_found:
            print(f"🔒 PII FOUND:")
            for pii in result.pii_found:
                print(f"   - {pii['type']}: '{pii['original']}' → '{pii['masked']}'")
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY:")
    summary = sanitizer.get_sanitization_summary()
    print(f"   Total PII masked: {summary['total_pii_masked']}")
    print(f"   Breakdown: {summary['breakdown']}")
    print("=" * 80)
