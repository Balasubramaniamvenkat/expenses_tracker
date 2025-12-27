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

# UPI Merchants with fictional names (no real company references)
UPI_MERCHANTS = {
    "groceries": [
        ("SUPERBASKET GROCERY", "SUPERBASKET@PAYTM", "PYTM0123456", "NA"),
        ("FRESHMART READY", "FRESHMART@ALPHABNK", "ALPHA0001234", "PAYMENT FOR ORDER"),
        ("QUICKMART", "QUICKMART@BETABNK", "BETA0DC0099", "GROCERIES"),
        ("INSTAMART GROCERY", "INSTAMART@PAYTM", "PYTM0123456", "GROCERY ORDER"),
        ("VALUEMART STORE", "VALUEMART@ALPHABNK", "ALPHA0001234", "NA"),
    ],
    "food_delivery": [
        ("QUICKBITE DELIVERY", "QUICKBITE@GAMMABNK", "GAMMA0000053", "FOOD DELIVERY"),
        ("FOODRUSH", "FOODRUSH@BETABNK", "BETA0DC0099", "FOOD ORDER"),
        ("TASTYBITES", "TASTYBITES@BETABNK", "BETA0DC0099", "NA"),
        ("MEALEXPRESS", "MEALEXPRESS@ALPHABNK", "ALPHA0001234", "FOOD DELIVERY"),
    ],
    "utilities": [
        ("CITY ELECTRICITY BD", "PAYTM-ELECBILL@PAYTM", "PYTM0123456", "OID{oid}@PAY"),
        ("METRO WATER BOARD", "PAYTM-WATERBILL@PAYTM", "PYTM0123456", "OID{oid}@PAY"),
        ("CITYPAY SERVICES", "CITYPAY@ALPHABNK", "ALPHA0001234", "UTILITY PAYMENT"),
        ("GAS SUPPLY CORP", "GASCORP@PAYTM", "PYTM0123456", "GAS BILL PAYMENT"),
    ],
    "subscriptions": [
        ("STREAMFLIX", "STREAMFLIX@GAMMABNK", "GAMMA0000499", "MONTHLY AUTOPAY"),
        ("PRIMEVIEW", "PRIMEVIEW@GAMMABNK", "GAMMA0APLUPI", "SUBSCRIPTION"),
        ("MUSICSTREAM", "MUSICSTREAM@BETABNK", "BETA0DC0099", "MONTHLY SUBSCRIPTION"),
        ("VIEWPLUS OTT", "VIEWPLUS@PAYTM", "PYTM0123456", "STREAMING SUBSCRIPTION"),
        ("VIDEOPRO PREMIUM", "VIDEOPRO@BETABNK", "BETA0DC0099", "PREMIUM SUBSCRIPTION"),
        ("CLOUDMUSIC", "CLOUDMUSIC@BETABNK", "BETA0DC0099", "SUBSCRIPTION"),
    ],
    "telecom": [
        ("TELEMAX MOBILE", "8744070@PAYTM", "PYTM0123456", "OID{oid}@PAY"),
        ("CONNECTPLUS", "CONNECTPLUS@ALPHABNK", "ALPHA0001234", "MOBILE RECHARGE"),
        ("CALLNET MOBILE", "CALLNET@PAYTM", "PYTM0123456", "PREPAID RECHARGE"),
        ("HOMELINK BROADBAND", "8744070@PAYTM", "PYTM0123456", "OID{oid}@PAY"),
        ("SPEEDNET FIBERNET", "SPEEDNET@BETABNK", "BETA0DC0099", "INTERNET BILL"),
    ],
    "shopping": [
        ("SHOPMART ONLINE", "SHOPMART@GAMMABNK", "GAMMA0APLUPI", "YOU ARE PAYING FOR"),
        ("MEGAMART ONLINE", "MEGAMART@GAMMABNK", "GAMMA0APLUPI", "YOU ARE PAYING FOR"),
        ("QUICKSHOP", "QUICKSHOP@ALPHABNK", "ALPHA0001234", "PAYMENT FOR ORDER"),
        ("FASHIONHUB", "FASHIONHUB@BETABNK", "BETA0DC0099", "FASHION ORDER"),
        ("STYLEMART", "STYLEMART@PAYTM", "PYTM0123456", "CLOTHING ORDER"),
        ("SPORTZONE STORE", "SPORTZONE@ALPHABNK", "ALPHA0001234", "SPORTS GOODS"),
    ],
    "fuel": [
        ("CITY FUEL STATION", "CITYFUEL@ALPHABNK", "ALPHA0001234", "FUEL PURCHASE"),
        ("PETRO POINT", "PETROPOINT@PAYTM", "PYTM0123456", "PETROL"),
        ("FUELMAX PUMPS", "FUELMAX@BETABNK", "BETA0DC0099", "FUEL"),
    ],
    "medical": [
        ("WELLNESS PHARMACY", "WELLNESSPHARM@ALPHABNK", "ALPHA0001234", "MEDICINES"),
        ("HEALTHPLUS CHEMIST", "HEALTHPLUS@PAYTM", "PYTM0123456", "PHARMACY"),
        ("MEDICO ONLINE", "MEDICOONLINE@BETABNK", "BETA0DC0099", "ONLINE PHARMACY"),
        ("DOCCARE CONSULT", "DOCCARE@ALPHABNK", "ALPHA0001234", "CONSULTATION"),
    ],
    "transport": [
        ("CITYCAB RIDES", "CITYCAB@BETABNK", "BETA0DC0099", "CAB RIDE"),
        ("QUICKRIDE CABS", "QUICKRIDE@ALPHABNK", "ALPHA0001234", "RIDE PAYMENT"),
        ("BIKEZIP", "BIKEZIP@PAYTM", "PYTM0123456", "BIKE TAXI"),
        ("METRO TRANSIT", "METROTRANSIT@ALPHABNK", "ALPHA0001234", "METRO CARD"),
    ],
    "investments": [
        ("XYZ STOCK BROKERS", "XYZBROKING@BETABNK", "BETA0DC0099", "{ref} X"),
        ("INVESTWELL APP", "INVESTWELL@BETABNK", "BETA0DC0099", "INVESTMENT"),
        ("WEALTHGROW MF", "WEALTHGROW@BETABNK", "BETA0DC0099", "MF INVESTMENT"),
    ],
    "restaurants": [
        ("SOUTH SPICE REST", "SOUTHSPICE@ALPHABNK", "ALPHA0001234", "PAYMENT FOR {ref}"),
        ("COFFEE CORNER", "COFFEECORNER@PAYTM", "PYTM0123456", "COFFEE"),
        ("BREW HOUSE", "BREWHOUSE@ALPHABNK", "ALPHA0001234", "COFFEE"),
        ("PIZZA EXPRESS", "PIZZAEXPRESS@BETABNK", "BETA0DC0099", "PIZZA ORDER"),
        ("BURGER PALACE", "BURGERPALACE@ALPHABNK", "ALPHA0001234", "FOOD"),
    ],
    "personal": [
        ("RAJESH KUMAR", "9902770108@ALPHABNK", "DELTA0017785", "PAYMENT FROM PHONE"),
        ("PRIYA SHARMA", "Q429632518@ALPHABNK", "ALPHA0001234", "NA"),
        ("AMIT SINGH", "Q331066230@ALPHABNK", "ALPHA0001234", "NA"),
        ("SURESH VERMA", "7026692616@DELTABNK", "DELTA0018295", "PAYMENT"),
    ],
}

