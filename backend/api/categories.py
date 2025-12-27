"""
Categories API endpoints for Family Finance Tracker - DYNAMIC CALCULATION
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import pandas as pd
import os
from datetime import datetime, timedelta

# Create router with the correct prefix
router = APIRouter(prefix="/api/categories", tags=["categories"])

# Health check endpoint
@router.get("/health")
async def categories_health():
    """Health check for categories API"""
    return {
        "status": "healthy",
        "service": "Categories API",
        "version": "3.0.0",
        "data_source": "dynamic_calculation_from_transactions",
        "chart_support": "Chart.js 4.5.0 compatible"
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
        # Look for processed_data.csv in multiple locations
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
        
        # Calculate category totals
        income_total = df[df['Amount'] > 0]['Amount'].sum()
        expenditure_total = abs(df[df['Amount'] < 0]['Amount'].sum())
        
        # Calculate investment (from Investment category or large positive transfers)
        investment_df = df[df['Category'].str.contains('Investment', case=False, na=False)]
        if investment_df.empty:
            # Alternative: look for large transactions to investment platforms
            investment_df = df[df['Description'].str.contains('ZERODHA|GROWW|PAYTM MONEY|MUTUAL FUND', case=False, na=False)]
        investment_total = abs(investment_df['Amount'].sum())
        
        # Calculate education (from Education category or educational platforms)
        education_df = df[df['Category'].str.contains('Education', case=False, na=False)]
        if education_df.empty:
            # Alternative: look for educational transactions
            education_df = df[df['Description'].str.contains('BOOK|COURSE|UDEMY|COURSERA|EDUCATION', case=False, na=False)]
        education_total = abs(education_df['Amount'].sum())
        
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
