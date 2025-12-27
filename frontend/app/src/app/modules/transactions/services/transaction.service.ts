import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { Transaction, TransactionFilter, TransactionSummary } from '../../../models/transaction.model';
import { environment } from '../../../../environments/environment';

export interface FilterOptions {
  categories: string[];
  accounts: string[];
  persons: string[];
}

export interface TransactionMetrics {
  total_transactions: number;
  total_income: number;
  total_expenses: number;
  net_savings: number;
  monthly_averages: {
    months: number;
    transactions: number;
    income: number;
    expenses: number;
    savings: number;
  };
  yearly_averages: {
    years: number;
    transactions: number;
    income: number;
    expenses: number;
    savings: number;
  };
}

export interface TimelineData {
  credits: Array<{x: string, y: number, description?: string, category?: string}>;
  debits: Array<{x: string, y: number, description?: string, category?: string}>;
}

export interface PaginationResponse {
  total_items: number;
  total_pages: number;
  current_page: number;
  page_size: number;
}

export interface TransactionListResponse {
  transactions: Transaction[];
  pagination: PaginationResponse;
}

@Injectable({
  providedIn: 'root'
})
export class TransactionService {
  private apiUrl = environment.apiUrl + '/transactions';

  constructor(private http: HttpClient) { }

  getTransactions(): Observable<TransactionListResponse> {
    // Update to use the correct endpoint with pagination parameters
    const params = new HttpParams()
      .set('page', '1')
      .set('page_size', '50');
    
    // Log the request URL for debugging
    console.log('Fetching transactions from:', `${this.apiUrl}/`);
    return this.http.get<TransactionListResponse>(`${this.apiUrl}/`, { params });
  }

  getFilteredTransactions(filters: TransactionFilter): Observable<TransactionListResponse> {
    let params = new HttpParams();
    
    console.log('=== getFilteredTransactions ===');
    console.log('Frontend filters received:', JSON.stringify(filters, null, 2));
    
    if (filters.date_from) {
      console.log('Adding start_date:', filters.date_from);
      params = params.set('start_date', filters.date_from);
    }
    
    if (filters.date_to) {
      console.log('Adding end_date:', filters.date_to);
      params = params.set('end_date', filters.date_to);
    }
    
    if (filters.accounts && filters.accounts.length && !filters.accounts.includes('All Accounts')) {
      // Handle multiple accounts by joining them with commas
      const accountsParam = filters.accounts.join(',');
      params = params.set('account', accountsParam);
      console.log('Setting account filter:', accountsParam);
    }
    
    if (filters.categories && filters.categories.length && !filters.categories.includes('All Categories')) {
      // Handle multiple categories by joining them with commas
      const categoriesParam = filters.categories.join(',');
      params = params.set('category', categoriesParam);
      console.log('Setting category filter:', categoriesParam);
    }
    
    if (filters.search_text && filters.search_text.trim() !== '') {
      params = params.set('search', filters.search_text.trim());
      console.log('Setting search filter:', filters.search_text.trim());
    }
    
    if (filters.amount_min !== undefined && filters.amount_min !== null) {
      params = params.set('min_amount', filters.amount_min.toString());
    }
    
    if (filters.amount_max !== undefined && filters.amount_max !== null) {
      params = params.set('max_amount', filters.amount_max.toString());
    }
    
    // Add pagination parameters from filters
    params = params.set('page', (filters.page || 1).toString());
    params = params.set('page_size', (filters.page_size || 50).toString());

    console.log('Final HTTP params string:', params.toString());
    console.log('Full request URL:', `${this.apiUrl}?${params.toString()}`);
    
    return this.http.get<TransactionListResponse>(this.apiUrl, { params });
  }

  getTransaction(id: string): Observable<Transaction> {
    return this.http.get<Transaction>(`${this.apiUrl}/${id}`);
  }

  createTransaction(transaction: Partial<Transaction>): Observable<Transaction> {
    return this.http.post<Transaction>(this.apiUrl, transaction);
  }

  updateTransaction(id: string, transaction: Partial<Transaction>): Observable<Transaction> {
    return this.http.put<Transaction>(`${this.apiUrl}/${id}`, transaction);
  }

  deleteTransaction(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }

  getFilterOptions(): Observable<FilterOptions> {
    return this.http.get<FilterOptions>(`${this.apiUrl}/filter-options`);
  }

