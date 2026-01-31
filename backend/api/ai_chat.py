"""
AI Chat API endpoints for Family Finance Tracker
Using LangChain for unified LLM interface - easily switch between providers!

LangChain Benefits:
- Same code works for Gemini, OpenAI, Claude, Groq, and more
- Just change the model_id to switch providers
- Consistent message format across all LLMs
- Easy to add new providers in the future
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import pandas as pd
from datetime import datetime
from typing import Tuple, Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# PII Sanitization
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'SRC'))
from pii_sanitizer import PIISanitizer, sanitize_for_ai_context  # type: ignore

# LangChain imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

router = APIRouter(prefix="/api/ai", tags=["ai"])

# ===========================================
# Model Definitions - All supported models
# ===========================================

AVAILABLE_MODELS = {
    "gemini": {
        "provider": "Google",
        "models": [
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "description": "Latest and fastest"},
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "description": "Fast and efficient"},
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "description": "Most capable"},
        ],
        "env_key": "GEMINI_API_KEY"
    },
    "openai": {
        "provider": "OpenAI",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "description": "Latest and most capable"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "Fast and affordable"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "Previous generation"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Fast and cheap"},
        ],
        "env_key": "OPENAI_API_KEY"
    },
    "anthropic": {
        "provider": "Anthropic",
        "models": [
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "description": "Best balance"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "description": "Most capable"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "description": "Fast and light"},
        ],
        "env_key": "ANTHROPIC_API_KEY"
    },
    "groq": {
        "provider": "Groq",
        "models": [
            {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "description": "Most capable"},
            {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B", "description": "Ultra fast"},
            {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "description": "Good balance"},
        ],
        "env_key": "GROQ_API_KEY"
    }
}

# ===========================================
# Request/Response Models
# ===========================================

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    model_id: str
    history: Optional[List[ChatMessage]] = []

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    provider: str

class ModelsResponse(BaseModel):
    models: List[ModelInfo]
    default_model: Optional[str]

# ===========================================
# LangChain LLM Factory - The Magic!
# ===========================================

def get_llm(model_id: str):
    """
    Factory function to create the appropriate LangChain LLM instance.
    This is where the magic happens - same interface, any provider!
    
    LangChain abstracts away the differences between providers.
    """
    provider = get_provider_from_model(model_id)
    
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_id,
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7,
            convert_system_message_to_human=True
        )
    
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_id,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7
        )
    
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_id,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.7
        )
    
    elif provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model_id,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.7
        )
    
    else:
        raise ValueError(f"Unknown provider for model: {model_id}")

# ===========================================
# Helper Functions
# ===========================================

def get_available_models() -> List[ModelInfo]:
    """Get list of models that have valid API keys configured"""
    available = []
    
    for provider_key, provider_info in AVAILABLE_MODELS.items():
        api_key = os.getenv(provider_info["env_key"], "").strip()
        
        if api_key:  # Key is configured
            for model in provider_info["models"]:
                available.append(ModelInfo(
                    id=model["id"],
                    name=model["name"],
                    description=model["description"],
                    provider=provider_info["provider"]
                ))
    
    return available

def get_provider_from_model(model_id: str) -> str:
    """Determine which provider a model belongs to"""
    for provider_key, provider_info in AVAILABLE_MODELS.items():
        for model in provider_info["models"]:
            if model["id"] == model_id:
                return provider_key
    return None

def get_transaction_context() -> tuple:
    """
    Load transaction data and create context for AI.
    Returns sanitized context with PII removed for privacy.
    
    Returns:
        tuple: (context_string, pii_summary_dict)
    """
    try:
        # Find processed_data.csv
        possible_paths = [
            'processed_data.csv',
            '../processed_data.csv',
            '../../processed_data.csv',
            os.path.join(os.path.dirname(__file__), '..', '..', 'processed_data.csv')
        ]
        
        csv_path = None
        for path in possible_paths:
            full_path = os.path.abspath(path)
            if os.path.exists(full_path):
                csv_path = full_path
                break
        
        if not csv_path:
            return "No transaction data available. Please upload a bank statement first.", {}
        
        print(f"📊 Loading transaction data from: {csv_path}")
        
        # Load and process the data
        df = pd.read_csv(csv_path)
        
        # ========================================
        # PII SANITIZATION - Protect user privacy
        # ========================================
        print("🔒 Sanitizing PII from transaction data...")
        sanitizer = PIISanitizer()
        df = sanitizer.sanitize_dataframe(df, description_column='Description')
        pii_summary = sanitizer.get_sanitization_summary()
        print(f"✅ PII Sanitization complete: {pii_summary['total_pii_masked']} items masked")
        print(f"   - Phone numbers: {pii_summary['breakdown']['phone_numbers']}")
        print(f"   - Account numbers: {pii_summary['breakdown']['account_numbers']}")
        print(f"   - Personal names: {pii_summary['breakdown']['personal_names']}")
        print(f"   - UPI IDs: {pii_summary['breakdown']['upi_ids']}")
        
        # Calculate summary statistics
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
        df = df.dropna(subset=['Amount', 'Transaction Date'])
        
        # Basic stats
        total_income = df[df['Amount'] > 0]['Amount'].sum()
        total_expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
        net_savings = total_income - total_expenses
        
        # Date range
        date_min = df['Transaction Date'].min().strftime('%Y-%m-%d')
        date_max = df['Transaction Date'].max().strftime('%Y-%m-%d')
        
        # Category breakdown
        category_summary = df.groupby('Category')['Amount'].sum().to_dict()
        
        # Top merchants/descriptions for expenses
        expense_df = df[df['Amount'] < 0].copy()
        expense_df['Amount'] = abs(expense_df['Amount'])
        top_merchants = expense_df.groupby('Description')['Amount'].sum().nlargest(10).to_dict()
        
        context = f"""
