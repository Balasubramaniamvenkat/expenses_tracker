"""
User interaction components for handling "Other" category transactions
and learning from user feedback.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from .enhanced_categories import (
    learn_from_user_categorization,
    get_pending_other_transactions,
    get_available_categories,
    enhanced_categorizer
)


def display_other_category_review(df: pd.DataFrame) -> None:
    """
    Display interface for reviewing and categorizing "Other" transactions.
    
    Args:
        df (pd.DataFrame): DataFrame with categorized transactions
    """
    st.markdown("### 🔍 Review Uncategorized Transactions")
    
    if df is None or df.empty:
        st.info("No transaction data available for review.")
        return
    
    # Get transactions categorized as "Other"
    other_transactions = df[df['Category'] == 'Other'].copy()
    
    if other_transactions.empty:
        st.success("🎉 Excellent! All transactions are properly categorized.")
        st.balloons()
        return
    
    # Display statistics
    total_transactions = len(df)
    other_count = len(other_transactions)
    other_percentage = (other_count / total_transactions) * 100
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Uncategorized Transactions", other_count)
    with col2:
        st.metric("Percentage", f"{other_percentage:.1f}%")
    with col3:
        if other_percentage > 10:
            st.error("❌ Needs Attention")
        elif other_percentage > 5:
            st.warning("⚠️ Could Improve")
        else:
            st.success("✅ Good")
    
    # Alert if too many "Other" transactions
    if other_percentage > 15:
        st.error("🚨 **CRITICAL**: Too many uncategorized transactions! This significantly reduces the accuracy of your financial analysis.")
    elif other_percentage > 10:
        st.warning("⚠️ **WARNING**: High number of uncategorized transactions. Consider reviewing them for better insights.")
    
    # Display transactions for review
    st.markdown("#### Transactions Needing Review")
    
    # Sort by amount (highest first) for prioritization
    other_expenses = other_transactions[other_transactions['Amount'] < 0].copy()
    if not other_expenses.empty:
        other_expenses['Amount'] = other_expenses['Amount'].abs()
        other_expenses = other_expenses.sort_values('Amount', ascending=False)
        
        # Show top transactions for manual categorization
        st.markdown("**Top Uncategorized Expenses (by amount):**")
        
        # Get available categories
        available_categories = get_available_categories()
        
        # Create categorization interface for top 5 transactions
        num_to_show = min(5, len(other_expenses))
        
        with st.form("categorize_transactions"):
            st.markdown("Select appropriate categories for these transactions:")
            
            categorization_data = []
            
            for i, (_, row) in enumerate(other_expenses.head(num_to_show).iterrows()):
                st.markdown(f"**Transaction {i+1}:**")
                col1, col2, col3 = st.columns([3, 2, 2])
                
                with col1:
                    st.text(f"₹{row['Amount']:,.2f}")
                    st.caption(row['Description'])
                    st.caption(f"Date: {row.get('Transaction Date', 'N/A')}")
                
                with col2:
                    category = st.selectbox(
                        "Category",
                        options=['Skip'] + list(available_categories.keys()),
                        key=f"cat_{i}",
                        index=0
                    )
                
                with col3:
                    if category and category != 'Skip':
                        subcategory = st.selectbox(
                            "Subcategory",
                            options=available_categories[category],
                            key=f"subcat_{i}"
                        )
                    else:
                        subcategory = None
                        st.empty()
                
                categorization_data.append({
                    'index': row.name,
                    'description': row['Description'],
                    'amount': row['Amount'],
                    'category': category,
                    'subcategory': subcategory
                })
                
                st.divider()
            
            # Submit button
            submitted = st.form_submit_button("💾 Save Categorizations", use_container_width=True)
            
            if submitted:
                # Process categorizations
                successful_updates = 0
                
                for data in categorization_data:
                    if data['category'] and data['category'] != 'Skip' and data['subcategory']:
                        # Learn from user input
                        success = learn_from_user_categorization(
                            data['description'],
                            -data['amount'],  # Convert back to negative for expenses
                            data['category'],
                            data['subcategory']
                        )
                        
                        if success:
                            successful_updates += 1
                            # Update the transaction in session state if available
                            if 'data' in st.session_state and st.session_state.data is not None:
                                mask = st.session_state.data.index == data['index']
                                st.session_state.data.loc[mask, 'Category'] = data['category']
                                st.session_state.data.loc[mask, 'Subcategory'] = data['subcategory']
                
                if successful_updates > 0:
                    st.success(f"✅ Successfully updated {successful_updates} transaction(s)! The system will remember these patterns for future transactions.")
                    st.info("🔄 Refresh the page to see updated categorizations.")
                else:
                    st.warning("No transactions were updated. Please select categories for the transactions you want to categorize.")
    
    # Show remaining uncategorized transactions in a table
    if len(other_transactions) > 5:
        st.markdown("#### All Uncategorized Transactions")
        
        # Prepare display dataframe
        display_df = other_transactions[['Transaction Date', 'Description', 'Amount']].copy()
        display_df['Amount'] = display_df['Amount'].apply(lambda x: f"₹{abs(x):,.2f}")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=300
        )
        
        st.caption(f"Showing all {len(other_transactions)} uncategorized transactions. Focus on the highest amounts first.")


def display_categorization_tips() -> None:
    """Display tips for better transaction categorization."""
    
    with st.expander("💡 Tips for Better Categorization"):
        st.markdown("""
        **How to Improve Categorization:**
        
        1. **Start with High-Value Transactions**: Focus on categorizing your largest expenses first for maximum impact.
        
        2. **Look for Patterns**: 
           - Recurring transactions (monthly bills, subscriptions)
           - Similar merchant names
           - Common transaction types
        
        3. **Use Specific Categories**:
           - **Expenses**: Daily living costs (groceries, dining, utilities, healthcare)
           - **Investments**: Mutual funds, stocks, gold, fixed deposits
           - **Education**: School fees, courses, books, training
           - **Transfers & Payments**: Bank transfers, loan EMIs, rent, family transfers
           - **Savings**: Transfers to savings accounts, emergency funds
        
        4. **Avoid "Other" Category**: Only use this when a transaction truly doesn't fit anywhere else.
        
        5. **The System Learns**: Once you categorize similar transactions, the system will automatically categorize future similar transactions.
        
        **Priority Categories for Manual Review:**
        - Large amounts that significantly impact your financial picture
        - Recurring monthly transactions
        - Transactions with unclear or abbreviated descriptions
        """)


def display_categorization_quality_dashboard(df: pd.DataFrame) -> None:
    """
    Display a dashboard showing categorization quality metrics.
    
    Args:
        df (pd.DataFrame): DataFrame with categorized transactions
    """
    if df is None or df.empty:
        return
    
    st.markdown("### 📊 Categorization Quality Dashboard")
    
    # Calculate quality metrics
    total_transactions = len(df)
    category_counts = df['Category'].value_counts()
    other_count = category_counts.get('Other', 0)
    other_percentage = (other_count / total_transactions) * 100
    
    # Quality score
    if other_percentage <= 2:
        quality_score = "Excellent ⭐⭐⭐⭐⭐"
        score_color = "green"
    elif other_percentage <= 5:
        quality_score = "Good ⭐⭐⭐⭐"
        score_color = "blue"
    elif other_percentage <= 10:
        quality_score = "Fair ⭐⭐⭐"
        score_color = "orange"
    else:
        quality_score = "Needs Improvement ⭐⭐"
        score_color = "red"
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Transactions", f"{total_transactions:,}")
    
    with col2:
        st.metric("Categorized", f"{total_transactions - other_count:,}")
    
    with col3:
        st.metric("Uncategorized", other_count, delta=f"-{other_percentage:.1f}%")
    
    with col4:
        st.markdown(f"**Quality Score**")
        st.markdown(f"<span style='color: {score_color}; font-size: 1.2em;'>{quality_score}</span>", 
                   unsafe_allow_html=True)
    
    # Category distribution chart
    if len(category_counts) > 1:
        st.markdown("#### Category Distribution")
        
        # Create pie chart data
        chart_data = category_counts.to_dict()
        
        # Highlight "Other" category if it exists
        colors = []
        for category in chart_data.keys():
            if category == 'Other':
                colors.append('#ff4444')  # Red for Other
            else:
                colors.append(None)  # Default color
        
        # Simple bar chart showing category distribution
        st.bar_chart(category_counts)
        
        # Show percentage breakdown
        st.markdown("**Percentage Breakdown:**")
        for category, count in category_counts.items():
            percentage = (count / total_transactions) * 100
            if category == 'Other' and percentage > 5:
                st.markdown(f"- 🔴 **{category}**: {percentage:.1f}% ({count:,} transactions)")
            else:
                st.markdown(f"- ✅ **{category}**: {percentage:.1f}% ({count:,} transactions)")


def display_learning_progress() -> None:
    """Display information about the system's learning progress."""
    
    st.markdown("### 🧠 System Learning Progress")
    
    try:
        # Check if user mappings exist
        user_mappings = enhanced_categorizer.user_mappings
        
        exact_matches = len(user_mappings.get('exact_matches', {}))
        keyword_mappings = len(user_mappings.get('keywords', {}))
        
        if exact_matches == 0 and keyword_mappings == 0:
            st.info("📚 The system hasn't learned any custom patterns yet. Start categorizing transactions to build intelligence!")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Exact Transaction Patterns", exact_matches)
                st.caption("Specific transactions the system has learned")
            
            with col2:
                st.metric("Keyword Patterns", keyword_mappings)
                st.caption("Keywords learned from your categorizations")
            
            st.success(f"🎓 The system has learned {exact_matches + keyword_mappings} patterns from your input and will automatically categorize similar future transactions!")
            
            # Show some examples if available
            if exact_matches > 0:
                with st.expander("📋 View Learned Patterns"):
                    st.markdown("**Recent exact matches learned:**")
                    for desc, mapping in list(user_mappings.get('exact_matches', {}).items())[:5]:
                        st.markdown(f"- `{desc[:50]}...` → **{mapping['category']}** / {mapping['subcategory']}")
                    
                    if keyword_mappings > 0:
                        st.markdown("**Keywords learned:**")
                        for keyword, mapping in list(user_mappings.get('keywords', {}).items())[:5]:
                            st.markdown(f"- `{keyword}` → **{mapping['category']}** / {mapping['subcategory']}")
    
    except Exception as e:
        st.error(f"Error displaying learning progress: {e}")


