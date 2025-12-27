# Synthetic Data Generator

Generate realistic HDFC bank statement CSV files for testing the finance tracker.

## Quick Usage

### Generate Preset Files
```bash
python generate_hdfc_data.py --presets
```

This creates 3 test files in the `inputs` folder:
- `synthetic_3months_heavy_spender.csv` - 3 months, high spending
- `synthetic_6months_moderate.csv` - 6 months, moderate spending  
- `synthetic_1month_minimal.csv` - 1 month, minimal transactions

### Custom Generation
```bash
python generate_hdfc_data.py --start-date 2024-01-01 --end-date 2024-12-31 --balance 500000 --output my_test_data.csv
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--presets` | Generate preset files | - |
| `--start-date` | Start date (YYYY-MM-DD) | Required |
| `--end-date` | End date (YYYY-MM-DD) | Required |
| `--balance` | Initial account balance | 1000000 |
| `--output` | Output filename | Auto-generated |
| `--min-tx` | Min transactions/day | 1 |
| `--max-tx` | Max transactions/day | 5 |

## Transaction Categories

The generator includes realistic transactions for:
- 🛒 Groceries (BigBasket, DMart, Zepto, Blinkit)
- 🍔 Food Delivery (Swiggy, Zomato)
- ⚡ Utilities (BESCOM, BWSSB, Gas)
- 📺 Subscriptions (Netflix, Spotify, Apple, YouTube)
- 📱 Telecom (Airtel, Jio, ACT Fibernet)
- 🛍️ Shopping (Amazon, Flipkart, Myntra)
- ⛽ Fuel (HP, Indian Oil, BPCL)
- 💊 Medical (Apollo, MedPlus)
- 🚗 Transport (Ola, Uber, Metro)
- 📈 Investments (Zerodha, Groww)
- 🍽️ Restaurants (A2B, CCD, Starbucks)
- 💸 Salary & NEFT Transfers
