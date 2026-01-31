import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatInputModule } from '@angular/material/input';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { HttpClient } from '@angular/common/http';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { Chart, registerables, ChartEvent, ActiveElement } from 'chart.js';

Chart.register(...registerables);

// Interfaces
interface DashboardSummary {
  totalIncome: number;
  totalExpenses: number;
  totalInvestments: number;
  netSavings: number;
  transactionCount: number;
  dateRange: {
    from: string;
    to: string;
  };
  topCategories: CategoryData[];
  monthlyTrend: MonthlyTrend[];
}

interface CategoryData {
  name: string;
  amount: number;
  percentage: number;
  icon: string;
  color: string;
}

interface MonthlyTrend {
  month: string;
  income: number;
  expenses: number;
}

interface TrendComparison {
  current: number;
  previous: number;
  change: number;
  trend: 'up' | 'down' | 'stable';
  isPositive: boolean;
}

interface TrendData {
  success: boolean;
  comparisons: {
    income: TrendComparison;
    expenses: TrendComparison;
    investments: TrendComparison;
    savings: TrendComparison;
  };
  periods: {
    current: { from: string; to: string };
    previous: { from: string; to: string };
  };
}

interface HierarchyCategory {
  id: string;
  name: string;
  icon: string;
  color: string;
  amount: number;
  percentage: number;
  transactionCount: number;
  subcategories: HierarchySubcategory[];
}

interface HierarchySubcategory {
  id: string;
  name: string;
  amount: number;
  percentage: number;
  percentageOfTotal: number;
  transactionCount: number;
  color: string;
  merchants: HierarchyMerchant[];
  transactions: TransactionItem[];
}

interface HierarchyMerchant {
  name: string;
  amount: number;
  count: number;
  percentage: number;
  color: string;
}

interface TransactionItem {
  date: string;
  description: string;
  amount: number;
  merchant: string;
}

interface HierarchyResponse {
  success: boolean;
  message: string;
  hierarchy: HierarchyCategory[];
  summary: {
    totalAmount: number;
    categoryCount: number;
    transactionCount: number;
    dateRange: { from: string; to: string };
    topCategory: string;
    transactionType: string;
  };
}

type DrillLevel = 'category' | 'subcategory' | 'merchant';

interface DrillState {
  level: DrillLevel;
  categoryId: string | null;
  categoryName: string | null;
  subcategoryId: string | null;
  subcategoryName: string | null;
}