# NEFT Transactions (fictional names)
NEFT_TEMPLATES = {
    "salary": [
        ("NEFT CR-EPSI0SF0002-ABC TECHNOLOGIES PVT LTD-JOHN DOE-{ref} SALARY FOR PAYROLL", "deposit"),
        ("NEFT CR-GAMMA0001234-XYZ CORP LTD-SALARY CREDIT-{ref}", "deposit"),
        ("NEFT CR-DELTA0001234-TECHWAVE SOLUTIONS PVT LTD-MONTHLY SALARY-{ref}", "deposit"),
    ],
    "transfer_out": [
        ("NEFT DR-ZETA0001688-JOHN DOE-FAMILY SUPPORT-{ref}-NET BANKING SI -REGTRANSFER", "withdrawal"),
        ("NEFT DR-GAMMA0001234-FAMILY TRANSFER-{ref}-IMPS TRANSFER", "withdrawal"),
    ],
    "transfer_in": [
        ("NEFT CR-OMEGA0000003-JANE DOE-JOHN DOE-{ref}", "deposit"),
        ("NEFT CR-ZETA0000001-XYZ STOCK BROKERS LTD-DSCNB A/C-JOHN DOE-{ref}", "deposit"),
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
    narration = f"SI HGACP07D9D{random.randint(1000000000, 9999999999)} METROCITY-{format_date(prev_date)}"
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
