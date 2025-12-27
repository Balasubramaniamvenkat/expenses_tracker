import { createReducer, on } from '@ngrx/store';
import { CategoryAnalytics, DateRange } from '../models/category.model';
import { ChartConfig } from '../models/chart-config.model';
import { CategoryActions } from './category.actions';

export interface CategoryState {
  analytics: CategoryAnalytics[];
  selectedDateRange: DateRange;
  selectedCategories: string[];
  chartConfigs: ChartConfig[];
  displayMode: 'amount' | 'percentage';
  chartType: 'donut' | 'sunburst' | 'bar' | 'line' | 'scatter';
  showComparison: boolean;
  loading: boolean;
  error: string | null;
  // Enhanced chart state
  chartData: any | null;
  chartOptions: any | null;
  chartInitialized: boolean;
}

export const initialState: CategoryState = {
  analytics: [],
  selectedDateRange: {
    startDate: new Date(new Date().getFullYear(), new Date().getMonth() - 5, 1), // Last 6 months
    endDate: new Date()
  },
  selectedCategories: ['income', 'expenditure', 'investment', 'education'],
  chartConfigs: [],
  displayMode: 'amount',
  chartType: 'bar', // Default to bar chart for better Chart.js integration
  showComparison: false,
  loading: false,
  error: null,
  chartData: null,
  chartOptions: null,
  chartInitialized: false
};

export const categoryReducer = createReducer(
  initialState,
  
  on(CategoryActions.loadAnalytics, (state) => ({
    ...state,
    loading: true,
    error: null
  })),
  
  on(CategoryActions.loadAnalyticsSuccess, (state, { analytics }) => ({
    ...state,
    analytics,
    loading: false,
    error: null
  })),
  
  on(CategoryActions.loadAnalyticsFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error
  })),
  
  on(CategoryActions.selectCategories, (state, { categoryIds }) => ({
    ...state,
    selectedCategories: categoryIds
  })),
  
  on(CategoryActions.updateDateRange, (state, { dateRange }) => ({
    ...state,
    selectedDateRange: dateRange
  })),
  
  on(CategoryActions.toggleDisplayMode, (state, { mode }) => ({
    ...state,
    displayMode: mode
  })),
  
  on(CategoryActions.changeChartType, (state, { chartType }) => ({
    ...state,
    chartType: chartType as 'donut' | 'sunburst' | 'bar' | 'line' | 'scatter',
    chartInitialized: false // Reset chart when type changes
  })),
  
  on(CategoryActions.toggleComparison, (state, { showComparison }) => ({
    ...state,
    showComparison
  })),
  
  on(CategoryActions.setBudgetTarget, (state, { categoryId, target }) => ({
    ...state,
    analytics: state.analytics.map(category =>
      category.categoryId === categoryId
        ? { ...category, budgetTarget: target }
        : category
    )
  })),
  
  on(CategoryActions.clearError, (state) => ({
    ...state,
    error: null
  })),
  
  // Enhanced chart actions
  on(CategoryActions.initializeChart, (state, { chartData, chartOptions }) => ({
    ...state,
    chartData,
    chartOptions,
    chartInitialized: true,
    error: null
  })),
  
  on(CategoryActions.updateChartData, (state, { chartData }) => ({
    ...state,
    chartData,
    error: null
  })),
  
  on(CategoryActions.chartError, (state, { error }) => ({
    ...state,
    error: `Chart Error: ${error}`,
    chartInitialized: false
  }))
);
