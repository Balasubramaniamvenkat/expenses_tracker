"""
Dashboard API endpoints for Family Finance Tracker
Provides summary statistics and analytics for the dashboard view
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
import pandas as pd
import os
from datetime import datetime, timedelta
from collections import defaultdict

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

def get_processed_data_path() -> Optional[str]:
    """Find the processed_data.csv file"""
    possible_paths = [
        'processed_data.csv',
        '../processed_data.csv',
        '../../processed_data.csv',
        os.path.join(os.path.dirname(__file__), '..', '..', 'processed_data.csv')
    ]
    
    for path in possible_paths:
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            return full_path
    return None


def load_transaction_data() -> Optional[pd.DataFrame]:
    """Load and clean transaction data"""
    csv_path = get_processed_data_path()
    if not csv_path:
        return None
    
    try:
        df = pd.read_csv(csv_path)
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
        df = df.dropna(subset=['Amount', 'Transaction Date'])
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


@router.get("/health")
async def dashboard_health():
    """Health check for dashboard API"""
    return {
        "status": "healthy",
        "service": "Dashboard API",
        "version": "1.0.0"
    }


@router.get("/summary")
async def get_dashboard_summary() -> Dict[str, Any]:
    """Get comprehensive dashboard summary with all financial metrics"""
    
    df = load_transaction_data()
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No transaction data found. Please upload a bank statement.")
    
    # Calculate basic metrics
    income_df = df[df['Amount'] > 0]
    expense_df = df[df['Amount'] < 0]
    
    total_income = float(income_df['Amount'].sum())
    total_expenses = float(abs(expense_df['Amount'].sum()))
    
    # Calculate investments (from category or keywords)
    investment_keywords = ['zerodha', 'mutual fund', 'investment', 'stocks', 'gold', 'mmtc']
    investment_mask = expense_df['Description'].str.lower().str.contains('|'.join(investment_keywords), na=False)
    if 'Category' in expense_df.columns:
        investment_mask = investment_mask | (expense_df['Category'].str.lower() == 'investments')
    total_investments = float(abs(expense_df[investment_mask]['Amount'].sum()))
    
    # Adjust expenses to exclude investments
    actual_expenses = total_expenses - total_investments
    
    # Date range
    date_from = df['Transaction Date'].min().strftime('%Y-%m-%d')
    date_to = df['Transaction Date'].max().strftime('%Y-%m-%d')
    
    # Top categories by spending
    top_categories = []
    if 'Category' in df.columns:
        category_totals = expense_df.groupby('Category')['Amount'].sum().abs().sort_values(ascending=False)
        
        category_colors = {
            'Food': '#FF6384',
            'Shopping': '#36A2EB',
            'Transportation': '#FFCE56',
            'Utilities': '#4BC0C0',
            'Healthcare': '#9966FF',
            'Entertainment': '#FF9F40',
            'Investments': '#2196F3',
            'Money Transfer': '#607D8B',
            'Housing': '#8BC34A',
            'Education': '#9C27B0',
            'LIC/Insurance': '#00BCD4',
            'Other': '#795548'
        }
        
        category_icons = {
            'Food': '🍔',
            'Shopping': '🛒',
            'Transportation': '🚗',
            'Utilities': '💡',
            'Healthcare': '🏥',
            'Entertainment': '🎬',
            'Investments': '💎',
            'Money Transfer': '🏦',
            'Housing': '🏠',
            'Education': '📚',
            'LIC/Insurance': '🛡️',
            'Other': '📦'
        }
        
        for cat, amount in category_totals.head(8).items():
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            top_categories.append({
                'name': cat,
                'amount': float(amount),
                'percentage': float(percentage),
                'icon': category_icons.get(cat, '📊'),
                'color': category_colors.get(cat, '#667eea')
            })
    
    # Monthly trend data - return ALL months in the data
    # Exclude investments from expenses for consistency with summary cards
    df['Month'] = df['Transaction Date'].dt.to_period('M')
    monthly_income = income_df.groupby(income_df['Transaction Date'].dt.to_period('M'))['Amount'].sum()
    
    # Get non-investment expenses for monthly chart
    non_investment_expense_df = expense_df[~investment_mask] if 'Category' in expense_df.columns else expense_df
    monthly_expenses = non_investment_expense_df.groupby(non_investment_expense_df['Transaction Date'].dt.to_period('M'))['Amount'].sum().abs()
    
    monthly_trend = []
    all_months = sorted(set(monthly_income.index) | set(monthly_expenses.index))
    for month in all_months:  # ALL months, not just last 6
        monthly_trend.append({
            'month': str(month),
            'income': float(monthly_income.get(month, 0)),
            'expenses': float(monthly_expenses.get(month, 0))
        })
    
    return {
        'totalIncome': total_income,
        'totalExpenses': actual_expenses,
        'totalInvestments': total_investments,
        'netSavings': total_income - actual_expenses,
        'transactionCount': len(df),
        'dateRange': {
            'from': date_from,
            'to': date_to
        },
        'topCategories': top_categories,
        'monthlyTrend': monthly_trend
    }


@router.get("/quick-stats")
async def get_quick_stats() -> Dict[str, Any]:
    """Get quick statistics for the dashboard"""
    
    df = load_transaction_data()
    
    if df is None or df.empty:
        return {
            'transactionCount': 0,
            'avgDailyExpense': 0,
            'savingsRate': 0,
            'monthsOfData': 0
        }
    
    income_df = df[df['Amount'] > 0]
    expense_df = df[df['Amount'] < 0]
    
    total_income = income_df['Amount'].sum()
    total_expenses = abs(expense_df['Amount'].sum())
    
    # Calculate months of data
    date_range = (df['Transaction Date'].max() - df['Transaction Date'].min()).days
    months_of_data = max(1, date_range // 30)
    
    # Average daily expense
    avg_daily_expense = total_expenses / max(1, date_range)
    
    # Savings rate
    savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
    
    return {
        'transactionCount': len(df),
        'avgDailyExpense': float(avg_daily_expense),
        'savingsRate': float(savings_rate),
        'monthsOfData': months_of_data
    }