FINANCIAL DATA SUMMARY:
=======================
Data Period: {date_min} to {date_max}
Total Transactions: {len(df)}

TOTALS:
- Total Income: ₹{total_income:,.2f}
- Total Expenses: ₹{total_expenses:,.2f}
- Net Savings: ₹{net_savings:,.2f}
- Savings Rate: {(net_savings/total_income*100) if total_income > 0 else 0:.1f}%

CATEGORY BREAKDOWN:
{chr(10).join(f'- {cat}: ₹{abs(amt):,.2f}' for cat, amt in sorted(category_summary.items(), key=lambda x: abs(x[1]), reverse=True)[:15])}

TOP SPENDING MERCHANTS:
{chr(10).join(f'- {desc[:60]}: ₹{amt:,.2f}' for desc, amt in list(top_merchants.items())[:10])}

RECENT TRANSACTIONS (Last 30):
{df.tail(30)[['Transaction Date', 'Description', 'Amount', 'Category']].to_string(index=False)}

NOTE: Personal names, phone numbers, and account numbers have been anonymized for privacy.
"""
        return context, pii_summary
        
    except Exception as e:
        print(f"❌ Error loading transaction data: {e}")
        return f"Error loading transaction data: {str(e)}", {}

def build_chat_messages(user_message: str, context: str, history: Optional[List[ChatMessage]] = None, pii_summary: Optional[Dict[str, Any]] = None) -> List:
    """Build LangChain message list from user input and history"""
    
    if history is None:
        history = []
    
    privacy_note = ""
    if pii_summary and pii_summary.get('total_pii_masked', 0) > 0:
        privacy_note = f"""

PRIVACY NOTICE: This data has been sanitized to protect user privacy.
- {pii_summary['breakdown'].get('personal_names', 0)} personal names replaced with placeholders like [PAYEE], [ACCOUNT_HOLDER]
- {pii_summary['breakdown'].get('phone_numbers', 0)} phone numbers partially masked
- {pii_summary['breakdown'].get('account_numbers', 0)} account numbers partially masked
When referring to transactions, use the category and merchant type rather than personal identifiers."""
    
    system_prompt = f"""You are a helpful financial assistant analyzing the user's bank transaction data.
Use the following financial data context to answer questions accurately.
Always format currency in Indian Rupees (₹) with proper comma separators.
Be concise but informative. Use tables and bullet points for clarity.
If asked about specific transactions, search through the data provided.{privacy_note}

