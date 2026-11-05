# Family Finance Tracker

A privacy-first personal finance management application designed to help families track, analyze, and manage their expenses with smart categorization and optional AI-powered insights. Built with Angular 19 and FastAPI, statement files and processed data are stored locally. If AI features are enabled, sanitized transaction context is sent to the selected AI provider.

## 📋 Overview

**Family Finance Tracker** helps you understand your spending patterns by analyzing bank statements. Upload CSV or Excel statements from supported banks, and the application will normalize and combine the selected batch for analysis. Each successful batch replaces the current processed dataset, so upload all statements you want included together:
- Automatically categorize transactions (Food, Shopping, Utilities, etc.)
- Provide visual analytics with charts and summaries
- Offer AI-powered insights and chat capabilities
- Render on-demand AI chat charts for spending by category or across day, week, and month periods
- Track income vs expenses over time

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📤 **Smart Upload** | Batch CSV/XLS/XLSX upload with transaction normalization and processed-dataset replacement |
| 🏷️ **Smart Categorization** | Merchant database + personal name detection for accurate categorization |
| 📊 **Drill-Down Dashboard** | Interactive charts with click-to-drill-down into subcategories and separate investment, planned-outflow, and transfer totals |
| 🧾 **Account Filters** | Filter dashboard analytics and transaction lists by account; account choices show only the last four digits where available |
| 🛒 **Indian Merchant Database** | 500+ pre-configured Indian merchants for accurate categorization |
| 🤖 **AI Chat** | Ask questions about your finances using multiple LLM providers |
| 🔒 **Privacy-First** | Statements are stored locally; AI context is sent to a provider only when AI features are used |
| 🛡️ **PII Protection** | Payee names, phone numbers, and account details are masked on a best-effort basis before AI processing |
| 📱 **Responsive UI** | Material Design that works on desktop and mobile |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                    Angular 19 + Material                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │  Dashboard  │ │ Transactions│ │  Categories │ │ AI Insights│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│                         │                                        │
│                    NgRx State Management                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP REST API
┌─────────────────────────┴───────────────────────────────────────┐
│                         BACKEND                                  │
│                    FastAPI (Python)                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │   Upload    │ │ Transactions│ │  Dashboard  │ │  AI Chat   │ │
│  │    API      │ │     API     │ │     API     │ │    API     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
│                         │                                        │
│              Data Processing (Pandas)                            │
│                         │                                        │
│              File Storage (CSV)                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.104.1 | REST API framework |
| Pandas | 2.1.3 | Data processing |
| Uvicorn | 0.24.0 | ASGI server |
| Pydantic | 2.5.0 | Data validation |
| LangChain | ≥0.1.0 | Multi-LLM integration |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Angular | 19.2.0 | Frontend framework |
| Angular Material | 19.2.0 | UI components |
| NgRx | 19.2.1 | State management |
| Chart.js | 4.3.0 | Data visualization |
| ngx-file-drop | 16.0.0 | File upload |

## 📁 Project Structure

```
simple_finance_tracker/
├── backend/
│   ├── api/                    # FastAPI endpoints
│   │   ├── main.py            # App entry point
│   │   ├── upload.py          # File upload handling
│   │   ├── transactions.py    # Transaction queries
│   │   ├── dashboard.py       # Analytics endpoints
│   │   ├── categories.py      # Category management
│   │   ├── categories_hierarchy.py  # Hierarchical category API
│   │   ├── account_filters.py # Shared analytics account filtering
│   │   └── ai_chat.py         # AI chat integration
│   ├── SRC/                    # Core processing modules
│   │   ├── data_extraction.py # CSV parsing
│   │   ├── categories.py      # Category manager
│   │   ├── refined_categories.py  # Smart categorization engine
│   │   ├── merchant_database.json # 500+ Indian merchants
│   │   ├── analysis.py        # Financial analytics
│   │   └── pii_sanitizer.py   # PII detection & masking
│   └── requirements.txt
├── frontend/app/
│   └── src/app/
│       ├── modules/
│       │   ├── upload/        # File upload module
│       │   ├── transactions/  # Transaction list
│       │   ├── categories/    # Category management
│       │   └── ai-insights/   # AI chat interface
│       ├── shared/
│       │   └── account-filter-options.ts # Shared masked account choices
│       └── pages/
│           └── dashboard/     # Enhanced drill-down dashboard
├── inputs/                     # Upload directory
└── synthetic_data/            # Test data generator
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload/batch` | POST | Upload a batch of bank statement files (CSV, XLS, XLSX) |
| `/api/upload/single` | POST | Upload one bank statement file |
| `/api/transactions/` | GET | List transactions with filters, including account selection |
| `/api/transactions/metrics` | GET | Transaction metrics with account filtering |
| `/api/dashboard/summary` | GET | Dashboard analytics with account filtering |
| `/api/categories/analytics` | GET | Category breakdown |
| `/api/categories/hierarchy` | GET | Hierarchical category data for drill-down |
| `/api/ai/chat` | POST | AI chat interaction |
| `/api/ai/models` | GET | Available AI models |

