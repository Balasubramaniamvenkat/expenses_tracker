export interface Transaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  balance?: number;
  category: string;
  subcategory?: string;
  account: string; // Changed from account_name to match backend
  type: 'income' | 'expense';
  reference?: string;
  tags?: string[];
  notes?: string;
}

export interface TransactionFilter {
  date_from?: string;
  date_to?: string;
  categories?: string[];
  accounts?: string[];
  persons?: string[];
  amount_min?: number;
  amount_max?: number;
  search_text?: string;
  transaction_types?: ('income' | 'expense')[];
  tags?: string[];
  page?: number;
  page_size?: number;
}

export interface TransactionSummary {
  total_transactions: number;
  total_income: number;
  total_expenses: number;
  net_amount: number;
  date_range: [string, string];
  categories_count: number;
  accounts_count: number;
}

export interface CategoryAnalysis {
  category: string;
  subcategories: string[];
  total_amount: number;
  transaction_count: number;
  percentage_of_total: number;
  average_amount: number;
  monthly_trend: { month: string; amount: number }[];
}

export interface MonthlyTrend {
  month: string;
  year: number;
  income: number;
  expenses: number;
  net: number;
  transaction_count: number;
}
