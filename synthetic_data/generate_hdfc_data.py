"""
HDFC Bank Statement Synthetic Data Generator
Generates realistic-looking bank statement data in HDFC CSV format for testing.
"""

import random
import csv
from datetime import datetime, timedelta
from pathlib import Path
import argparse


# ============================================================================
# CONFIGURATION - Merchant and Transaction Templates
# ============================================================================

# UPI Merchants with realistic patterns
UPI_MERCHANTS = {
    "groceries": [
        ("BIGBASKET", "BIGBASKET1@PAYTM", "PYTM0123456", "NA"),
        ("DMART READY", "DMARTREADY@YBL", "YESB0YBLUPI", "PAYMENT FOR ORDER"),
        ("ZEPTO", "ZEPTO@ICICI", "ICIC0DC0099", "GROCERIES"),
        ("BLINKIT", "BLINKIT@PAYTM", "PYTM0123456", "GROCERY ORDER"),
        ("MORE RETAIL", "MORERETAIL@YBL", "YESB0YBLUPI", "NA"),
    ],
    "food_delivery": [
        ("SWIGGY", "SWIGGY.RZP@HDFCBANK", "HDFC0000053", "PAYVIARAZORPAY"),
        ("ZOMATO", "ZOMATO@ICICI", "ICIC0DC0099", "FOOD ORDER"),
        ("SWIGGY", "SWIGGYSTORES@ICICI", "ICIC0DC0099", "NA"),
        ("UBER EATS", "UBEREATS@YBL", "YESB0YBLUPI", "FOOD DELIVERY"),
    ],
    "utilities": [
        ("BESCOM ELECTRICITY B", "PAYTM-PTMBBP@PAYTM", "PYTM0123456", "OID{oid}@PAY"),
        ("BWSSB WATER BILL", "PAYTM-PTMBBP@PAYTM", "PYTM0123456", "OID{oid}@PAY"),
        ("BANGALORE ONE", "BANGALOREONE@YBL", "YESB0YBLUPI", "UTILITY PAYMENT"),
        ("PIPED GAS BILL", "IOCL@PAYTM", "PYTM0123456", "GAS BILL PAYMENT"),
    ],
    "subscriptions": [
        ("NETFLIX COM", "NETFLIXUPI.PAYU@HDFCBANK", "HDFC0000499", "MONTHLY AUTOPAY. C"),
        ("AMAZON PRIME", "AMAZONPRIME@YAPL", "YESB0APLUPI", "PRIME SUBSCRIPTION"),
        ("SPOTIFY INDIA", "SPOTIFY@ICICI", "ICIC0DC0099", "MONTHLY SUBSCRIPTION"),
        ("HOTSTAR", "HOTSTAR@PAYTM", "PYTM0123456", "STREAMING SUBSCRIPTION"),
        ("YOUTUBE PREMIUM", "GOOGLE@ICICI", "ICIC0DC0099", "YOUTUBE PREMIUM"),
        ("APPLE SERVICES", "APPLESERVICES.BDSI@ICICI", "ICIC0DC0099", "MANDATEREQUEST"),
    ],
    "telecom": [
        ("AIRTEL MOBILE BILL", "8744070@PAYTM", "PYTM0123456", "OID{oid}@PAY"),
        ("JIO RECHARGE", "JIORECHARGE@YBL", "YESB0YBLUPI", "MOBILE RECHARGE"),
        ("VI MOBILE", "VIRECHARGE@PAYTM", "PYTM0123456", "PREPAID RECHARGE"),
        ("HATHWAY LANDLINE BIL", "8744070@PAYTM", "PYTM0123456", "OID{oid}@PAY"),
        ("ACT FIBERNET", "ACTFIBERNET@ICICI", "ICIC0DC0099", "INTERNET BILL"),
    ],
    "shopping": [
        ("AMAZON PAY", "AMAZONPAYHFC@YAPL", "YESB0APLUPI", "YOU ARE PAYING FOR"),
        ("AMAZON INDIA", "AMAZON@YAPL", "YESB0APLUPI", "YOU ARE PAYING FOR"),
        ("FLIPKART", "FLIPKART@YBL", "YESB0YBLUPI", "PAYMENT FOR ORDER"),
        ("MYNTRA", "MYNTRA@ICICI", "ICIC0DC0099", "FASHION ORDER"),
        ("AJIO", "AJIO@PAYTM", "PYTM0123456", "CLOTHING ORDER"),
        ("DECATHLON", "DECATHLON@YBL", "YESB0YBLUPI", "SPORTS GOODS"),
    ],
    "fuel": [
        ("HP PETROL PUMP", "HPPETROL@YBL", "YESB0YBLUPI", "FUEL PURCHASE"),
        ("INDIAN OIL", "IOCL@PAYTM", "PYTM0123456", "PETROL"),
        ("BHARAT PETROLEUM", "BPCL@ICICI", "ICIC0DC0099", "FUEL"),
    ],
    "medical": [
        ("APOLLO PHARMACY", "APOLLOPHARMACY@YBL", "YESB0YBLUPI", "MEDICINES"),
        ("MEDPLUS", "MEDPLUS@PAYTM", "PYTM0123456", "PHARMACY"),
        ("NETMEDS", "NETMEDS@ICICI", "ICIC0DC0099", "ONLINE PHARMACY"),
        ("PRACTO", "PRACTO@YBL", "YESB0YBLUPI", "CONSULTATION"),
    ],
    "transport": [
        ("OLA CABS", "OLA@ICICI", "ICIC0DC0099", "CAB RIDE"),
        ("UBER INDIA", "UBER@YBL", "YESB0YBLUPI", "RIDE PAYMENT"),
        ("RAPIDO", "RAPIDO@PAYTM", "PYTM0123456", "BIKE TAXI"),
        ("METRO RECHARGE", "BMRCL@YBL", "YESB0YBLUPI", "METRO CARD"),
    ],
    "investments": [
        ("ZERODHA BROKING LIMI", "ZERODHA.BROKING@ICICI", "ICIC0DC0099", "{ref} Z"),
        ("GROWW", "GROWW@ICICI", "ICIC0DC0099", "INVESTMENT"),
        ("COIN BY ZERODHA", "ZERODHA@ICICI", "ICIC0DC0099", "MF INVESTMENT"),
    ],
    "restaurants": [
        ("ADYAR ANANDA BHAVAN", "A2BKARNATAKA@YBL", "YESB0YBLUPI", "PAYMENT FOR {ref}"),
        ("CAFE COFFEE DAY", "CCD@PAYTM", "PYTM0123456", "COFFEE"),
        ("STARBUCKS", "STARBUCKS@YBL", "YESB0YBLUPI", "COFFEE"),
        ("DOMINOS PIZZA", "DOMINOS@ICICI", "ICIC0DC0099", "PIZZA ORDER"),
        ("MCDONALD", "MCDONALDS@YBL", "YESB0YBLUPI", "FOOD"),
    ],
    "personal": [
        ("DHIRENDRA KUMAR  MAJ", "9902770108@YBL", "SBIN0017785", "PAYMENT FROM PHONE"),
        ("JAYA", "Q429632518@YBL", "YESB0YBLUPI", "NA"),
        ("VARADARAJU", "Q331066230@YBL", "YESB0YBLUPI", "NA"),
        ("ANIL KUMAR", "7026692616@IBL", "SBIN0018295", "SENT FROM PAYTM"),
    ],
}

