# Quick Start Guide

Get the Family Finance Tracker running in under 5 minutes.

Run the commands below from the repository root (the folder containing this file), unless a step says otherwise.

## Prerequisites

- **Python 3.9+** - [Download Python](https://python.org)
- **Node.js 18.19.1+, 20.11.1+, or 22.x** - [Download Node.js](https://nodejs.org)
- **Git** - [Download Git](https://git-scm.com)

---

## 🚀 Step 1: Start the Backend

Open a terminal and run:

```bash
# Navigate to backend directory
cd backend

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
cd frontend/app

# Install dependencies (first time only)
npm install

# Start the Angular development server
npm start
```

✅ **Frontend running at:** http://localhost:4200

---

## 🌐 Step 3: Access the Application

Open your browser and navigate to: **http://localhost:4200**

Each upload batch replaces the current processed dataset. Select all CSV/Excel
statements you want included in the dashboard together; the upload accepts any number
of files, up to 50MB each. The selected files are parsed, normalized, and categorized
as one batch, with duplicate transactions within that batch removed. When every file
processes successfully, `processed_data.csv` is atomically overwritten with only the
batch's transactions, and dashboard totals are recalculated from it. If any file fails,
the existing processed dataset is left unchanged and the full batch must be corrected
and uploaded again. Original files are kept in `inputs`; uploading identical file
content reuses the existing source file. The `inputs` folder is local and Git-ignored;
the synthetic data generator also writes its test files there.

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
cd backend
```

Create `.env` file with your API key:

```env
# Choose one or more:
GEMINI_API_KEY=your-google-ai-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GROQ_API_KEY=your-groq-key
```

Google Gemini support is included in the default backend requirements. For OpenAI, Anthropic, or Groq, install the corresponding optional LangChain integration package listed in `backend/requirements.txt` before using that provider.

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
cd backend
python -m uvicorn api.main:app --reload --port 8000
```

---

## 📁 Test with Sample Data

Generate test data to try the application:

```bash
cd synthetic_data
python generate_hdfc_data.py --presets
```

This creates fictional sample bank statement files in the Git-ignored `inputs` folder that you can upload to test the application.

---

## ✅ Verification Checklist

- [ ] Backend shows "Uvicorn running on http://127.0.0.1:8000"
- [ ] Frontend shows "Compiled successfully"
- [ ] Browser opens http://localhost:4200 without errors
- [ ] Upload page accepts CSV, XLS, and XLSX statements
- [ ] Upload multiple statements and confirm they replace the processed dataset
- [ ] Dashboard shows data after upload

---

**Need more help?** Check the [README.md](README.md) for detailed documentation.