## 🤖 AI Integration

The application supports multiple LLM providers through LangChain:
- **Google Gemini** - Fast and efficient
- **OpenAI GPT** - Widely used
- **Anthropic Claude** - Detailed analysis
- **Groq** - Ultra-fast inference

### Setting Up AI (Optional)

1. Create a `.env` file in the `backend/` directory:
   ```bash
   cd backend
   touch .env   # or create manually on Windows
   ```

2. Add your API key to the `.env` file:
   ```env
   # Google Gemini (recommended - free tier available)
   GEMINI_API_KEY=your-google-ai-api-key

   # OR OpenAI
   OPENAI_API_KEY=your-openai-api-key

   # OR Anthropic Claude
   ANTHROPIC_API_KEY=your-anthropic-api-key

   # OR Groq (free, fast inference)
   GROQ_API_KEY=your-groq-api-key
   ```

3. Get your API keys:
   - **Gemini**: https://makersuite.google.com/app/apikey
   - **OpenAI**: https://platform.openai.com/api-keys
   - **Anthropic**: https://console.anthropic.com/
   - **Groq**: https://console.groq.com/keys

Google Gemini support is included in the default backend requirements. For OpenAI, Anthropic, or Groq, install the corresponding optional LangChain integration package listed in `backend/requirements.txt` before enabling that provider.

> ⚠️ **Note**: The `.env` file is excluded from Git. Never commit API keys to version control.

## 🚧 Development Roadmap

### Phase 1 ✅
- [x] CSV upload and parsing
- [x] Basic transaction categorization
- [x] Dashboard with charts
- [x] AI chat integration

### Phase 2 ✅
- [x] Enhanced categorization with merchant database
- [x] Personal name auto-detection
- [x] Drill-down dashboard with subcategory views
- [x] Modern UI enhancements (styled dropdowns)
- [x] Indian merchant database (500+ merchants)

### Phase 3 (Planned)
- [ ] Budget tracking & alerts
- [ ] Recurring transaction detection
- [ ] Export reports (PDF/Excel)
- [ ] Multi-bank support
- [ ] Family member expense tracking

## 📄 Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- [CSV_FORMAT.md](CSV_FORMAT.md) - Input file format specification

## 🔒 Privacy & Security

- **Local Storage**: Uploaded statements and processed transaction data are stored on your machine.
- **Optional AI**: When AI chat is used, sanitized transaction context is sent to the selected provider. PII masking reduces exposure but does not guarantee complete anonymization; review the provider's privacy terms.
- **API Keys**: Only used for AI features (optional)

### 🛡️ PII Protection for AI Features

Before AI chat context is sent to a provider, the application attempts to detect and mask personal information:

| Data Type | Protection Method |
|-----------|------------------|
| **Personal Names** | Payee fields in UPI, NEFT, IMPS and RTGS descriptions replaced with `[PAYEE]`. Known merchants and bank codes are kept. Masking is default-deny, so some non-name words in those fields are also masked |
| **Phone Numbers** | Partially masked (e.g., `XXXXX43210`) |
| **Account Numbers** | Partially masked (e.g., `********6321`) |
| **UPI IDs** | Only the first character of the username is kept (e.g., `r***@bank`) |

**How it works:**
- Before any data is sent to AI providers (Gemini, OpenAI, etc.), the PII sanitizer automatically detects and masks sensitive information
- AI chat uses locally calculated monthly category totals for clear time-based aggregate questions and includes the full sanitized transaction ledger only when transaction- or merchant-level details are needed
- Merchant and business names in sanitized descriptions are retained for pharmacy, fees, transport, and other merchant-level analysis; account columns are not sent
- When a chart is requested, its values are aggregated by the backend and returned to the chat UI as a chart payload; the chart payload contains no transaction descriptions
- Masking is best-effort and pattern-based. Unusual bank formats or free-text remarks may not be caught
- A green **"PII Protected"** shield badge in the AI chat indicates protection is active
- Click the badge to see exactly what types of data are being protected

**Example transformation:**
```
Original:  UPI-TEST PERSON-TESTPHONE@SAMPLEBANK-TESTBANK-TESTREF-Payment
Sanitized: UPI-[PAYEE]-TESTPHONE@SAMPLEBANK-TESTBANK-TESTREF-Payment
```

Run the sanitizer regression tests with `python backend/test_pii_sanitizer.py`.

> **Important:** AI chat sends transaction context outside your machine after sanitization. Do not use AI features unless you are comfortable with the selected provider receiving that context.

## 📄 License

The repository does not currently include a `LICENSE` file. Confirm the intended license with the project owner before reuse or redistribution.