# NEFT Transactions
NEFT_TEMPLATES = {
    "salary": [
        ("NEFT CR-ICIC0SF0002-XFORMICS TECHNOLOGIE-BALASUBRAMANIAMVENKATANARAYANAN-{ref} SALARY FOR PAYROLL", "deposit"),
        ("NEFT CR-HDFC0001234-ACME CORP LTD-SALARY CREDIT-{ref}", "deposit"),
        ("NEFT CR-SBIN0001234-TECHSOLUTIONS PVT LTD-MONTHLY SALARY-{ref}", "deposit"),
    ],
    "transfer_out": [
        ("NEFT DR-UTIB0001688-BALASUBRAMANIAM VENKATANARAYANAN-SANDOZ - MUM-{ref}-NET BANKING SI -REGTRANSFER", "withdrawal"),
        ("NEFT DR-HDFC0001234-FAMILY TRANSFER-{ref}-IMPS TRANSFER", "withdrawal"),
    ],
    "transfer_in": [
        ("NEFT CR-CITI0000003-S RAMALAKSHMI-BALASUBRAMANIAM V-{ref}", "deposit"),
        ("NEFT CR-YESB0000001-ZERODHA BROKING LTD-DSCNB A/C-BALASUBRAMANIAM VENKATANARAYANAN-{ref}", "deposit"),
    ],
}

# Amount ranges for different categories
AMOUNT_RANGES = {
    "groceries": (200, 5000),
    "food_delivery": (150, 1500),
    "utilities": (50, 3000),
    "subscriptions": (99, 2000),
    "telecom": (199, 2000),
    "shopping": (200, 15000),
    "fuel": (500, 5000),
    "medical": (100, 5000),
    "transport": (50, 1500),
    "investments": (1000, 50000),
    "restaurants": (50, 2000),
    "personal": (100, 5000),
    "salary": (80000, 200000),
    "transfer_out": (5000, 50000),
    "transfer_in": (1000, 500000),
}


