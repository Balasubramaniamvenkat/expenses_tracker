# Synthetic Data Generator

Generate realistic HDFC bank statement CSV files for testing the finance tracker.

## Quick Usage

Run these commands from the `synthetic_data` directory. Generated files are saved to the repository's `inputs` directory, which is Git-ignored.

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

The generator creates fictional transactions for:
- 🛒 Groceries (Superbasket, Freshmart, Quickmart, Valuemart)
- 🍔 Food Delivery (Quickbite, Foodrush, Tastybites)
- ⚡ Utilities (City Electricity, Metro Water, Gas Supply)
- 📺 Subscriptions (Streamflix, Primeview, Musicstream, Viewplus)
- 📱 Telecom (Telemax, Connectplus, Speednet)
- 🛍️ Shopping (Shopmart, Megamart, Fashionhub)
- ⛽ Fuel (City Fuel, Petro Point, Fuelmax)
- 💊 Medical (Wellness Pharmacy, Healthplus, Medico)
- 🚗 Transport (Citycab, Quickride, Bikezip, Metro Transit)
- 📈 Investments (XYZ Stock Brokers, Investwell, Wealthgrow)
- 🍽️ Restaurants (South Spice, Coffee Corner, Pizza Express)
- 💸 Salary & NEFT Transfers (ABC Technologies, XYZ Corp)

> **Note**: All merchant names, bank codes, and personal names are completely fictional.
