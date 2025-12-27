export interface CategoryAnalytics {
  categoryId: string;
  categoryName: string;
  icon: string;
  color: string;
  monthlyAmount: number;
  percentageOfIncome: number;
  percentageOfCategory: number;
  budgetTarget: number;
  budgetVariance: number;
  trend: TrendType;
  trendValue: number;
  subcategories: SubcategoryAnalytics[];
  insights: CategoryInsight[];
}

export interface SubcategoryAnalytics {
  subcategoryId: string;
  name: string;
  amount: number;
  percentage: number;
  transactions: number;
  topMerchants: MerchantSummary[];
}

export interface MerchantSummary {
  name: string;
  amount: number;
  transactions: number;
  percentage: number;
}

export interface CategoryInsight {
  type: 'warning' | 'success' | 'info' | 'alert';
  message: string;
  actionable: boolean;
  recommendation?: string;
}

export type TrendType = 'up' | 'down' | 'stable';

export interface DateRange {
  startDate: Date;
  endDate: Date;
}

export interface CategorySummary {
  totalIncome: number;
  totalExpenditure: number;
  totalInvestment: number;
  totalEducation: number;
  totalTransfers: number;
  savingsRate: number;
  netSavings: number;
}

// Display Mode Configuration
export interface DisplayMode {
  viewType: 'amount' | 'percentage';
  chartType: 'donut' | 'sunburst' | 'bar' | 'line';
  showComparison: boolean;
  timeframe: 'month' | 'quarter' | 'year';
}

// Toggle State Management
export interface ViewToggleState {
  displayMode: 'amount' | 'percentage';
  chartConfig: ChartDisplayConfig;
  previousPeriodComparison: boolean;
}

export interface ChartDisplayConfig {
  type: string;
  responsive: boolean;
  maintainAspectRatio: boolean;
  animationDuration: number;
}

// Major Categories Configuration
export const MAJOR_CATEGORIES = [
  {
    id: 'income',
    name: 'INCOME',
    icon: '💰',
    color: '#4CAF50',
    targetPercentage: 100,
    description: 'Salary, dividends, business income, other income'
  },
  {
    id: 'expenditure',
    name: 'EXPENDITURE',
    icon: '🛒',
    color: '#FF9800',
    targetPercentage: 65,
    description: 'Food, utilities, transportation, shopping, entertainment'
  },
  {
    id: 'investment',
    name: 'INVESTMENT',
    icon: '💎',
    color: '#2196F3',
    targetPercentage: 18,
    description: 'Stocks, mutual funds, gold, fixed deposits, ETFs'
  },
  {
    id: 'education',
    name: 'EDUCATION',
    icon: '📚',
    color: '#9C27B0',
    targetPercentage: 9,
    description: 'Tuition, books, online courses, training, workshops'
  },
  {
    id: 'transfers',
    name: 'TRANSFERS & SAVINGS',
    icon: '🏦',
    color: '#607D8B',
    targetPercentage: 8,
    description: 'Bank transfers, savings, insurance, loan payments'
  }
] as const;

export type MajorCategoryId = typeof MAJOR_CATEGORIES[number]['id'];