# ============================================================================
# DATA GENERATION FUNCTIONS
# ============================================================================

def generate_reference_number():
    """Generate a realistic reference number."""
    return f"{random.randint(100000000000, 999999999999)}"


def generate_oid():
    """Generate OID for payment references."""
    return f"{random.randint(20000000000, 29999999999)}"


def format_date(dt):
    """Format date as DD-MM-YYYY."""
    return dt.strftime("%d-%m-%Y")


def generate_upi_transaction(category, date, closing_balance):
    """Generate a UPI transaction."""
    merchant = random.choice(UPI_MERCHANTS[category])
    merchant_name, upi_id, ifsc, desc = merchant
    
    ref_num = generate_reference_number()
    oid = generate_oid()
    
    # Format description with placeholders
    desc = desc.replace("{oid}", oid).replace("{ref}", str(random.randint(1000000, 9999999)))
    
    narration = f"UPI-{merchant_name}-{upi_id}-{ifsc}-{ref_num}-{desc}"
    
    min_amt, max_amt = AMOUNT_RANGES[category]
    amount = round(random.uniform(min_amt, max_amt), 2)
    
    new_balance = round(closing_balance - amount, 2)
    
    return {
        "Date": format_date(date),
        "Narration": narration,
        "Chq./Ref.No.": f"{float(ref_num):.5E}",
        "Value Dt": format_date(date),
        "Withdrawal Amt.": amount,
        "Deposit Amt.": "",
        "Closing Balance": new_balance,
    }, new_balance


def generate_neft_transaction(category, date, closing_balance):
    """Generate a NEFT transaction."""
    template, tx_type = random.choice(NEFT_TEMPLATES[category])
    ref_num = f"{random.randint(10000000000, 99999999999)}DC"
    
    narration = template.replace("{ref}", ref_num)
    
    min_amt, max_amt = AMOUNT_RANGES[category]
    amount = round(random.uniform(min_amt, max_amt), 2)
    
    if tx_type == "deposit":
        new_balance = round(closing_balance + amount, 2)
        return {
            "Date": format_date(date),
            "Narration": narration,
            "Chq./Ref.No.": f"00{ref_num}",
            "Value Dt": format_date(date),
            "Withdrawal Amt.": "",
            "Deposit Amt.": amount,
            "Closing Balance": new_balance,
        }, new_balance
    else:
        new_balance = round(closing_balance - amount, 2)
        return {
            "Date": format_date(date),
            "Narration": narration,
            "Chq./Ref.No.": ref_num,
            "Value Dt": format_date(date),
            "Withdrawal Amt.": amount,
            "Deposit Amt.": "",
            "Closing Balance": new_balance,
        }, new_balance


def generate_si_transaction(date, closing_balance):
    """Generate a Standing Instruction transaction."""
    prev_date = date - timedelta(days=1)
    narration = f"SI HGACP07D9D{random.randint(1000000000, 9999999999)} BANGALO-{format_date(prev_date)}"
    amount = round(random.uniform(50, 500), 2)
    new_balance = round(closing_balance - amount, 2)
    
    return {
        "Date": format_date(date),
        "Narration": narration,
        "Chq./Ref.No.": "0",
        "Value Dt": format_date(date),
        "Withdrawal Amt.": amount,
        "Deposit Amt.": "",
        "Closing Balance": new_balance,
    }, new_balance


