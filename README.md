# Family Finance Tracker

A privacy-first personal finance management application designed to help families track, analyze, and manage their expenses with smart categorization and AI-powered insights. Built with Angular 19 and FastAPI, this application processes all data locally - no cloud dependency.

## 📋 Overview

**Family Finance Tracker** helps you understand your spending patterns by analyzing bank statements. Upload your HDFC bank CSV statement, and the application will:
- Automatically categorize transactions (Food, Shopping, Utilities, etc.)
- Provide visual analytics with charts and summaries
- Offer AI-powered insights and chat capabilities
- Track income vs expenses over time

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📤 **Smart Upload** | Drag & drop CSV upload with automatic parsing |
| 🏷️ **Auto-Categorization** | ML-ready categorization with user learning |
| 📊 **Analytics Dashboard** | Interactive charts showing spending patterns |
| 🤖 **AI Chat** | Ask questions about your finances using multiple LLM providers |
| 🔒 **Privacy-First** | All data processed locally - nothing leaves your machine |
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
│   │   └── ai_chat.py         # AI chat integration
│   ├── SRC/                    # Core processing modules
│   │   ├── data_extraction.py # CSV parsing
│   │   ├── categories.py      # Categorization logic
│   │   └── analysis.py        # Financial analytics
│   └── requirements.txt
├── frontend/app/
│   └── src/app/
│       ├── modules/
│       │   ├── upload/        # File upload module
│       │   ├── transactions/  # Transaction list
│       │   ├── categories/    # Category management
│       │   └── ai-insights/   # AI chat interface
│       └── pages/
│           └── dashboard/     # Main dashboard
├── inputs/                     # Upload directory
└── synthetic_data/            # Test data generator
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload/` | POST | Upload bank statement CSV |
| `/api/transactions/` | GET | List transactions with filters |
| `/api/transactions/summary` | GET | Transaction summary statistics |
| `/api/dashboard/summary` | GET | Dashboard analytics |
| `/api/categories/analytics` | GET | Category breakdown |
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
   cd simple_finance_tracker/backend
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

> ⚠️ **Note**: The `.env` file is excluded from Git. Never commit API keys to version control.

## 🚧 Development Roadmap

### Phase 1 (Current) ✅
- [x] CSV upload and parsing
- [x] Basic transaction categorization
- [x] Dashboard with charts
- [x] AI chat integration

### Phase 2 (Planned)
- [ ] Enhanced category learning
- [ ] Budget tracking
- [ ] Recurring transaction detection
- [ ] Export reports

## 📄 Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- [CSV_FORMAT.md](CSV_FORMAT.md) - Input file format specification

## 🔒 Privacy & Security

- **Local Processing**: All data stays on your machine
- **No Cloud Storage**: No data is sent to external servers
- **API Keys**: Only used for AI features (optional)

## 📄 License

MIT License - Free for personal and commercial use.
