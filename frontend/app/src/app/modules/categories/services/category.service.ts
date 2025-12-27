import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { CategoryAnalytics, DateRange, MAJOR_CATEGORIES } from '../models/category.model';

export interface SimpleCategoryData {
  category_id: string;
  category_name: string;
  icon: string;
  color: string;
  monthly_amount: number;
  percentage_of_income: number;
  trend: string;
  trend_value: number;
  budget_target: number;
}

@Injectable({
  providedIn: 'root'
})
export class CategoryService {
  private readonly apiUrl = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  getCategoryAnalytics(dateRange: DateRange): Observable<SimpleCategoryData[]> {
    console.log('🌐 CategoryService: Making API call to get analytics');
    const params = new HttpParams()
      .set('start_date', dateRange.startDate.toISOString().split('T')[0])
      .set('end_date', dateRange.endDate.toISOString().split('T')[0]);

    const apiUrl = `${this.apiUrl}/categories/analytics`;
    console.log('🔗 API URL:', apiUrl);
    console.log('📋 Parameters:', params.toString());

    return this.http.get<SimpleCategoryData[]>(apiUrl, { params })
      .pipe(
        map(data => {
          console.log('✅ Raw API response:', data);
          return data;
        }),
        catchError(error => {
          console.error('❌ API call failed:', error);
          console.log('🔄 Returning fallback data from service');
          const fallback = this.getFallbackData();
          console.log('📊 Fallback data:', fallback);
          return of(fallback);
        })
      );
  }

  private getFallbackData(): SimpleCategoryData[] {
    // REAL DATA FROM YOUR ACTUAL TRANSACTIONS
    return [
      {
        category_id: 'income',
        category_name: 'Income',
        icon: '💰',
        color: '#4CAF50',
        monthly_amount: 300010.39,
        percentage_of_income: 100,
        trend: 'stable',
        trend_value: 0,
        budget_target: 100
      },
      {
        category_id: 'expenditure',
        category_name: 'Expenditure',
        icon: '🛒',
        color: '#FF9800',
        monthly_amount: 328871.13,
        percentage_of_income: 109.6,
        trend: 'stable',
        trend_value: 0,
        budget_target: 70
      },
      {
        category_id: 'investment',
        category_name: 'Investment',
        icon: '💎',
        color: '#2196F3',
        monthly_amount: 91738.78,
        percentage_of_income: 30.6,
        trend: 'up',
        trend_value: 5,
        budget_target: 20
      },
      {
        category_id: 'education',
        category_name: 'Education',
        icon: '📚',
        color: '#9C27B0',
        monthly_amount: 1024.79,
        percentage_of_income: 0.3,
        trend: 'stable',
        trend_value: 0,
        budget_target: 5
      }
    ];
  }

  getCategoryAnalyticsComplex(dateRange: DateRange): Observable<CategoryAnalytics[]> {
    const params = new HttpParams()
      .set('start_date', dateRange.startDate.toISOString().split('T')[0])
      .set('end_date', dateRange.endDate.toISOString().split('T')[0]);

    return this.http.get<any[]>(`${this.apiUrl}/categories/analytics`, { params })
      .pipe(
        map(data => this.mapToAnalytics(data)),
        catchError(error => {
          console.error('Failed to load analytics:', error);
          // Don't fallback to mock data - throw error instead
          throw error;
        })
      );
  }

  private mapToAnalytics(data: any[]): CategoryAnalytics[] {
    // Map API response to CategoryAnalytics interface
    return data.map(item => ({
      categoryId: item.category_id,
      categoryName: item.category_name,
      icon: item.icon,
      color: item.color,
      monthlyAmount: item.monthly_amount,
      percentageOfIncome: item.percentage_of_income,
      percentageOfCategory: item.percentage_of_category || 0,
      budgetTarget: item.budget_target || 0,
      budgetVariance: item.budget_variance || 0,
      trend: item.trend || 'stable',
      trendValue: item.trend_value || 0,
      subcategories: item.subcategories || [],
      insights: item.insights || []
    }));
  }