def generate_synthetic_data(
    start_date: datetime,
    end_date: datetime,
    initial_balance: float = 1000000,
    transactions_per_day: tuple = (1, 5),
    include_salary: bool = True,
    salary_day: int = 29,
):
    """
    Generate synthetic HDFC bank statement data.
    
    Args:
        start_date: Start date for transactions
        end_date: End date for transactions
        initial_balance: Starting account balance
        transactions_per_day: Min and max transactions per day
        include_salary: Whether to include monthly salary
        salary_day: Day of month for salary credit
    
    Returns:
        List of transaction dictionaries
    """
    transactions = []
    closing_balance = initial_balance
    current_date = start_date
    
    # Transaction category weights (probability distribution)
    upi_categories = [
        ("groceries", 0.15),
        ("food_delivery", 0.12),
        ("utilities", 0.05),
        ("subscriptions", 0.08),
        ("telecom", 0.05),
        ("shopping", 0.15),
        ("fuel", 0.05),
        ("medical", 0.05),
        ("transport", 0.10),
        ("investments", 0.05),
        ("restaurants", 0.10),
        ("personal", 0.05),
    ]
    
    categories = [c[0] for c in upi_categories]
    weights = [c[1] for c in upi_categories]
    
    while current_date <= end_date:
        day_transactions = []
        
        # Add salary on salary day
        if include_salary and current_date.day == salary_day:
            tx, closing_balance = generate_neft_transaction("salary", current_date, closing_balance)
            day_transactions.append(tx)
        
        # Random chance of NEFT transfer in
        if random.random() < 0.02:  # 2% chance per day
            tx, closing_balance = generate_neft_transaction("transfer_in", current_date, closing_balance)
            day_transactions.append(tx)
        
        # Random chance of NEFT transfer out
        if random.random() < 0.03:  # 3% chance per day
            tx, closing_balance = generate_neft_transaction("transfer_out", current_date, closing_balance)
            day_transactions.append(tx)
        
        # Random chance of Standing Instruction
        if random.random() < 0.05:  # 5% chance per day
            tx, closing_balance = generate_si_transaction(current_date, closing_balance)
            day_transactions.append(tx)
        
        # Generate random UPI transactions
        num_transactions = random.randint(*transactions_per_day)
        
        # Reduce transactions on weekends
        if current_date.weekday() >= 5:
            num_transactions = max(0, num_transactions - 2)
        
        for _ in range(num_transactions):
            category = random.choices(categories, weights=weights)[0]
            tx, closing_balance = generate_upi_transaction(category, current_date, closing_balance)
            day_transactions.append(tx)
        
        # Sort by time (randomize order within day)
        random.shuffle(day_transactions)
        transactions.extend(day_transactions)
        
        current_date += timedelta(days=1)
    
    return transactions


def save_to_csv(transactions, output_path):
    """Save transactions to CSV file in HDFC format."""
    fieldnames = [
        "Date", "Narration", "Chq./Ref.No.", "Value Dt",
        "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    
    print(f"✅ Generated {len(transactions)} transactions")
    print(f"📁 Saved to: {output_path}")


# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================

def generate_preset_files():
    """Generate multiple preset synthetic data files."""
    
    # Get the inputs folder path
    script_dir = Path(__file__).parent
    inputs_dir = script_dir.parent / "inputs"
    inputs_dir.mkdir(exist_ok=True)
    
    presets = [
        {
            "name": "synthetic_3months_heavy_spender",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 3, 31),
            "initial_balance": 500000,
            "transactions_per_day": (3, 8),
            "include_salary": True,
            "salary_day": 1,
        },
        {
            "name": "synthetic_6months_moderate",
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 6, 30),
            "initial_balance": 1500000,
            "transactions_per_day": (1, 4),
            "include_salary": True,
            "salary_day": 28,
        },
        {
            "name": "synthetic_1month_minimal",
            "start_date": datetime(2024, 11, 1),
            "end_date": datetime(2024, 11, 30),
            "initial_balance": 200000,
            "transactions_per_day": (0, 3),
            "include_salary": True,
            "salary_day": 25,
        },
    ]
    
    for preset in presets:
        name = preset.pop("name")
        print(f"\n🔄 Generating: {name}")
        
        transactions = generate_synthetic_data(**preset)
        output_path = inputs_dir / f"{name}.csv"
        save_to_csv(transactions, output_path)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic HDFC bank statement data"
    )
    parser.add_argument(
        "--presets",
        action="store_true",
        help="Generate preset synthetic data files"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--balance",
        type=float,
        default=1000000,
        help="Initial balance (default: 1000000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file name (saved in inputs folder)"
    )
    parser.add_argument(
        "--min-tx",
        type=int,
        default=1,
        help="Minimum transactions per day"
    )
    parser.add_argument(
        "--max-tx",
        type=int,
        default=5,
        help="Maximum transactions per day"
    )
    
    args = parser.parse_args()
    
    if args.presets:
        generate_preset_files()
    elif args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
        end = datetime.strptime(args.end_date, "%Y-%m-%d")
        
        transactions = generate_synthetic_data(
            start_date=start,
            end_date=end,
            initial_balance=args.balance,
            transactions_per_day=(args.min_tx, args.max_tx),
        )
        
        script_dir = Path(__file__).parent
        inputs_dir = script_dir.parent / "inputs"
        
        output_name = args.output or f"synthetic_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.csv"
        output_path = inputs_dir / output_name
        
        save_to_csv(transactions, output_path)
    else:
        # Default: generate presets
        print("No arguments provided. Generating preset files...")
        generate_preset_files()


if __name__ == "__main__":
    main()
