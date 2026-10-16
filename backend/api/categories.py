"""
Categories API endpoints for Family Finance Tracker - DYNAMIC CALCULATION
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import pandas as pd
import os
from datetime import datetime, timedelta
import sys

# Add SRC to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'SRC')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from data_extraction import get_processed_data_path, save_processed_data

# Import refined categorizer with fallback
USE_REFINED = False
RefinedCategorizerClass = None
REFINED_CATEGORIES = {}

def _get_default_colors():
    return {
        "Income": "#4CAF50", "Investments": "#2196F3", "Insurance": "#00BCD4",
        "Education": "#9C27B0", "Healthcare": "#9966FF", "Money Transfer": "#607D8B",
        "Individual Transfers": "#78909C", "Subscriptions": "#AB47BC",
        "Food & Dining": "#FF6384", "Shopping": "#36A2EB", "Transportation": "#FFCE56",
        "Travel": "#5C6BC0", "Telecom": "#26A69A",
        "Utilities": "#4BC0C0", "Entertainment": "#FF9F40", "Housing": "#8BC34A",
        "Other": "#795548"
    }

def _get_default_icons():
    return {
        "Income": "💰", "Investments": "💎", "Insurance": "🛡️", "Education": "📚",
        "Healthcare": "🏥", "Money Transfer": "💸", "Individual Transfers": "👤",
        "Subscriptions": "🔄", "Food & Dining": "🍔",
        "Shopping": "🛒", "Transportation": "🚗", "Travel": "🧳",
        "Telecom": "📱", "Utilities": "💡",
        "Entertainment": "🎬", "Housing": "🏠", "Other": "📦"
    }

try:
    from refined_categories import (
        RefinedCategorizer as _RefinedCategorizer, 
        REFINED_CATEGORIES as _REFINED_CATEGORIES, 
        get_category_colors, get_category_icons, get_category_group
    )
    RefinedCategorizerClass = _RefinedCategorizer
    REFINED_CATEGORIES = _REFINED_CATEGORIES
    USE_REFINED = True
except ImportError as e:
    print(f"Warning: Could not import refined_categories: {e}")
    get_category_colors = _get_default_colors
    get_category_icons = _get_default_icons
    get_category_group = lambda category: 'Income' if category == 'Income' else 'Expense'

try:
    from categories import categorize_transaction, learn_category
except ImportError as e:
    print(f"Warning: Could not import categories: {e}")
    def categorize_transaction(desc, amt):
        return {"category": "Other", "subcategory": "Uncategorized"}
    def learn_category(desc, cat, subcat):
        return False

# Create router with the correct prefix
router = APIRouter(prefix="/api/categories", tags=["categories"])


# Pydantic models for request/response
class LearnCategoryRequest(BaseModel):
    description: str
    category: str
    subcategory: str
    match_type: Optional[str] = "keyword"


class RecategorizeRequest(BaseModel):
    force: Optional[bool] = False


# Health check endpoint
@router.get("/health")
async def categories_health():
    """Health check for categories API"""
    return {
        "status": "healthy",
        "service": "Categories API",
        "version": "3.1.0",  # Updated version
        "data_source": "dynamic_calculation_from_transactions",
        "chart_support": "Chart.js 4.5.0 compatible",
        "refined_categorizer": USE_REFINED,
        "features": [
            "Investment tracking (Zerodha, SIP, Gold, Jewelry)",
            "Insurance separation (LIC, Health, Vehicle)",
            "Education categorization",
            "Healthcare detection",
            "Smart UPI differentiation",
            "User-learnable mappings"
        ]
    }

# Analytics endpoint - DYNAMIC DATA
@router.get("/analytics")
async def categories_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    chart_format: Optional[str] = Query("default", description="Chart format (default, chartjs)")
):
    """Get category analytics data - DYNAMICALLY CALCULATED from actual transactions"""
    
    print("🔍 Categories Analytics API called - DYNAMIC CALCULATION")
    print(f"   - Start Date: {start_date}")
    print(f"   - End Date: {end_date}")
    print(f"   - Chart Format: {chart_format}")
    
    try:
        # Calculate real data from processed_data.csv
        real_data = await calculate_category_analytics(start_date, end_date)
        
        if chart_format == "chartjs":
            # Return Chart.js optimized format
            return {
                "labels": [item["category_name"] for item in real_data],
                "datasets": [{
                    "label": "Monthly Average (₹)",
                    "data": [item["monthly_amount"] for item in real_data],
                    "backgroundColor": [item["color"] + "80" for item in real_data],
                    "borderColor": [item["color"] for item in real_data],
                    "borderWidth": 2
                }]
            }
        
        return real_data
        
    except Exception as e:
        print(f"❌ Error calculating analytics: {e}")
        # Return empty data instead of hardcoded values
        return []

async def calculate_category_analytics(start_date: Optional[str], end_date: Optional[str]) -> List[Dict[str, Any]]:
    """Calculate category analytics from actual processed_data.csv"""
    
    try:
        csv_path = get_processed_data_path()
        if not os.path.exists(csv_path):
            print("❌ processed_data.csv not found")
            return get_empty_categories()
        
        print(f"📊 Loading transaction data from: {csv_path}")
        
        # Load and process the data
        df = pd.read_csv(csv_path)
        print(f"   Loaded {len(df)} transactions")
        
        # Clean the data
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
        df = df.dropna(subset=['Amount', 'Transaction Date'])
        if 'Description' not in df.columns:
            df['Description'] = ''
        if 'Category' not in df.columns:
            df['Category'] = ''
        missing_categories = (
            df['Category'].isna()
            | df['Category'].astype(str).str.strip().eq('')
        )
        for index in df.index[missing_categories]:
            result = categorize_transaction(
                str(df.at[index, 'Description']),
                float(df.at[index, 'Amount'])
            )
            df.at[index, 'Category'] = result['category']
        
        # Filter by date range if provided
        if start_date:
            df = df[df['Transaction Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Transaction Date'] <= pd.to_datetime(end_date)]
        
        # Calculate monthly periods
        df['Month'] = df['Transaction Date'].dt.to_period('M')
        num_months = len(df['Month'].unique())
        
        if num_months == 0:
            print("❌ No data found for the specified date range")
            return get_empty_categories()
        
        print(f"   Analyzing {num_months} months of data")
        
        # Keep cashflow categories separate so transfers and planned or
        # investment outflows are not reported as day-to-day expenses.
        category_groups = df['Category'].map(get_category_group)
        income_total = df.loc[
            df['Amount'].gt(0) & category_groups.eq('Income'),
            'Amount'
        ].sum()
        expenditure_total = abs(df.loc[
            df['Amount'].lt(0) & category_groups.eq('Expense'),
            'Amount'
        ].sum())
        investment_total = abs(df.loc[
            df['Amount'].lt(0) & category_groups.eq('Investment'),
            'Amount'
        ].sum())
        education_total = abs(df.loc[
            df['Amount'].lt(0) & df['Category'].eq('Education'),
            'Amount'
        ].sum())
        
        # Calculate monthly averages
        monthly_income = income_total / num_months
        monthly_expenditure = expenditure_total / num_months
        monthly_investment = investment_total / num_months
        monthly_education = education_total / num_months
        
        print(f"   📈 Calculated monthly averages:")
        print(f"      Income: ₹{monthly_income:,.2f}")
        print(f"      Expenditure: ₹{monthly_expenditure:,.2f}")
        print(f"      Investment: ₹{monthly_investment:,.2f}")
        print(f"      Education: ₹{monthly_education:,.2f}")
        
        # Create dynamic data structure
        categories = [
            {
                "category_id": "income",
                "category_name": "Income",
                "icon": "💰",
                "color": "#4CAF50",
                "monthly_amount": round(monthly_income, 2),
                "percentage_of_income": 100.0,
                "trend": "stable",
                "trend_value": 0.0,
                "budget_target": 100.0
            },
            {
                "category_id": "expenditure",
                "category_name": "Expenditure",
                "icon": "🛒",
                "color": "#FF9800",
                "monthly_amount": round(monthly_expenditure, 2),
                "percentage_of_income": round((monthly_expenditure / monthly_income) * 100, 1) if monthly_income > 0 else 0,
                "trend": "up" if monthly_expenditure > monthly_income else "stable",
                "trend_value": round(((monthly_expenditure - monthly_income) / monthly_income) * 100, 1) if monthly_income > 0 else 0,
                "budget_target": 70.0
            },
            {
                "category_id": "investment",
                "category_name": "Investment",
                "icon": "💎",
                "color": "#2196F3",
                "monthly_amount": round(monthly_investment, 2),
                "percentage_of_income": round((monthly_investment / monthly_income) * 100, 1) if monthly_income > 0 else 0,
                "trend": "up" if monthly_investment > 0 else "stable",
                "trend_value": 5.0,
                "budget_target": 20.0
            },
            {
                "category_id": "education",
                "category_name": "Education",
                "icon": "📚",
                "color": "#9C27B0",
                "monthly_amount": round(monthly_education, 2),
                "percentage_of_income": round((monthly_education / monthly_income) * 100, 1) if monthly_income > 0 else 0,
                "trend": "stable",
                "trend_value": 0.0,
                "budget_target": 5.0
            }
        ]
        
        return categories
        
    except Exception as e:
        print(f"❌ Error in calculate_category_analytics: {e}")
        return get_empty_categories()

def get_empty_categories() -> List[Dict[str, Any]]:
    """Return empty categories when no data is available"""
    return [
        {
            "category_id": "income",
            "category_name": "Income",
            "icon": "💰",
            "color": "#4CAF50",
            "monthly_amount": 0.0,
            "percentage_of_income": 100.0,
            "trend": "stable",
            "trend_value": 0.0,
            "budget_target": 100.0
        },
        {
            "category_id": "expenditure",
            "category_name": "Expenditure",
            "icon": "🛒",
            "color": "#FF9800",
            "monthly_amount": 0.0,
            "percentage_of_income": 0.0,
            "trend": "stable",
            "trend_value": 0.0,
            "budget_target": 70.0
        },
        {
            "category_id": "investment",
            "category_name": "Investment",
            "icon": "💎",
            "color": "#2196F3",
            "monthly_amount": 0.0,
            "percentage_of_income": 0.0,
            "trend": "stable",
            "trend_value": 0.0,
            "budget_target": 20.0
        },
        {
            "category_id": "education",
            "category_name": "Education",
            "icon": "📚",
            "color": "#9C27B0",
            "monthly_amount": 0.0,
            "percentage_of_income": 0.0,
            "trend": "stable",
            "trend_value": 0.0,
            "budget_target": 5.0
        }
    ]

# Summary endpoint - DYNAMIC DATA
@router.get("/summary")
async def categories_summary():
    """Get category summary data - DYNAMICALLY CALCULATED"""
    try:
        categories = await calculate_category_analytics(None, None)
        
        return {
            "total_income": categories[0]["monthly_amount"],
            "total_expenditure": categories[1]["monthly_amount"],
            "total_investment": categories[2]["monthly_amount"],
            "total_education": categories[3]["monthly_amount"],
            "savings_rate": round(((categories[0]["monthly_amount"] - categories[1]["monthly_amount"]) / categories[0]["monthly_amount"]) * 100, 1) if categories[0]["monthly_amount"] > 0 else 0,
            "data_source": "dynamic_calculation"
        }
    except Exception as e:
        print(f"❌ Error in categories_summary: {e}")
        return {
            "total_income": 0,
            "total_expenditure": 0,
            "total_investment": 0,
            "total_education": 0,
            "savings_rate": 0,
            "data_source": "error"
        }


# ============================================================================
# NEW ENDPOINTS FOR REFINED CATEGORIZATION
# ============================================================================

@router.get("/all")
async def get_all_categories_list():
    """
    Get all available categories with their subcategories, icons, and colors.
    Uses the refined categorization system.
    """
    try:
        if USE_REFINED:
            categories_info = {}
            for cat_name, cat_info in REFINED_CATEGORIES.items():
                categories_info[cat_name] = {
                    "icon": cat_info.get("icon", "📦"),
                    "color": cat_info.get("color", "#795548"),
                    "description": cat_info.get("description", ""),
                    "priority": cat_info.get("priority", 99),
                    "subcategories": list(cat_info.get("subcategories", {}).keys())
                }
            return {
                "success": True,
                "categories": categories_info,
                "total_categories": len(categories_info)
            }
        else:
            return {
                "success": False,
                "error": "Refined categorizer not available",
                "categories": {}
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learn")
async def learn_from_user(request: LearnCategoryRequest):
    """
    Learn from user corrections to improve future categorization.
    
    This creates a user-defined mapping that will be used for similar transactions.
    """
    try:
        if not USE_REFINED:
            raise HTTPException(status_code=503, detail="Refined categorizer not available")
        
        success = learn_category(
            description=request.description,
            category=request.category,
            subcategory=request.subcategory
        )
        
        if success:
            return {
                "success": True,
                "message": f"Learned: '{request.description}' → {request.category}/{request.subcategory}",
                "description": request.description,
                "category": request.category,
                "subcategory": request.subcategory
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save learning")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/categorize")
async def categorize_single(description: str = Body(...), amount: float = Body(0.0)):
    """
    Categorize a single transaction description.
    
    Returns the category, subcategory, confidence, and reason.
    """
    try:
        if USE_REFINED and RefinedCategorizerClass is not None:
            categorizer = RefinedCategorizerClass()
            result = categorizer.categorize(description, amount)
            return {
                "success": True,
                "description": description,
                "amount": amount,
                "category": result["category"],
                "subcategory": result["subcategory"],
                "confidence": result["confidence"],
                "reason": result["reason"]
            }
        else:
            result = categorize_transaction(description, amount)
            return {
                "success": True,
                "description": description,
                "amount": amount,
                "category": result["category"],
                "subcategory": result["subcategory"],
                "confidence": "medium",
                "reason": "Legacy categorization"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recategorize-all")
async def recategorize_all_data(request: RecategorizeRequest):
    """
    Re-categorize all transactions in processed_data.csv using the refined categorizer.
    
    This is useful after updating categorization rules or learning new mappings.
    """
    try:
        # Get the processed data file path
        data_file = get_processed_data_path()
        
        if not os.path.exists(data_file):
            raise HTTPException(status_code=404, detail="No processed data found")
        
        # Read the data
        df = pd.read_csv(data_file)
        original_count = len(df)
        if 'Category' not in df.columns:
            df['Category'] = ''
        if 'Subcategory' not in df.columns:
            df['Subcategory'] = ''
        
        # Count original categories
        original_categories = df['Category'].value_counts().to_dict() if 'Category' in df.columns else {}
        
        # Re-categorize each transaction
        changes = []
        for idx, row in df.iterrows():
            description = str(row.get('Description', ''))
            amount = float(row.get('Amount', 0))
            old_category = row.get('Category', 'Other')
            
            result = categorize_transaction(description, amount)
            new_category = result['category']
            new_subcategory = result['subcategory']
            
            df.at[idx, 'Category'] = new_category
            if 'Subcategory' in df.columns:
                df.at[idx, 'Subcategory'] = new_subcategory
            
            if old_category != new_category:
                changes.append({
                    "description": description[:50] + "..." if len(description) > 50 else description,
                    "old_category": old_category,
                    "new_category": new_category,
                    "new_subcategory": new_subcategory
                })
        
        # Save the updated data
        if not save_processed_data(df):
            raise HTTPException(status_code=500, detail="Could not save recategorized transactions")
        
        # Count new categories
        new_categories = df['Category'].value_counts().to_dict()
        
        return {
            "success": True,
            "message": f"Re-categorized {original_count} transactions",
            "total_transactions": original_count,
            "changes_made": len(changes),
            "original_distribution": original_categories,
            "new_distribution": new_categories,
            "sample_changes": changes[:20]  # Return first 20 changes as sample
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/colors")
async def get_colors():
    """Get color mapping for all categories."""
    try:
        if USE_REFINED:
            return {
                "success": True,
                "colors": get_category_colors()
            }
        else:
            return {
                "success": True,
                "colors": {
                    "Income": "#4CAF50",
                    "Investments": "#2196F3",
                    "Insurance": "#00BCD4",
                    "Education": "#9C27B0",
                    "Healthcare": "#9966FF",
                    "Money Transfer": "#607D8B",
                    "Food & Dining": "#FF6384",
                    "Shopping": "#36A2EB",
                    "Transportation": "#FFCE56",
                    "Travel": "#5C6BC0",
                    "Telecom": "#26A69A",
                    "Utilities": "#4BC0C0",
                    "Entertainment": "#FF9F40",
                    "Housing": "#8BC34A",
                    "Other": "#795548"
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/icons")
async def get_icons():
    """Get icon mapping for all categories."""
    try:
        if USE_REFINED:
            return {
                "success": True,
                "icons": get_category_icons()
            }
        else:
            return {
                "success": True,
                "icons": {
                    "Income": "💰",
                    "Investments": "💎",
                    "Insurance": "🛡️",
                    "Education": "📚",
                    "Healthcare": "🏥",
                    "Money Transfer": "💸",
                    "Food & Dining": "🍔",
                    "Shopping": "🛒",
                    "Transportation": "🚗",
                    "Travel": "🧳",
                    "Telecom": "📱",
                    "Utilities": "💡",
                    "Entertainment": "🎬",
                    "Housing": "🏠",
                    "Other": "📦"
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