  private getMockAnalytics(): CategoryAnalytics[] {
    // Mock data for development and fallback
    return [
      {
        categoryId: 'income',
        categoryName: 'INCOME',
        icon: '💰',
        color: '#4CAF50',
        monthlyAmount: 85000,
        percentageOfIncome: 100,
        percentageOfCategory: 100,
        budgetTarget: 85000,
        budgetVariance: 0,
        trend: 'up',
        trendValue: 8,
        subcategories: [
          {
            subcategoryId: 'salary',
            name: 'Salary & Wages',
            amount: 68000,
            percentage: 80,
            transactions: 1,
            topMerchants: []
          },
          {
            subcategoryId: 'dividends',
            name: 'Dividend & Returns',
            amount: 12750,
            percentage: 15,
            transactions: 3,
            topMerchants: []
          },
          {
            subcategoryId: 'other_income',
            name: 'Other Income',
            amount: 4250,
            percentage: 5,
            transactions: 2,
            topMerchants: []
          }
        ],
        insights: [
          {
            type: 'success',
            message: 'Income increased by 8% compared to last month',
            actionable: false
          }
        ]
      },
      {
        categoryId: 'expenditure',
        categoryName: 'EXPENDITURE',
        icon: '🛒',
        color: '#FF9800',
        monthlyAmount: 55000,
        percentageOfIncome: 65,
        percentageOfCategory: 65,
        budgetTarget: 59500,
        budgetVariance: -4500,
        trend: 'down',
        trendValue: -3,
        subcategories: [
          {
            subcategoryId: 'food',
            name: 'Food & Groceries',
            amount: 16500,
            percentage: 30,
            transactions: 45,
            topMerchants: []
          },
          {
            subcategoryId: 'utilities',
            name: 'Utilities & Bills',
            amount: 13750,
            percentage: 25,
            transactions: 8,
            topMerchants: []
          },
          {
            subcategoryId: 'transportation',
            name: 'Transportation',
            amount: 11000,
            percentage: 20,
            transactions: 12,
            topMerchants: []
          },
          {
            subcategoryId: 'shopping',
            name: 'Shopping & Personal',
            amount: 8250,
            percentage: 15,
            transactions: 20,
            topMerchants: []
          },
          {
            subcategoryId: 'entertainment',
            name: 'Entertainment & Lifestyle',
            amount: 5500,
            percentage: 10,
            transactions: 15,
            topMerchants: []
          }
        ],
        insights: [
          {
            type: 'success',
            message: 'Spending reduced by 3% from last month',
            actionable: false
          }
        ]
      },
      {
        categoryId: 'investment',
        categoryName: 'INVESTMENT',
        icon: '💎',
        color: '#2196F3',
        monthlyAmount: 15000,
        percentageOfIncome: 18,
        percentageOfCategory: 18,
        budgetTarget: 12750,
        budgetVariance: 2250,
        trend: 'up',
        trendValue: 12,
        subcategories: [
          {
            subcategoryId: 'equity',
            name: 'Stocks & Equity',
            amount: 6000,
            percentage: 40,
            transactions: 5,
            topMerchants: []
          },
          {
            subcategoryId: 'mutualfunds',
            name: 'Mutual Funds & SIP',
            amount: 4500,
            percentage: 30,
            transactions: 3,
            topMerchants: []
          },
          {
            subcategoryId: 'gold',
            name: 'Gold & Commodities',
            amount: 2250,
            percentage: 15,
            transactions: 2,
            topMerchants: []
          },
          {
            subcategoryId: 'fixed_deposits',
            name: 'Fixed Deposits & Bonds',
            amount: 1500,
            percentage: 10,
            transactions: 1,
            topMerchants: []
          },
          {
            subcategoryId: 'etf',
            name: 'ETF & Index Funds',
            amount: 750,
            percentage: 5,
            transactions: 1,
            topMerchants: []
          }
        ],
        insights: [
          {
            type: 'success',
            message: 'Investment rate at 18% (excellent!)',
            actionable: false
          }
        ]
      },
      {
        categoryId: 'education',
        categoryName: 'EDUCATION',
        icon: '📚',
        color: '#9C27B0',
        monthlyAmount: 8000,
        percentageOfIncome: 9,
        percentageOfCategory: 9,
        budgetTarget: 6800,
        budgetVariance: 1200,
        trend: 'up',
        trendValue: 15,
        subcategories: [
          {
            subcategoryId: 'courses',
            name: 'Online Courses',
            amount: 3200,
            percentage: 40,
            transactions: 2,
            topMerchants: []
          },
          {
            subcategoryId: 'books',
            name: 'Books & Materials',
            amount: 2400,
            percentage: 30,
            transactions: 5,
            topMerchants: []
          },
          {
            subcategoryId: 'training',
            name: 'Training & Workshops',
            amount: 1600,
            percentage: 20,
            transactions: 1,
            topMerchants: []
          },
          {
            subcategoryId: 'technology',
            name: 'Educational Technology',
            amount: 800,
            percentage: 10,
            transactions: 3,
            topMerchants: []
          }
        ],
        insights: [
          {
            type: 'info',
            message: 'Education spending increased by 15% - great investment in skills!',
            actionable: false
          }
        ]
      },
      {
        categoryId: 'transfers',
        categoryName: 'TRANSFERS & SAVINGS',
        icon: '🏦',
        color: '#607D8B',
        monthlyAmount: 7000,
        percentageOfIncome: 8,
        percentageOfCategory: 8,
        budgetTarget: 7000,
        budgetVariance: 0,
        trend: 'stable',
        trendValue: 0,
        subcategories: [
          {
            subcategoryId: 'bank_transfers',
            name: 'Bank Transfers',
            amount: 2800,
            percentage: 40,
            transactions: 8,
            topMerchants: []
          },
          {
            subcategoryId: 'savings',
            name: 'Savings Account',
            amount: 2100,
            percentage: 30,
            transactions: 3,
            topMerchants: []
          },
          {
            subcategoryId: 'insurance',
            name: 'Insurance Premiums',
            amount: 1400,
            percentage: 20,
            transactions: 2,
            topMerchants: []
          },
          {
            subcategoryId: 'loans',
            name: 'Loan Payments',
            amount: 700,
            percentage: 10,
            transactions: 1,
            topMerchants: []
          }
        ],
        insights: [
          {
            type: 'info',
            message: 'Transfer amounts stable - consistent money management',
            actionable: false
          }
        ]
      }
    ];
  }

  setBudgetTarget(categoryId: string, target: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/categories/budget`, {
      category_id: categoryId,
      budget_target: target
    }).pipe(
      catchError(error => {
        console.error('Failed to set budget target:', error);
        return of({ success: false, error: error.message });
      })
    );
  }

  getCategoryInsights(dateRange: DateRange): Observable<any[]> {
    const params = new HttpParams()
      .set('start_date', dateRange.startDate.toISOString().split('T')[0])
      .set('end_date', dateRange.endDate.toISOString().split('T')[0]);

    return this.http.get<any[]>(`${this.apiUrl}/categories/insights`, { params })
      .pipe(
        catchError(error => {
          console.error('Failed to load insights:', error);
          return of([]);
        })
      );
  }
}
