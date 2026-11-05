"""
Dashboard API endpoints for Family Finance Tracker
Provides summary statistics and analytics for the dashboard view
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

from .account_filters import filter_by_account

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SRC')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from categories import categorize_transaction
from refined_categories import get_category_group
from data_extraction import get_processed_data_path as get_canonical_processed_data_path


def get_processed_data_path() -> Optional[str]:
    """Return the single generated dataset path used by the upload pipeline."""
    path = get_canonical_processed_data_path()
    return path if os.path.exists(path) else None


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
        if 'Description' not in df.columns:
            df['Description'] = ''

        if 'Category' not in df.columns:
            df['Category'] = ''
        if 'Subcategory' not in df.columns:
            df['Subcategory'] = ''

        missing = df['Category'].isna() | df['Category'].astype(str).str.strip().eq('')
        for index in df.index[missing]:
            result = categorize_transaction(str(df.at[index, 'Description']), float(df.at[index, 'Amount']))
            df.at[index, 'Category'] = result['category']
            df.at[index, 'Subcategory'] = result['subcategory']

        missing_subcategories = df['Subcategory'].isna() | df['Subcategory'].astype(str).str.strip().eq('')
        for index in df.index[missing_subcategories]:
            result = categorize_transaction(str(df.at[index, 'Description']), float(df.at[index, 'Amount']))
            df.at[index, 'Subcategory'] = result['subcategory']
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


def _months_covered(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> float:
    dates = df['Transaction Date'].dropna()
    if dates.empty and not (start_date and end_date):
        return 1
    first = pd.to_datetime(start_date) if start_date else dates.min()
    last = pd.to_datetime(end_date) if end_date else dates.max()
    months_between = (last.year - first.year) * 12 + last.month - first.month
    if start_date and end_date:
        if months_between == 0:
            return max(1 / first.days_in_month, (last.day - first.day + 1) / first.days_in_month)
        return (
            (first.days_in_month - first.day + 1) / first.days_in_month
            + months_between - 1
            + last.day / last.days_in_month
        )
    return float(max(1, months_between + 1))


@router.get("/health")
async def dashboard_health():
    """Health check for dashboard API"""
    return {
        "status": "healthy",
        "service": "Dashboard API",
        "version": "1.0.0"
    }


@router.get("/summary")
async def get_dashboard_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account: Optional[str] = None
) -> Dict[str, Any]:
    """Get comprehensive dashboard summary with all financial metrics"""
    
    df = load_transaction_data()
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No transaction data found. Please upload a bank statement.")

    df = filter_by_account(df, account)
    if start_date:
        df = df[df['Transaction Date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Transaction Date'] < pd.to_datetime(end_date) + pd.Timedelta(days=1)]
    if df.empty:
        return {
            'totalIncome': 0.0,
            'totalExpenses': 0.0,
            'totalInvestments': 0.0,
            'totalPlanned': 0.0,
            'totalTransfers': 0.0,
            'netSavings': 0.0,
            'transactionCount': 0,
            'monthsCovered': _months_covered(df, start_date, end_date),
            'dateRange': {'from': start_date or '', 'to': end_date or ''},
            'topCategories': [],
            'monthlyTrend': []
        }

    months_covered = _months_covered(df, start_date, end_date)
    
    # Calculate basic metrics
    income_mask = (
        df['Amount'].gt(0)
        & df['Category'].map(get_category_group).eq('Income')
    )
    income_df = df[income_mask]
    expense_df = df[df['Amount'] < 0]
    
    total_income = float(income_df['Amount'].sum())
    expense_groups = expense_df['Category'].map(get_category_group)
    expense_category_df = expense_df[expense_groups.eq('Expense')]
    investment_df = expense_df[expense_groups.eq('Investment')]
    planned_df = expense_df[expense_groups.eq('Planned')]
    transfer_df = df[df['Category'].map(get_category_group).eq('Transfer')]
    actual_expenses = float(abs(expense_category_df['Amount'].sum()))
    total_investments = float(abs(investment_df['Amount'].sum()))
    total_planned = float(abs(planned_df['Amount'].sum()))
    total_transfers = float(transfer_df['Amount'].abs().sum())
    
    # Date range
    date_from = df['Transaction Date'].min().strftime('%Y-%m-%d')
    date_to = df['Transaction Date'].max().strftime('%Y-%m-%d')
    
    # Top categories by spending
    top_categories = []
    if not expense_category_df.empty:
        category_totals = expense_category_df.groupby('Category')['Amount'].sum().abs().sort_values(ascending=False)
        category_spending_total = float(category_totals.sum())
        
        category_colors = {
            'Food': '#FF6384',
            'Food & Dining': '#FF6384',
            'Shopping': '#36A2EB',
            'Transportation': '#FFCE56',
            'Travel': '#5C6BC0',
            'Telecom': '#26A69A',
            'Utilities': '#4BC0C0',
            'Healthcare': '#9966FF',
            'Entertainment': '#FF9F40',
            'Investments': '#2196F3',
            'Money Transfer': '#607D8B',
            'Individual Transfers': '#78909C',
            'Subscriptions': '#AB47BC',
            'Insurance': '#00BCD4',
            'Housing': '#8BC34A',
            'Education': '#9C27B0',
            'LIC/Insurance': '#00BCD4',
            'Loans & EMI': '#E91E63', 'Taxes & Government': '#455A64', 'Donations & Charity': '#FF7043', 'Personal Care': '#F06292', 'Cash & ATM': '#90A4AE', 'Other': '#795548'
        }
        
        category_icons = {
            'Food': '🍔',
            'Food & Dining': '🍔',
            'Shopping': '🛒',
            'Transportation': '🚗',
            'Travel': '🧳',
            'Telecom': '📱',
            'Utilities': '💡',
            'Healthcare': '🏥',
            'Entertainment': '🎬',
            'Investments': '💎',
            'Money Transfer': '🏦',
            'Individual Transfers': '👤',
            'Subscriptions': '🔄',
            'Insurance': '🛡️',
            'Housing': '🏠',
            'Education': '📚',
            'LIC/Insurance': '🛡️',
            'Loans & EMI': '🏦', 'Taxes & Government': '🏛️', 'Donations & Charity': '🙏', 'Personal Care': '💇', 'Cash & ATM': '🏧', 'Other': '📦'
        }
        
        for cat, amount in category_totals.head(8).items():
            percentage = (amount / category_spending_total * 100) if category_spending_total > 0 else 0
            top_categories.append({
                'name': cat,
                'amount': float(amount),
                'averageMonthlyAmount': float(amount / months_covered),
                'percentage': float(percentage),
                'icon': category_icons.get(cat, '📊'),
                'color': category_colors.get(cat, '#667eea')
            })
    
    # Monthly trend data - return ALL months in the data
    # Exclude investments from expenses for consistency with summary cards
    df['Month'] = df['Transaction Date'].dt.to_period('M')
    monthly_income = income_df.groupby(income_df['Transaction Date'].dt.to_period('M'))['Amount'].sum()
    
    # Get non-investment expenses for monthly chart
    non_investment_expense_df = expense_df[
        expense_df['Category'].map(get_category_group).eq('Expense')
    ]
    monthly_expenses = non_investment_expense_df.groupby(non_investment_expense_df['Transaction Date'].dt.to_period('M'))['Amount'].sum().abs()
    monthly_investments = investment_df.groupby(investment_df['Transaction Date'].dt.to_period('M'))['Amount'].sum().abs()
    monthly_planned = planned_df.groupby(planned_df['Transaction Date'].dt.to_period('M'))['Amount'].sum().abs()
    monthly_transfers = transfer_df.assign(
        Amount=transfer_df['Amount'].abs()
    ).groupby(transfer_df['Transaction Date'].dt.to_period('M'))['Amount'].sum()
    
    monthly_trend = []
    all_months = sorted(
        set(monthly_income.index)
        | set(monthly_expenses.index)
        | set(monthly_investments.index)
        | set(monthly_planned.index)
        | set(monthly_transfers.index)
    )
    for month in all_months:  # ALL months, not just last 6
        monthly_trend.append({
            'month': str(month),
            'income': float(monthly_income.get(month, 0)),
            'expenses': float(monthly_expenses.get(month, 0)),
            'investments': float(monthly_investments.get(month, 0)),
            'planned': float(monthly_planned.get(month, 0)),
            'transfers': float(monthly_transfers.get(month, 0))
        })
    
    return {
        'totalIncome': total_income,
        'totalExpenses': actual_expenses,
        'totalInvestments': total_investments,
        'totalPlanned': total_planned,
        'totalTransfers': total_transfers,
        'netSavings': total_income - actual_expenses,
        'transactionCount': len(df),
        'monthsCovered': months_covered,
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
    
    income_mask = (
        df['Amount'].gt(0)
        & df['Category'].map(get_category_group).eq('Income')
    )
    income_df = df[income_mask]
    expense_df = df[df['Amount'] < 0]
    
    total_income = income_df['Amount'].sum()
    expense_groups = expense_df['Category'].map(get_category_group)
    actual_expense_df = expense_df[expense_groups.eq('Expense')]
    total_expenses = abs(actual_expense_df['Amount'].sum())
    
    # Calculate months of data
    first_date = df['Transaction Date'].min()
    last_date = df['Transaction Date'].max()
    date_range = max(1, (last_date - first_date).days + 1)
    months_of_data = max(
        1,
        (last_date.year - first_date.year) * 12 + last_date.month - first_date.month + 1
    )
    
    # Average daily expense
    avg_daily_expense = total_expenses / date_range
    
    # Savings rate
    savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0
    
    return {
        'transactionCount': len(df),
        'avgDailyExpense': float(avg_daily_expense),
        'savingsRate': float(savings_rate),
        'monthsOfData': months_of_data
    }