@Component({
  selector: 'app-dashboard-enhanced',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDividerModule,
    MatSelectModule,
    MatFormFieldModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatInputModule,
    MatSidenavModule,
    MatListModule,
    MatChipsModule,
    MatTooltipModule
  ],
  templateUrl: './dashboard-enhanced.component.html',
  styleUrls: ['./dashboard-enhanced.component.scss']
})
export class DashboardEnhancedComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private trendChart: Chart | null = null;
  private categoryChart: Chart | null = null;

  // Expose Math for template use
  Math = Math;

  // Data
  summary: DashboardSummary | null = null;
  trendData: TrendData | null = null;
  hierarchyData: HierarchyResponse | null = null;
  
  // State
  isLoading = true;
  error: string | null = null;
  
  // Date Range
  dateRangeOptions = [
    { value: '1m', label: 'Last Month' },
    { value: '3m', label: 'Last 3 Months' },
    { value: '6m', label: 'Last 6 Months' },
    { value: '1y', label: 'Last Year' },
    { value: 'all', label: 'All Time' },
    { value: 'custom', label: 'Custom Range' }
  ];
  selectedDateRange = 'all';
  customStartDate: Date | null = null;
  customEndDate: Date | null = null;
  
  // Drill-down state
  drillState: DrillState = {
    level: 'category',
    categoryId: null,
    categoryName: null,
    subcategoryId: null,
    subcategoryName: null
  };
  
  // Transaction drawer
  isDrawerOpen = false;
  drawerTitle = '';
  drawerTransactions: TransactionItem[] = [];
  drawerLoading = false;

  // Chart data for current drill level
  currentChartData: any[] = [];
  currentDrillTotal: number = 0;  // Total amount for current drill level
  
  private readonly API_BASE = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadAllData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.trendChart?.destroy();
    this.categoryChart?.destroy();
  }

  loadAllData(): void {
    this.isLoading = true;
    this.error = null;

    const dateParams = this.getDateParams();

    forkJoin({
      summary: this.http.get<DashboardSummary>(`${this.API_BASE}/api/dashboard/summary`),
      trends: this.http.get<TrendData>(`${this.API_BASE}/api/categories/trend-comparison`),
      hierarchy: this.http.get<HierarchyResponse>(`${this.API_BASE}/api/categories/hierarchy${dateParams}`)
    }).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.summary = data.summary;
          this.trendData = data.trends;
          this.hierarchyData = data.hierarchy;
          this.isLoading = false;
          
          // Reset drill state
          this.resetDrillState();
          
          setTimeout(() => this.createCharts(), 100);
        },
        error: (err) => {
          console.error('Dashboard API error:', err);
          this.loadFallbackData();
        }
      });
  }

  private getDateParams(): string {
    if (this.selectedDateRange === 'all') {
      return '?transaction_type=expense';
    }
    
    const now = new Date();
    let startDate: Date;
    
    switch (this.selectedDateRange) {
      case '1m':
        startDate = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
        break;
      case '3m':
        startDate = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
        break;
      case '6m':
        startDate = new Date(now.getFullYear(), now.getMonth() - 6, now.getDate());
        break;
      case '1y':
        startDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
        break;
      case 'custom':
        if (this.customStartDate && this.customEndDate) {
          return `?start_date=${this.formatDate(this.customStartDate)}&end_date=${this.formatDate(this.customEndDate)}&transaction_type=expense`;
        }
        return '?transaction_type=expense';
      default:
        return '?transaction_type=expense';
    }
    
    return `?start_date=${this.formatDate(startDate)}&end_date=${this.formatDate(now)}&transaction_type=expense`;
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  onDateRangeChange(): void {
    if (this.selectedDateRange !== 'custom') {
      this.loadAllData();
    }
  }

  applyCustomDateRange(): void {
    if (this.customStartDate && this.customEndDate) {
      this.loadAllData();
    }
  }

  private loadFallbackData(): void {
    this.http.get<DashboardSummary>(`${this.API_BASE}/api/dashboard/summary`)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.summary = data;
          this.isLoading = false;
          setTimeout(() => this.createCharts(), 100);
        },
        error: () => {
          this.error = 'Could not connect to the server. Please make sure the backend is running.';
          this.isLoading = false;
        }
      });
  }

  private createCharts(): void {
    if (!this.summary) return;
    this.createTrendChart();
    this.createCategoryChart();
  }

  private createTrendChart(): void {
    const canvas = document.getElementById('trendChart') as HTMLCanvasElement;
    if (!canvas || !this.summary) return;

    this.trendChart?.destroy();

    let months: string[];
    let incomeData: number[];
    let expenseData: number[];

    if (this.summary.monthlyTrend && this.summary.monthlyTrend.length > 0) {
      months = this.summary.monthlyTrend.map(t => {
        const parts = t.month.split('-');
        if (parts.length === 2) {
          const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
          const monthIndex = parseInt(parts[1], 10) - 1;
          const year = parts[0].slice(-2);
          return `${monthNames[monthIndex]} '${year}`;
        }
        return t.month;
      });
      incomeData = this.summary.monthlyTrend.map(t => t.income);
      expenseData = this.summary.monthlyTrend.map(t => t.expenses);
    } else {
      const now = new Date();
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      months = [monthNames[now.getMonth()]];
      incomeData = [this.summary.totalIncome];
      expenseData = [this.summary.totalExpenses + this.summary.totalInvestments];
    }

    this.trendChart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: months,
        datasets: [
          {
            label: 'Income',
            data: incomeData,
            borderColor: '#4CAF50',
            backgroundColor: 'rgba(76, 175, 80, 0.1)',
            fill: true,
            tension: 0.4
          },
          {
            label: 'Expenses',
            data: expenseData,
            borderColor: '#FF9800',
            backgroundColor: 'rgba(255, 152, 0, 0.1)',
            fill: true,
            tension: 0.4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => '₹' + Number(value).toLocaleString('en-IN')
            }
          }
        }
      }
    });
  }

  private createCategoryChart(): void {
    const canvas = document.getElementById('categoryChart') as HTMLCanvasElement;
    if (!canvas) return;

    this.categoryChart?.destroy();

    const chartData = this.getChartDataForCurrentLevel();
    this.currentChartData = chartData;
    // Calculate total for current drill level
    this.currentDrillTotal = chartData.reduce((sum, item) => sum + item.amount, 0);

    if (chartData.length === 0) {
      return;
    }

    this.categoryChart = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: chartData.map(c => c.name),
        datasets: [{
          data: chartData.map(c => c.amount),
          backgroundColor: chartData.map(c => c.color),
          borderWidth: 3,
          borderColor: '#fff',
          hoverBorderWidth: 4,
          hoverOffset: 10
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: {
            display: false // We'll use custom legend
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = context.parsed;
                const percentage = chartData[context.dataIndex]?.percentage || 0;
                return `${context.label}: ₹${value.toLocaleString('en-IN')} (${percentage.toFixed(1)}%)`;
              }
            }
          }
        },
        onClick: (event: ChartEvent, elements: ActiveElement[]) => {
          if (elements.length > 0) {
            const index = elements[0].index;
            this.handleChartClick(index);
          }
        }
      }
    });
  }

  private getChartDataForCurrentLevel(): any[] {
    if (!this.hierarchyData?.hierarchy) {
      // Fallback to summary data
      if (this.summary?.topCategories) {
        return this.summary.topCategories.filter(c => c.name !== 'Income');
      }
      return [];
    }

    const hierarchy = this.hierarchyData.hierarchy;

    switch (this.drillState.level) {
      case 'category':
        return hierarchy.map(cat => ({
          id: cat.id,
          name: cat.name,
          amount: cat.amount,
          percentage: cat.percentage,
          color: cat.color,
          icon: cat.icon,
          transactionCount: cat.transactionCount
        }));

      case 'subcategory':
        const category = hierarchy.find(c => c.id === this.drillState.categoryId);
        if (!category) return [];
        return category.subcategories.map(sub => ({
          id: sub.id,
          name: sub.name,
          amount: sub.amount,
          percentage: sub.percentage,
          color: sub.color,
          transactionCount: sub.transactionCount
        }));

      case 'merchant':
        const cat = hierarchy.find(c => c.id === this.drillState.categoryId);
        if (!cat) return [];
        const subcat = cat.subcategories.find(s => s.id === this.drillState.subcategoryId);
        if (!subcat) return [];
        return subcat.merchants.map(m => ({
          id: m.name,
          name: m.name,
          amount: m.amount,
          percentage: m.percentage,
          color: m.color,
          transactionCount: m.count
        }));

      default:
        return [];
    }
  }

  handleChartClick(index: number): void {
    const clickedItem = this.currentChartData[index];
    if (!clickedItem) return;

    switch (this.drillState.level) {
      case 'category':
        this.drillState = {
          level: 'subcategory',
          categoryId: clickedItem.id,
          categoryName: clickedItem.name,
          subcategoryId: null,
          subcategoryName: null
        };
        this.createCategoryChart();
        break;

      case 'subcategory':
        this.drillState = {
          ...this.drillState,
          level: 'merchant',
          subcategoryId: clickedItem.id,
          subcategoryName: clickedItem.name
        };
        this.createCategoryChart();
        break;

      case 'merchant':
        // Open transaction drawer for this merchant
        this.openTransactionDrawer(clickedItem);
        break;
    }
  }

  drillUp(): void {
    switch (this.drillState.level) {
      case 'subcategory':
        this.drillState = {
          level: 'category',
          categoryId: null,
          categoryName: null,
          subcategoryId: null,
          subcategoryName: null
        };
        break;

      case 'merchant':
        this.drillState = {
          ...this.drillState,
          level: 'subcategory',
          subcategoryId: null,
          subcategoryName: null
        };
        break;
    }
    this.createCategoryChart();
  }

  resetDrillState(): void {
    this.drillState = {
      level: 'category',
      categoryId: null,
      categoryName: null,
      subcategoryId: null,
      subcategoryName: null
    };
  }

  getBreadcrumb(): string[] {
    const crumbs = ['All Categories'];
    if (this.drillState.categoryName) {
      crumbs.push(this.drillState.categoryName);
    }
    if (this.drillState.subcategoryName) {
      crumbs.push(this.drillState.subcategoryName);
    }
    return crumbs;
  }

  onBreadcrumbClick(index: number): void {
    if (index === 0) {
      this.resetDrillState();
      this.createCategoryChart();
    } else if (index === 1 && this.drillState.level === 'merchant') {
      this.drillUp();
    }
  }

  openTransactionDrawer(item: any): void {
    this.isDrawerOpen = true;
    this.drawerLoading = true;
    this.drawerTitle = `${item.name} - Transactions`;
    
    // Get transactions from hierarchy data
    if (this.hierarchyData?.hierarchy && this.drillState.categoryId) {
      const category = this.hierarchyData.hierarchy.find(c => c.id === this.drillState.categoryId);
      if (category && this.drillState.subcategoryId) {
        const subcategory = category.subcategories.find(s => s.id === this.drillState.subcategoryId);
        if (subcategory) {
          this.drawerTransactions = subcategory.transactions.filter(
            t => t.merchant.toLowerCase() === item.name.toLowerCase()
          );
        }
      }
    }
    this.drawerLoading = false;
  }

  openCategoryTransactions(categoryData: any): void {
    this.isDrawerOpen = true;
    this.drawerLoading = true;
    this.drawerTitle = `${categoryData.name} - All Transactions`;

    const params = this.getDateParams().replace('?', '&');
    this.http.get<any>(`${this.API_BASE}/api/categories/transactions-by-category?category=${categoryData.name}${params}`)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.drawerTransactions = data.transactions || [];
          this.drawerLoading = false;
        },
        error: () => {
          this.drawerTransactions = [];
          this.drawerLoading = false;
        }
      });
  }

  closeDrawer(): void {
    this.isDrawerOpen = false;
    this.drawerTransactions = [];
  }

  // Trend helpers
  getTrendIcon(trend: string): string {
    switch (trend) {
      case 'up': return 'trending_up';
      case 'down': return 'trending_down';
      default: return 'trending_flat';
    }
  }

  getTrendClass(comparison: TrendComparison | undefined, type: string): string {
    if (!comparison) return '';
    
    // For expenses, down is good. For income/savings, up is good.
    if (type === 'expenses') {
      return comparison.trend === 'down' ? 'trend-positive' : 
             comparison.trend === 'up' ? 'trend-negative' : '';
    }
    return comparison.trend === 'up' ? 'trend-positive' : 
           comparison.trend === 'down' ? 'trend-negative' : '';
  }

  // Stats helpers
  getMonthsCount(): number {
    if (!this.summary?.dateRange) return 0;
    const from = new Date(this.summary.dateRange.from);
    const to = new Date(this.summary.dateRange.to);
    return Math.max(1, Math.ceil((to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24 * 30)));
  }

  getSavingsRate(): number {
    if (!this.summary || this.summary.totalIncome === 0) return 0;
    return ((this.summary.totalIncome - this.summary.totalExpenses) / this.summary.totalIncome) * 100;
  }

  getAvgDailyExpense(): number {
    if (!this.summary) return 0;
    const days = this.getMonthsCount() * 30;
    return days > 0 ? this.summary.totalExpenses / days : 0;
  }

  formatCurrency(value: number): string {
    return '₹' + value.toLocaleString('en-IN', { maximumFractionDigits: 0 });
  }

  getSelectedDateRangeLabel(): string {
    const option = this.dateRangeOptions.find(o => o.value === this.selectedDateRange);
    return option ? option.label : 'All Time';
  }

  getDateRangeIcon(value: string): string {
    const icons: { [key: string]: string } = {
      '1m': 'today',
      '3m': 'date_range',
      '6m': 'event_note',
      '1y': 'calendar_month',
      'all': 'all_inclusive',
      'custom': 'edit_calendar'
    };
    return icons[value] || 'calendar_today';
  }
}