def show_category_management_sidebar():
    """Show category management options in sidebar."""
    
    with st.sidebar:
        st.markdown("### 🏷️ Category Management")
        
        # Quick stats
        if 'data' in st.session_state and st.session_state.data is not None:
            df = st.session_state.data
            other_count = len(df[df['Category'] == 'Other'])
            total_count = len(df)
            other_pct = (other_count / total_count) * 100
            
            if other_count > 0:
                st.warning(f"⚠️ {other_count} uncategorized transactions ({other_pct:.1f}%)")
                
                if st.button("🔍 Review Now", use_container_width=True):
                    st.session_state.show_review = True
            else:
                st.success("✅ All transactions categorized!")
        
        # Learning progress
        try:
            user_mappings = enhanced_categorizer.user_mappings
            learned_patterns = len(user_mappings.get('exact_matches', {})) + len(user_mappings.get('keywords', {}))
            
            if learned_patterns > 0:
                st.metric("🧠 Learned Patterns", learned_patterns)
        except:
            pass
        
        # Reset learning (for testing)
        if st.button("🔄 Reset Learning", help="Clear all learned patterns (for testing)"):
            try:
                enhanced_categorizer.user_mappings = {'keywords': {}, 'patterns': {}, 'exact_matches': {}}
                enhanced_categorizer._save_user_mappings()
                st.success("Learning data reset!")
                st.rerun()
            except Exception as e:
                st.error(f"Error resetting: {e}")
