"""
Analysis module for Personal Finance Tracker.
This module provides functions for analyzing transaction data.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Use try/except to handle both relative and absolute imports
try:
    from .categories import categorize_transaction
    from .enhanced_categories import categorize_transaction_enhanced, analyze_categorization_quality
except ImportError:
    from categories import categorize_transaction
    from enhanced_categories import categorize_transaction_enhanced, analyze_categorization_quality


def calculate_summary_statistics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate basic summary statistics for transactions.
    
    Args:
        df (pd.DataFrame): DataFrame with transaction data
    
    Returns:
        Dict[str, float]: Summary statistics including total transactions, income, expenses, and average
    
    Raises:
        ValueError: If DataFrame is empty or missing required columns
    """
    try:
        if df is None or df.empty:
            return {
                'total_transactions': 0.0,
                'total_income': 0.0,
                'total_expenses': 0.0,
                'avg_transaction': 0.0,
                'net_cash_flow': 0.0,
                'savings_rate': 0.0
            }
        
        required_columns = ['Amount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"DataFrame must contain columns: {missing_columns}")
        
        total_transactions = len(df)
        total_income = df[df['Amount'] > 0]['Amount'].sum()
        total_expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
        avg_transaction = abs(df['Amount']).mean() if total_transactions > 0 else 0.0
        net_cash_flow = total_income - total_expenses
        savings_rate = (net_cash_flow / total_income * 100) if total_income > 0 else 0.0
        
        return {
            'total_transactions': float(total_transactions),
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'avg_transaction': float(avg_transaction),
            'net_cash_flow': float(net_cash_flow),
            'savings_rate': float(savings_rate)
        }
    except Exception as e:
        raise ValueError(f"Error calculating summary statistics: {str(e)}")


def get_top_merchants(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """
    Get the top merchants by total spend.
    
    Args:
        df (pd.DataFrame): DataFrame with transaction data
        limit (int): Number of merchants to return
    
    Returns:
        pd.DataFrame: Top merchants with their total spend
    
    Raises:
        ValueError: If DataFrame is empty or missing required columns
    """
    try:
        if df is None or df.empty:
            return pd.DataFrame(columns=['Description', 'Transaction Count', 'Total Spend'])
        
        required_columns = ['Amount', 'Description']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"DataFrame must contain columns: {missing_columns}")
        
        # Only consider expenses (negative amounts)
        expenses = df[df['Amount'] < 0].copy()
        if expenses.empty:
            return pd.DataFrame(columns=['Description', 'Transaction Count', 'Total Spend'])
        
        # Clean and normalize merchant names
        expenses['Description'] = expenses['Description'].str.strip().str.upper()
        
        # Group by description and calculate total spend
        merchants = (expenses.groupby('Description')
                    .agg(
                        Transaction_Count=('Amount', 'count'),
                        Total_Spend=('Amount', 'sum')
                    )
                    .reset_index())
        
        # Rename columns to match visualization module expectations
        merchants = merchants.rename(columns={
            'Transaction_Count': 'Transaction Count',
            'Total_Spend': 'Total Spend'
        })
        
        # Sort by total spend (absolute value) and get top merchants
        merchants['Total Spend'] = merchants['Total Spend'].abs()
        merchants = merchants.sort_values('Total Spend', ascending=False).head(limit)
        
        return merchants.reset_index(drop=True)
        
    except Exception as e:
        raise ValueError(f"Error analyzing top merchants: {str(e)}")


def calculate_inflow_outflow(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calculate monthly inflow and outflow of money.
    
    Args:
        df (pd.DataFrame): DataFrame with transaction data
    
    Returns:
        Dict[str, Dict[str, float]]: Monthly inflow/outflow data
    
    Raises:
        ValueError: If DataFrame is empty or missing required columns
    """
    try:
        if df is None or df.empty:
            return {}
        
        required_columns = ['Amount', 'Transaction Date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"DataFrame must contain columns: {missing_columns}")
        
        # Filter out rows with missing or invalid dates
        df_clean = df[df['Transaction Date'].notna()].copy()
        if df_clean.empty:
            return {}
        
        # Create month column
        df_clean['Month'] = df_clean['Transaction Date'].dt.strftime('%Y-%m')
        
        # Calculate inflow and outflow for each month
        monthly: Dict[str, Dict[str, float]] = {}
        
        for month in sorted(df_clean['Month'].unique()):
            if not isinstance(month, str) or not month:
                continue
                
            month_data = df_clean[df_clean['Month'] == month]
            inflow = float(month_data[month_data['Amount'] > 0]['Amount'].sum())
            outflow = float(abs(month_data[month_data['Amount'] < 0]['Amount'].sum()))
            
            monthly[month] = {
                'inflow': inflow,
                'outflow': outflow,
                'net': inflow - outflow
            }
        
        return monthly
        
    except Exception as e:
        raise ValueError(f"Error calculating inflow/outflow: {str(e)}")


def calculate_weekly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate weekly spending statistics.
    
    Args:
        df (pd.DataFrame): DataFrame with transaction data
    
    Returns:
        pd.DataFrame: Weekly statistics
    
    Raises:
        ValueError: If DataFrame is empty or missing required columns
    """
    try:
        if df is None or df.empty:
            return pd.DataFrame(columns=['Week', 'Total Income', 'Total Expenses', 'Transaction Count', 'Net Amount'])
        
        required_columns = ['Amount', 'Transaction Date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"DataFrame must contain columns: {missing_columns}")
        
        # Filter out rows with missing dates
        df_clean = df[df['Transaction Date'].notna()].copy()
        if df_clean.empty:
            return pd.DataFrame(columns=['Week', 'Total Income', 'Total Expenses', 'Transaction Count', 'Net Amount'])
        
        # Create week column
        df_clean['Week'] = df_clean['Transaction Date'].dt.strftime('%Y-%U')
        
        # Calculate weekly statistics
        weekly_stats = (df_clean.groupby('Week')
                       .agg(
                           **{
                               'Total Income': ('Amount', lambda x: x[x > 0].sum()),
                               'Total Expenses': ('Amount', lambda x: abs(x[x < 0].sum())),
                               'Transaction Count': ('Amount', 'count')
                           }
                       )
                       .reset_index())
        
        # Add net amount
        weekly_stats['Net Amount'] = weekly_stats['Total Income'] - weekly_stats['Total Expenses']
        
        return weekly_stats.sort_values('Week')
        
    except Exception as e:
        raise ValueError(f"Error calculating weekly statistics: {str(e)}")


def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize transactions and add category information.
    
    Args:
        df (pd.DataFrame): DataFrame with transaction data
    
    Returns:
        pd.DataFrame: DataFrame with added category columns
    
    Raises:
        ValueError: If DataFrame is empty or missing required columns
    """
    try:
        if df is None or df.empty:
            return df
        
        required_columns = ['Amount', 'Description']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"DataFrame must contain columns: {missing_columns}")
        
        # Create a copy to avoid modifying the original
        categorized = df.copy()
        
        # Apply enhanced categorization to each transaction
        categories = []
        subcategories = []
        
        for _, row in categorized.iterrows():
            try:
                # Use enhanced categorization
                result = categorize_transaction_enhanced(row['Description'], row['Amount'])
                categories.append(result['category'])
                subcategories.append(result['subcategory'])
            except Exception:
                # Fallback to original categorization if error occurs
                try:
                    result = categorize_transaction(row['Description'], row['Amount'])
                    categories.append(result['category'])
                    subcategories.append(result['subcategory'])
                except Exception:
                    # Use default categorization if both fail
                    categories.append('Other')
                    subcategories.append('Uncategorized')
        
        categorized['Category'] = categories
        categorized['Subcategory'] = subcategories
        
        return categorized
        
    except Exception as e:
        raise ValueError(f"Error categorizing transactions: {str(e)}")


def calculate_category_summary(df: pd.DataFrame, include_income: bool = False) -> pd.DataFrame:
    """
    Calculate spending summary by category.
    
    Args:
        df (pd.DataFrame): DataFrame with categorized transactions
        include_income (bool): Whether to include income categories. Default is False.
    
    Returns:
        pd.DataFrame: Category summary statistics
    
    Raises:
        ValueError: If DataFrame is empty or missing required columns
    """
    try:
        if df is None or df.empty:
            return pd.DataFrame(columns=['Category', 'Total_Amount', 'Transaction_Count', 'Avg_Amount'])
        
        required_columns = ['Amount', 'Category']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"DataFrame must contain columns: {missing_columns}")
        
        # Filter data based on include_income parameter
        if include_income:
            filtered_df = df.copy()
        else:
            filtered_df = df[df['Amount'] < 0].copy()
        
        if filtered_df.empty:
            return pd.DataFrame(columns=['Category', 'Total_Amount', 'Transaction_Count', 'Avg_Amount'])
        
        # Group by category and calculate statistics
        category_summary = (filtered_df.groupby('Category')
                           .agg(
                               Total_Amount=('Amount', lambda x: abs(x.sum())),
                               Transaction_Count=('Amount', 'count'),
                               Avg_Amount=('Amount', lambda x: abs(x.mean()))
                           )
                           .reset_index())
        
        # Sort by total amount descending
        category_summary = category_summary.sort_values('Total_Amount', ascending=False)
        
        return category_summary.reset_index(drop=True)
        
    except Exception as e:
        raise ValueError(f"Error calculating category summary: {str(e)}")


def calculate_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate various financial trends from the transaction data.
    
    Args:
        df (pd.DataFrame): DataFrame with transaction data
    
    Returns:
        Dict[str, Any]: Dictionary containing various trend metrics
    """
    try:
        if df is None or df.empty:
            return {
                'monthly_trend': {},
                'spending_growth': 0.0,
                'income_growth': 0.0,
                'savings_trend': {},
                'category_trends': {}
            }
        
        required_columns = ['Amount', 'Transaction Date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"DataFrame must contain columns: {missing_columns}")
        
        # Filter out invalid dates
        df_clean = df[df['Transaction Date'].notna()].copy()
        if df_clean.empty:
            return {
                'monthly_trend': {},
                'spending_growth': 0.0,
                'income_growth': 0.0,
                'savings_trend': {},
                'category_trends': {}
            }
        
        # Calculate monthly trends
        df_clean['Month'] = df_clean['Transaction Date'].dt.strftime('%Y-%m')
        monthly_summary = df_clean.groupby('Month').agg(
            Income=('Amount', lambda x: x[x > 0].sum()),
            Expenses=('Amount', lambda x: abs(x[x < 0].sum())),
            Net=('Amount', lambda x: x.sum())
        ).reset_index()
        
        # Column names are already correct now
        monthly_summary = monthly_summary.sort_values('Month')
        
        # Calculate growth rates
        spending_growth = 0.0
        income_growth = 0.0
        
        if len(monthly_summary) >= 2:
            first_month = monthly_summary.iloc[0]
            last_month = monthly_summary.iloc[-1]
            
            if first_month['Expenses'] > 0:
                spending_growth = ((last_month['Expenses'] - first_month['Expenses']) / first_month['Expenses']) * 100
            
            if first_month['Income'] > 0:
                income_growth = ((last_month['Income'] - first_month['Income']) / first_month['Income']) * 100
        
        # Calculate savings trend
        savings_trend = {}
        for _, row in monthly_summary.iterrows():
            savings_rate = (row['Net'] / row['Income'] * 100) if row['Income'] > 0 else 0
            savings_trend[row['Month']] = savings_rate
        
        # Calculate category trends (if categories exist)
        category_trends = {}
        if 'Category' in df_clean.columns:
            category_monthly = df_clean[df_clean['Amount'] < 0].groupby(['Month', 'Category'])['Amount'].sum().abs().reset_index()
            for category in category_monthly['Category'].unique():
                cat_data = category_monthly[category_monthly['Category'] == category]
                if len(cat_data) >= 2:
                    first_amount = cat_data.iloc[0]['Amount']
                    last_amount = cat_data.iloc[-1]['Amount']
                    growth = ((last_amount - first_amount) / first_amount * 100) if first_amount > 0 else 0
                    category_trends[category] = growth
        
        return {
            'monthly_trend': monthly_summary.to_dict('records'),
            'spending_growth': float(round(spending_growth, 2)),
            'income_growth': float(round(income_growth, 2)),
            'savings_trend': savings_trend,
            'category_trends': category_trends
        }
        
    except Exception as e:
        raise ValueError(f"Error calculating trends: {str(e)}")


def get_financial_health_score(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate a comprehensive financial health score based on various metrics.
    
    Args:
        df (pd.DataFrame): DataFrame with transaction data
    
    Returns:
        Dict[str, float]: Financial health metrics and overall score
    """
    try:
        if df is None or df.empty:
            return {
                'overall_score': 0.0,
                'savings_score': 0.0,
                'spending_consistency': 0.0,
                'category_diversification': 0.0,
                'emergency_fund_ratio': 0.0
            }
        
        summary = calculate_summary_statistics(df)
        
        # Calculate savings score (0-100 based on savings rate)
        savings_rate = summary['savings_rate']
        savings_score = min(max(savings_rate * 2, 0), 100)  # 50% savings = 100 score
        
        # Calculate spending consistency (lower variance = higher score)
        monthly_expenses = []
        df_clean = df[df['Transaction Date'].notna()].copy()
        df_clean['Month'] = df_clean['Transaction Date'].dt.strftime('%Y-%m')
        
        for month in df_clean['Month'].unique():
            month_expenses = abs(df_clean[(df_clean['Month'] == month) & (df_clean['Amount'] < 0)]['Amount'].sum())
            monthly_expenses.append(month_expenses)
        
        if len(monthly_expenses) > 1:
            cv = np.std(monthly_expenses) / np.mean(monthly_expenses) if np.mean(monthly_expenses) > 0 else 1
            spending_consistency = max(100 - (cv * 100), 0)
        else:
            spending_consistency = 50.0
        
        # Calculate category diversification
        if 'Category' in df.columns:
            expense_categories = df[df['Amount'] < 0]['Category'].nunique()
            category_diversification = min(expense_categories * 10, 100)  # Max 10 categories for full score
        else:
            category_diversification = 50.0
        
        # Calculate emergency fund ratio (simplified - based on monthly surplus)
        emergency_fund_ratio = min(max(savings_rate, 0), 50) * 2  # 25% surplus = 100 score
        
        # Overall score (weighted average)
        overall_score = (
            savings_score * 0.4 +
            spending_consistency * 0.2 +
            category_diversification * 0.2 +
            emergency_fund_ratio * 0.2
        )
        
        return {
            'overall_score': float(round(overall_score, 1)),
            'savings_score': float(round(savings_score, 1)),
            'spending_consistency': float(round(spending_consistency, 1)),
            'category_diversification': float(round(category_diversification, 1)),
            'emergency_fund_ratio': float(round(emergency_fund_ratio, 1))
        }
        
    except Exception as e:
        raise ValueError(f"Error calculating financial health score: {str(e)}")


def analyze_other_category_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze transactions in 'Other' category to identify potential miscategorizations.
    
    Args:
        df (pd.DataFrame): DataFrame with categorized transactions
        
    Returns:
        Dict with analysis results and recommendations
    """
    try:
        if df is None or df.empty:
            return {'error': 'No data provided', 'other_count': 0, 'recommendations': []}
        
        # Get transactions categorized as 'Other'
        other_transactions = df[df['Category'] == 'Other'].copy()
        
        if other_transactions.empty:
            return {
                'other_count': 0,
                'other_percentage': 0.0,
                'total_other_amount': 0.0,
                'recommendations': ['Excellent! No transactions in Other category.'],
                'sample_transactions': []
            }
        
        total_transactions = len(df)
        other_count = len(other_transactions)
        other_percentage = (other_count / total_transactions) * 100
        
        # Calculate total amount in Other category
        other_expenses = other_transactions[other_transactions['Amount'] < 0]
        total_other_amount = abs(other_expenses['Amount'].sum()) if not other_expenses.empty else 0
        
        # Get sample transactions for review
        sample_size = min(10, len(other_transactions))
        sample_transactions = other_transactions.head(sample_size)[['Description', 'Amount', 'Transaction Date']].to_dict('records')
        
        # Generate recommendations based on percentage
        recommendations = []
        if other_percentage > 20:
            recommendations.extend([
                "CRITICAL: More than 20% of transactions are uncategorized!",
                "Immediate action required to improve categorization accuracy.",
                "Review and categorize the sample transactions shown below."
            ])
        elif other_percentage > 10:
            recommendations.extend([
                "HIGH: More than 10% of transactions are uncategorized.",
                "Consider reviewing transaction descriptions and adding new keywords.",
                "Focus on recurring transactions that can be auto-categorized."
            ])
        elif other_percentage > 5:
            recommendations.extend([
                "MEDIUM: Consider reviewing uncategorized transactions.",
                "Look for patterns in transaction descriptions that can be automated."
            ])
        else:
            recommendations.append("GOOD: Low percentage of uncategorized transactions.")
        
        return {
            'other_count': other_count,
            'other_percentage': round(other_percentage, 2),
            'total_other_amount': round(total_other_amount, 2),
            'recommendations': recommendations,
            'sample_transactions': sample_transactions
        }
        
    except Exception as e:
        return {'error': f"Error analyzing Other category: {str(e)}"}


def get_expense_only_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate expense summary excluding investments, transfers, savings, and education.
    
    Args:
        df (pd.DataFrame): DataFrame with categorized transactions
        
    Returns:
        Dict with expense-only analysis for spending reduction advice
    """
    try:
        if df is None or df.empty:
            return {'error': 'No data provided', 'total_expenses': 0}
        
        # Define categories to exclude from "spending reduction" analysis
        non_expense_categories = {'Investments', 'Transfers & Payments', 'Savings', 'Education', 'Income'}
        
        # Filter for actual expenses only
        expense_transactions = df[
            (df['Amount'] < 0) & 
            (~df['Category'].isin(non_expense_categories))
        ].copy()
        
        if expense_transactions.empty:
            return {
                'total_expenses': 0,
                'category_breakdown': {},
                'top_categories': [],
                'recommendations': ['No discretionary expenses found for optimization.']
            }
        
        # Calculate absolute amounts
        expense_transactions['Amount'] = expense_transactions['Amount'].abs()
        
        # Category breakdown
        category_summary = expense_transactions.groupby('Category')['Amount'].sum().sort_values(ascending=False)
        total_expenses = category_summary.sum()
        
        category_breakdown = {}
        for category, amount in category_summary.items():
            percentage = (amount / total_expenses) * 100 if total_expenses > 0 else 0
            category_breakdown[category] = {
                'amount': round(amount, 2),
                'percentage': round(percentage, 2)
            }
        
        # Top 5 categories for spending reduction focus
        top_categories = category_summary.head(5).index.tolist()
        
        # Generate spending reduction recommendations
        recommendations = []
        if 'Expenses' in category_breakdown:
            dining_pct = category_breakdown.get('Expenses', {}).get('percentage', 0)
            if dining_pct > 25:
                recommendations.append("Consider reducing dining out expenses - they represent a significant portion of spending.")
        
        if 'Entertainment' in category_breakdown:
            entertainment_pct = category_breakdown.get('Entertainment', {}).get('percentage', 0)
            if entertainment_pct > 15:
                recommendations.append("Review entertainment subscriptions and expenses for potential savings.")
        
        if len(recommendations) == 0:
            recommendations.append("Your expense distribution looks reasonable. Focus on the top categories for optimization.")
        
        return {
            'total_expenses': round(total_expenses, 2),
            'category_breakdown': category_breakdown,
            'top_categories': top_categories,
            'recommendations': recommendations
        }
        
    except Exception as e:
        return {'error': f"Error calculating expense summary: {str(e)}"}


def generate_categorization_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive categorization quality report.
    
    Args:
        df (pd.DataFrame): DataFrame with categorized transactions
        
    Returns:
        Dict with comprehensive categorization analysis
    """
    try:
        if df is None or df.empty:
            return {'error': 'No data provided'}
        
        # Basic statistics
        total_transactions = len(df)
        
        # Category distribution
        category_counts = df['Category'].value_counts()
        category_percentages = (category_counts / total_transactions * 100).round(2)
        
        # Amount distribution by category
        expense_transactions = df[df['Amount'] < 0].copy()
        if not expense_transactions.empty:
            expense_transactions['Amount'] = expense_transactions['Amount'].abs()
            amount_by_category = expense_transactions.groupby('Category')['Amount'].sum()
            total_expense_amount = amount_by_category.sum()
            amount_percentages = (amount_by_category / total_expense_amount * 100).round(2) if total_expense_amount > 0 else pd.Series()
        else:
            amount_by_category = pd.Series()
            amount_percentages = pd.Series()
        
        # Other category analysis
        other_analysis = analyze_other_category_quality(df)
        
        # Expense-only analysis
        expense_analysis = get_expense_only_summary(df)
        
        # Overall quality score
        other_pct = other_analysis.get('other_percentage', 0)
        if other_pct <= 2:
            quality_score = 'Excellent'
        elif other_pct <= 5:
            quality_score = 'Good'
        elif other_pct <= 10:
            quality_score = 'Fair'
        else:
            quality_score = 'Poor'
        
        return {
            'total_transactions': total_transactions,
            'category_distribution': {
                'by_count': category_counts.to_dict(),
                'by_count_percentage': category_percentages.to_dict(),
                'by_amount': amount_by_category.to_dict(),
                'by_amount_percentage': amount_percentages.to_dict()
            },
            'other_category_analysis': other_analysis,
            'expense_analysis': expense_analysis,
            'quality_score': quality_score,
            'recommendations': _generate_quality_recommendations(other_pct, category_counts)
        }
        
    except Exception as e:
        return {'error': f"Error generating categorization report: {str(e)}"}


def _generate_quality_recommendations(other_percentage: float, category_counts: pd.Series) -> List[str]:
    """Generate recommendations based on categorization quality."""
    recommendations = []
    
    # Other category recommendations
    if other_percentage > 15:
        recommendations.append("URGENT: Review all 'Other' transactions and add missing categories/keywords.")
    elif other_percentage > 5:
        recommendations.append("Review 'Other' transactions and improve keyword matching.")
    
    # Category balance recommendations
    if len(category_counts) < 5:
        recommendations.append("Consider adding more specific subcategories for better expense tracking.")
    
    # Top category recommendations
    top_category = category_counts.index[0] if not category_counts.empty else None
    if top_category and category_counts[top_category] / category_counts.sum() > 0.5:
        recommendations.append(f"'{top_category}' dominates transactions. Consider splitting into subcategories.")
    
    if not recommendations:
        recommendations.append("Categorization quality looks good! Continue monitoring for improvements.")
    
    return recommendations