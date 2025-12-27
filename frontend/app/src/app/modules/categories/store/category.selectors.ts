import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CategoryState } from './category.reducer';

export const selectCategoryState = createFeatureSelector<CategoryState>('categories');

export const selectAllCategories = createSelector(
  selectCategoryState,
  (state) => state.analytics
);

export const selectSelectedCategories = createSelector(
  selectCategoryState,
  (state) => state.selectedCategories
);

export const selectFilteredCategories = createSelector(
  selectAllCategories,
  selectSelectedCategories,
  (analytics, selectedIds) => analytics.filter(category => 
    selectedIds.includes(category.categoryId)
  )
);

export const selectDateRange = createSelector(
  selectCategoryState,
  (state) => state.selectedDateRange
);

export const selectDisplayMode = createSelector(
  selectCategoryState,
  (state) => state.displayMode
);

export const selectChartType = createSelector(
  selectCategoryState,
  (state) => state.chartType
);

export const selectShowComparison = createSelector(
  selectCategoryState,
  (state) => state.showComparison
);

export const selectLoading = createSelector(
  selectCategoryState,
  (state) => state.loading
);

export const selectError = createSelector(
  selectCategoryState,
  (state) => state.error
);

export const selectCategorySummary = createSelector(
  selectAllCategories,
  (analytics) => {
    const income = analytics.find(c => c.categoryId === 'income')?.monthlyAmount || 0;
    const expenditure = analytics.find(c => c.categoryId === 'expenditure')?.monthlyAmount || 0;
    const investment = analytics.find(c => c.categoryId === 'investment')?.monthlyAmount || 0;
    const education = analytics.find(c => c.categoryId === 'education')?.monthlyAmount || 0;
    const transfers = analytics.find(c => c.categoryId === 'transfers')?.monthlyAmount || 0;
    
    const netSavings = income - expenditure;
    const savingsRate = income > 0 ? (netSavings / income) * 100 : 0;
    
    return {
      totalIncome: income,
      totalExpenditure: expenditure,
      totalInvestment: investment,
      totalEducation: education,
      totalTransfers: transfers,
      savingsRate,
      netSavings
    };
  }
);

export const selectChartData = createSelector(
  selectFilteredCategories,
  selectDisplayMode,
  (analytics, displayMode) => analytics.map(category => ({
    label: category.categoryName,
    value: displayMode === 'amount' ? category.monthlyAmount : category.percentageOfIncome,
    color: category.color,
    displayValue: displayMode === 'amount' 
      ? category.monthlyAmount 
      : category.percentageOfIncome,
    formattedValue: displayMode === 'amount'
      ? `₹${category.monthlyAmount.toLocaleString()}`
      : `${category.percentageOfIncome.toFixed(1)}%`,
    tooltipText: displayMode === 'amount'
      ? `Monthly Average: ₹${category.monthlyAmount.toLocaleString()}`
      : `${category.percentageOfIncome.toFixed(1)}% of total income`
  }))
);