{context}"""
    
    messages = [SystemMessage(content=system_prompt)]
    
    # Add conversation history
    for msg in history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))
    
    # Add current message
    messages.append(HumanMessage(content=user_message))
    
    return messages

def get_install_hint(model_id: str) -> str:
    """Get pip install hint for missing provider"""
    provider = get_provider_from_model(model_id)
    hints = {
        "gemini": "langchain-google-genai",
        "openai": "langchain-openai",
        "anthropic": "langchain-anthropic",
        "groq": "langchain-groq"
    }
    return hints.get(provider, "langchain")

# ===========================================
# API Endpoints
# ===========================================

@router.get("/health")
async def ai_health():
    """Health check for AI API"""
    available_models = get_available_models()
    return {
        "status": "healthy",
        "service": "AI Chat API",
        "framework": "LangChain",
        "description": "Unified LLM interface - same code for any provider!",
        "available_models_count": len(available_models),
        "providers_configured": list(set(m.provider for m in available_models))
    }

@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """Get list of available AI models (based on configured API keys)"""
    models = get_available_models()
    default_model = os.getenv("DEFAULT_AI_MODEL", "gemini-1.5-flash")
    
    # Verify default model is available
    model_ids = [m.id for m in models]
    if default_model not in model_ids and models:
        default_model = models[0].id
    
    return ModelsResponse(
        models=models,
        default_model=default_model if models else None
    )

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Send a message to the selected AI model using LangChain.
    
    The beauty of LangChain: Same code works for ANY provider!
    - Gemini? ✓
    - OpenAI? ✓
    - Claude? ✓
    - Groq? ✓
    
    Just change the model_id, and LangChain handles the rest!
    """
    
    # Validate model is available
    available_models = get_available_models()
    model_ids = [m.id for m in available_models]
    
    if not available_models:
        raise HTTPException(
            status_code=503,
            detail="No AI models available. Please configure at least one API key in backend/.env file."
        )
    
    if request.model_id not in model_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{request.model_id}' is not available. Configure the API key in .env file."
        )
    
    try:
        # Get transaction context (sanitized for privacy)
        context, pii_summary = get_transaction_context()
        
        # Build messages using LangChain message types
        messages = build_chat_messages(request.message, context, request.history, pii_summary)
        
        # Get the LLM instance (works the same for any provider!)
        llm = get_llm(request.model_id)
        
        # Invoke the LLM - same call for Gemini, OpenAI, Claude, or Groq!
        provider = get_provider_from_model(request.model_id)
        print(f"🤖 Invoking {request.model_id} ({provider}) via LangChain...")
        
        response = llm.invoke(messages)
        
        print(f"✅ Response received from {provider}")
        
        return {
            "response": response.content,
            "model_used": request.model_id,
            "provider": provider,
            "framework": "LangChain",
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError as e:
        hint = get_install_hint(request.model_id)
        raise HTTPException(
            status_code=500,
            detail=f"LangChain provider not installed. Run: pip install {hint}"
        )
    except Exception as e:
        print(f"❌ Error calling AI model: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error calling AI model: {str(e)}"
        )

@router.get("/quick-questions")
async def get_quick_questions():
    """Get suggested quick questions for users"""
    return {
        "questions": [
            "What did I spend on food this month?",
            "Show my top 5 expenses",
            "What's my monthly average spending?",
            "Compare income vs expenses",
            "Which category am I overspending on?",
            "Any unusual transactions?",
            "What's my savings rate?",
            "Summarize my financial health"
        ]
    }


@router.get("/privacy-status")
async def get_privacy_status():
    """
    Get the current privacy protection status.
    Shows what PII protection measures are active.
    """
    # Get a sample sanitization to show what's being protected
    try:
        context, pii_summary = get_transaction_context()
        
        return {
            "privacy_enabled": True,
            "protection_measures": [
                {
                    "type": "personal_names",
                    "description": "Personal names replaced with [PAYEE], [ACCOUNT_HOLDER]",
                    "count": pii_summary.get('breakdown', {}).get('personal_names', 0),
                    "icon": "person_off"
                },
                {
                    "type": "phone_numbers",
                    "description": "Phone numbers partially masked (e.g., XXXXX43210)",
                    "count": pii_summary.get('breakdown', {}).get('phone_numbers', 0),
                    "icon": "phone_disabled"
                },
                {
                    "type": "account_numbers",
                    "description": "Account/reference numbers partially masked",
                    "count": pii_summary.get('breakdown', {}).get('account_numbers', 0),
                    "icon": "credit_card_off"
                },
                {
                    "type": "upi_ids",
                    "description": "UPI IDs masked (e.g., us***er@bank)",
                    "count": pii_summary.get('breakdown', {}).get('upi_ids', 0),
                    "icon": "lock"
                }
            ],
            "total_items_protected": pii_summary.get('total_pii_masked', 0),
            "message": "Your personal information is protected. Only anonymized financial data is shared with AI."
        }
    except Exception as e:
        return {
            "privacy_enabled": True,
            "protection_measures": [],
            "total_items_protected": 0,
            "message": "Privacy protection is enabled. Upload data to see protection details."
        }
