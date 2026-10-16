# Bank Statement Input Formats

The application accepts bank statements in **CSV (`.csv`), Excel 97-2003 (`.xls`), and Excel (`.xlsx`)** formats. Statements from different banks are mapped to a shared transaction format before they are merged.

CSV files should have their column headers in the first row. Excel workbooks may have bank details above the table; the application searches the first 50 rows of each sheet for the transaction header.

## Recognized Columns

Column names may vary by bank. The importer recognizes common alternatives:

| Standard field | Example source column names | Required |
|-------------|-------------|---------|
| Transaction date | `Date`, `Tran Date`, `Transaction Date`, `Value Date` | Yes |
| Description | `Narration`, `Particulars`, `Description`, `Transaction Details`, `Remarks` | Yes |
| Debit | `Withdrawal Amt.`, `Debit`, `DR` | At least one amount field |
| Credit | `Deposit Amt.`, `Credit`, `CR` | At least one amount field |
| Transaction amount | `Amount`, `Transaction Amount` | At least one amount field |
| Balance | `Closing Balance`, `Balance`, `BAL` | Optional |

Debit amounts are normalized as negative values and credits as positive values. A single amount column is kept signed unless a transaction type column identifies it as a debit or credit.

---

## 📄 Sample CSV Content

```csv
Date,Narration,Chq./Ref.No.,Value Dt,Withdrawal Amt.,Deposit Amt.,Closing Balance
01-01-2024,NEFT DR-UTIB0001688-JOHN DOE-TRANSFER,N001242809098988,01-01-2024,11000,,1010503.27
02-01-2024,UPI-SWIGGY-SWIGGY@YBL-YESB0YBLUPI-437276589036,437276589036,02-01-2024,849,,1009654.27
02-01-2024,NEFT CR-CITI0000003-EMPLOYER NAME-SALARY,CITIN24401114659,02-01-2024,,85000,1094654.27
03-01-2024,UPI-AMAZON PAY-AMAZONPAYHFC@YAPL-YESB0APLUPI,437276589037,03-01-2024,1500,,1093154.27
```

---

## 📅 Date Format

The application supports multiple date formats:

| Format | Example | Priority |
|--------|---------|----------|
| `DD-MM-YYYY` | `01-01-2024` | ✅ Preferred |
| `DD/MM/YYYY` | `01/01/2024` | Supported |
| `YYYY-MM-DD` | `2024-01-01` | Supported |
| `DD-MM-YY` | `01-01-24` | Supported |

**Recommended:** Use `DD-MM-YYYY` format (e.g., `25-12-2024`)

---

## 💰 Amount Format

- Use **numbers only** (no currency symbols)
- Decimal separator: `.` (period)
- No thousand separators
- Leave empty if no amount (not `0`)

**Examples:**
- ✅ `1500.50`
- ✅ `25000`
- ✅ `` (empty for no transaction)
- ❌ `₹1,500.50`
- ❌ `1,500.50`

---

## 📝 Transaction Narration

The narration field is used for automatic categorization. The system recognizes:

### UPI Transactions
```
UPI-MERCHANT_NAME-VPA@BANK-BANK_CODE-REFERENCE-DESCRIPTION
```
**Example:** `UPI-SWIGGY-SWIGGY.RZP@HDFCBANK-HDFC0000053-437276589036-PAYVIARAZORPAY`

### NEFT/IMPS Transactions
```
NEFT DR-BANK_CODE-RECIPIENT_NAME-PURPOSE-REFERENCE
NEFT CR-BANK_CODE-SENDER_NAME-PURPOSE-REFERENCE
```
**Example:** `NEFT CR-CITI0000003-EMPLOYER LTD-SALARY-CITIN24401114659`

### ATM Transactions
```
ATM-BANK_NAME-LOCATION-REFERENCE
```
**Example:** `ATM-HDFC-BANGALORE-437276589036`

---

## 🏷️ Auto-Categorization Keywords

The system automatically categorizes based on these keywords:

| Category | Keywords Detected |
|----------|-------------------|
| Food & Dining | swiggy, zomato, restaurant, cafe, bigbasket |
| Shopping | amazon, flipkart, myntra, shopping |
| Utilities | electricity, bescom, water, gas |
| Telecom | airtel, jio, vi, broadband, DTH |
| Transportation | uber, ola, metro, petrol, fuel |
| Travel | IRCTC, flights, hotel bookings, travel booking |
| Entertainment | netflix, spotify, prime, youtube |
| Healthcare | apollo, pharmacy, medical, hospital |
| Investments | zerodha, groww, mutual fund, stocks |
| Income | salary, neft cr, credit, refund |

Food merchants are split by service: BigBasket and Swiggy Instamart are groceries; regular Swiggy and Zomato orders are food delivery. Telecom providers (Airtel, Jio, Vodafone Idea/Vi, and BSNL) belong to Telecom, not groceries. Travel includes IRCTC rail bookings, flights, hotels/accommodation, and travel-booking services; local taxis, metro, and fuel remain Transportation.

---

## ⚠️ Common Issues

### Issue: "Unable to parse CSV"
- ✅ Ensure first row has column headers
- ✅ Check for special characters in file
- ✅ Save as UTF-8 encoding

### Issue: "Date parsing failed"
- ✅ Use `DD-MM-YYYY` format
- ✅ Ensure dates are valid (no 31-02-2024)

### Issue: "Amount not recognized"
- ✅ Remove currency symbols
- ✅ Remove thousand separators
- ✅ Use period (.) for decimals

---

## 🔄 How to Export from HDFC NetBanking

1. Login to HDFC NetBanking
2. Go to **Accounts** → **Account Statement**
3. Select date range
4. Choose **Download** → **CSV Format**
5. Save the file
6. Upload to Family Finance Tracker

---

## 🧪 Generate Test Data

Don't have a bank statement? Generate test data:

```bash
cd synthetic_data
python generate_hdfc_data.py --presets
```

Run this from the repository root. It creates fictional sample files in the Git-ignored `inputs/` folder:
- `synthetic_1month_minimal.csv` - Basic test data
- `synthetic_3months_heavy_spender.csv` - More transactions
- `synthetic_6months_moderate.csv` - Long-term data

---

## 📤 Uploading Your File

1. Go to http://localhost:4200/upload
2. Drag & drop your CSV file
3. Or click to browse and select
4. Wait for processing
5. View results in Dashboard

---

**Need help?** Check the [QUICKSTART.md](QUICKSTART.md) guide.