  getTransactionMetrics(filters?: TransactionFilter): Observable<TransactionMetrics> {
    let params = new HttpParams();
    
    if (filters) {
      if (filters.date_from) {
        params = params.set('start_date', filters.date_from);
      }
      
      if (filters.date_to) {
        params = params.set('end_date', filters.date_to);
      }
      
      if (filters.accounts && filters.accounts.length && !filters.accounts.includes('All Accounts')) {
        const accountsParam = filters.accounts.join(',');
        params = params.set('account', accountsParam);
      }
      
      if (filters.categories && filters.categories.length && !filters.categories.includes('All Categories')) {
        const categoriesParam = filters.categories.join(',');
        params = params.set('category', categoriesParam);
      }
      
      if (filters.search_text && filters.search_text.trim() !== '') {
        params = params.set('search', filters.search_text.trim());
      }
      
      if (filters.amount_min !== undefined && filters.amount_min !== null) {
        params = params.set('min_amount', filters.amount_min.toString());
      }
      
      if (filters.amount_max !== undefined && filters.amount_max !== null) {
        params = params.set('max_amount', filters.amount_max.toString());
      }
    }
    
    console.log('Metrics request params:', params.toString());
    return this.http.get<TransactionMetrics>(`${this.apiUrl}/metrics`, { params });
  }

  getTransactionTimeline(filters?: TransactionFilter): Observable<TimelineData> {
    let params = new HttpParams();
    
    if (filters) {
      if (filters.date_from) {
        params = params.set('start_date', filters.date_from);
      }
      
      if (filters.date_to) {
        params = params.set('end_date', filters.date_to);
      }
      
      if (filters.accounts && filters.accounts.length && !filters.accounts.includes('All Accounts')) {
        const accountsParam = filters.accounts.join(',');
        params = params.set('account', accountsParam);
      }
      
      if (filters.categories && filters.categories.length && !filters.categories.includes('All Categories')) {
        const categoriesParam = filters.categories.join(',');
        params = params.set('category', categoriesParam);
      }
      
      if (filters.search_text && filters.search_text.trim() !== '') {
        params = params.set('search', filters.search_text.trim());
      }
      
      if (filters.amount_min !== undefined && filters.amount_min !== null) {
        params = params.set('min_amount', filters.amount_min.toString());
      }
      
      if (filters.amount_max !== undefined && filters.amount_max !== null) {
        params = params.set('max_amount', filters.amount_max.toString());
      }
    }
    
    console.log('Timeline request params:', params.toString());
    return this.http.get<TimelineData>(`${this.apiUrl}/timeline`, { params });
  }

  getSummary(filters?: TransactionFilter): Observable<TransactionSummary> {
    let params = new HttpParams();
    
    if (filters) {
      Object.keys(filters).forEach(key => {
        const value = (filters as any)[key];
        if (value !== null && value !== undefined && value !== '') {
          if (Array.isArray(value) && value.length > 0) {
            params = params.set(key, value.join(','));
          } else if (!Array.isArray(value)) {
            params = params.set(key, value.toString());
          }
        }
      });
    }

    return this.http.get<TransactionSummary>(`${this.apiUrl}/summary`, { params });
  }

  exportTransactions(filters?: TransactionFilter): Observable<Blob> {
    let params = new HttpParams();
    
    if (filters) {
      Object.keys(filters).forEach(key => {
        const value = (filters as any)[key];
        if (value !== null && value !== undefined && value !== '') {
          if (Array.isArray(value) && value.length > 0) {
            params = params.set(key, value.join(','));
          } else if (!Array.isArray(value)) {
            params = params.set(key, value.toString());
          }
        }
      });
    }

    return this.http.get(`${this.apiUrl}/export`, { 
      params, 
      responseType: 'blob' 
    });
  }

  bulkUpdateCategories(transactionIds: string[], category: string, subcategory?: string): Observable<void> {
    return this.http.patch<void>(`${this.apiUrl}/bulk-update-categories`, {
      transaction_ids: transactionIds,
      category,
      subcategory
    });
  }

  bulkDelete(transactionIds: string[]): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/bulk-delete`, {
      body: { transaction_ids: transactionIds }
    });
  }

  // Mock data for development - remove when backend is ready
  private getMockTransactions(): Transaction[] {
    return [
      {
        id: '1',
        date: '2024-01-15',
        description: 'Grocery Shopping',
        amount: -2500.00,
        category: 'Food & Dining',
        subcategory: 'Groceries',
        account: 'Savings Account',
        type: 'expense'
      },
      {
        id: '2',
        date: '2024-01-14',
        description: 'Salary Credit',
        amount: 50000.00,
        category: 'Income',
        subcategory: 'Salary',
        account: 'Savings Account',
        type: 'income'
      }
    ];
  }
}

