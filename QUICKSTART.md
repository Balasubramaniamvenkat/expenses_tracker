# Quick Start Guide

Get the Family Finance Tracker running in under 5 minutes.

## Prerequisites

- **Python 3.9+** - [Download Python](https://python.org)
- **Node.js 18+** - [Download Node.js](https://nodejs.org)
- **Git** - [Download Git](https://git-scm.com)

---

## 🚀 Step 1: Start the Backend

Open a terminal and run:

```bash
# Navigate to backend directory
cd simple_finance_tracker/backend

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the backend server
python -m uvicorn api.main:app --reload --port 8000
```

✅ **Backend running at:** http://localhost:8000

📚 **API Documentation:** http://localhost:8000/docs

---

## 🎨 Step 2: Start the Frontend

Open a **new terminal** and run:

```bash
# Navigate to frontend directory
cd simple_finance_tracker/frontend/app

# Install dependencies (first time only)
npm install

# Start the Angular development server
npm start
```

✅ **Frontend running at:** http://localhost:4200

---

## 🌐 Step 3: Access the Application

Open your browser and navigate to: **http://localhost:4200**

---

## 📊 Quick Reference

| Component | URL | Command |
|-----------|-----|---------|
| Frontend | http://localhost:4200 | `npm start` |
| Backend | http://localhost:8000 | `python -m uvicorn api.main:app --reload --port 8000` |
| API Docs | http://localhost:8000/docs | Auto-generated Swagger UI |

---

## 🤖 Optional: Enable AI Features

To use the AI chat feature, create a `.env` file in the `backend` directory:

```bash
cd simple_finance_tracker/backend
```

Create `.env` file with your API key:

```env
# Choose one or more:
GEMINI_API_KEY=your-google-ai-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GROQ_API_KEY=your-groq-key
```

---

## 🔧 Troubleshooting

### Port Already in Use

**Windows (PowerShell):**
```powershell
# Find and kill process on port 8000
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Find and kill process on port 4200
Get-NetTCPConnection -LocalPort 4200 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

**macOS/Linux:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 4200
lsof -ti:4200 | xargs kill -9
```

### NumPy Compatibility Warning

If you see NumPy warnings:
```bash
pip install "numpy<2.0.0"
```

### Module Not Found Errors

Ensure you're running the backend from the correct directory:
```bash
# Must run from backend directory, NOT backend/api
cd simple_finance_tracker/backend
python -m uvicorn api.main:app --reload --port 8000
```

---

## 📁 Test with Sample Data

Generate test data to try the application:

```bash
cd simple_finance_tracker/synthetic_data
python generate_hdfc_data.py --presets
```

This creates sample bank statement files in the `inputs` folder that you can upload to test the application.

---

## ✅ Verification Checklist

- [ ] Backend shows "Uvicorn running on http://0.0.0.0:8000"
- [ ] Frontend shows "Compiled successfully"
- [ ] Browser opens http://localhost:4200 without errors
- [ ] Upload page accepts CSV files
- [ ] Dashboard shows data after upload

---

**Need more help?** Check the [README.md](README.md) for detailed documentation.
