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
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { HttpClient } from '@angular/common/http';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { Chart, registerables, ChartEvent, ActiveElement } from 'chart.js';

Chart.register(...registerables);

// Interfaces
interface DashboardSummary {
  totalIncome: number;
  totalExpenses: number;
  totalInvestments: number;
  totalPlanned: number;
  netSavings: number;
  transactionCount: number;
  monthsCovered: number;
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
  averageMonthlyAmount: number;
  percentage: number;
  icon: string;
  color: string;
}

interface MonthlyTrend {
  month: string;
  income: number;
  expenses: number;
  investments: number;
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
  averageMonthlyAmount: number;
  percentage: number;
  transactionCount: number;
  subcategories: HierarchySubcategory[];
}

interface HierarchySubcategory {
  id: string;
  name: string;
  amount: number;
  averageMonthlyAmount: number;
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
  averageMonthlyAmount: number;
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
    monthsCovered: number;
    categoryCount: number;
    transactionCount: number;
    dateRange: { from: string; to: string };
    topCategory: string;
    transactionType: string;
  };
}

type DrillLevel = 'category' | 'subcategory' | 'merchant';
type BreakdownType = 'expense' | 'income' | 'investment';

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
    MatTooltipModule,
    MatButtonToggleModule
  ],
  templateUrl: './dashboard-enhanced.component.html',
  styleUrls: ['./dashboard-enhanced.component.scss']
})
export class DashboardEnhancedComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private trendChart: Chart | null = null;
  private categoryChart: Chart | null = null;
  private averageChart: Chart | null = null;
  private dashboardLoadId = 0;

  // Expose Math for template use
  Math = Math;

  // Data
  summary: DashboardSummary | null = null;
  trendData: TrendData | null = null;
  hierarchyData: HierarchyResponse | null = null;
  incomeHierarchyData: HierarchyResponse | null = null;
  investmentHierarchyData: HierarchyResponse | null = null;
  private incomeTopCategories: CategoryData[] = [];
  private investmentTopCategories: CategoryData[] = [];
  isInvestmentHierarchyLoading = false;
  investmentHierarchyError: string | null = null;
  isIncomeHierarchyLoading = false;
  incomeHierarchyError: string | null = null;

  // Which side of the books the breakdown charts and category list show
  breakdownType: BreakdownType = 'expense';
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
  drawerTotal = 0;
  drawerLoading = false;
  drawerLoadingMore = false;
  drawerError: string | null = null;
  private drawerOffset = 0;
  private drawerFilters: { category: string; subcategory?: string; merchant?: string } | null = null;
  private readonly drawerPageSize = 50;

  // Chart data for current drill level
  currentChartData: any[] = [];
  currentDrillTotal: number = 0;  // Total amount for current drill level
  averageChartData: any[] = [];
  averageDrillState: DrillState = {
    level: 'category',
    categoryId: null,
    categoryName: null,
    subcategoryId: null,
    subcategoryName: null
  };
  
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
    this.averageChart?.destroy();
  }

  loadAllData(): void {
    const loadId = ++this.dashboardLoadId;
    this.isLoading = true;
    this.error = null;
    this.trendData = null;
    this.hierarchyData = null;
    this.incomeHierarchyData = null;
    this.investmentHierarchyData = null;
    this.incomeTopCategories = [];
    this.investmentTopCategories = [];
    this.isInvestmentHierarchyLoading = false;
    this.investmentHierarchyError = null;
    this.isIncomeHierarchyLoading = false;
    this.incomeHierarchyError = null;

    const dateParams = this.getDateParams();
    const summaryParams = new URLSearchParams(dateParams.replace(/^\?/, ''));
    summaryParams.delete('transaction_type');
    const summaryQuery = summaryParams.toString();

    forkJoin({
      summary: this.http.get<DashboardSummary>(
        `${this.API_BASE}/api/dashboard/summary${summaryQuery ? `?${summaryQuery}` : ''}`
      ),
      trends: this.http.get<TrendData>(`${this.API_BASE}/api/categories/trend-comparison`),
      hierarchy: this.http.get<HierarchyResponse>(`${this.API_BASE}/api/categories/hierarchy${dateParams}`)
    }).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          if (loadId !== this.dashboardLoadId) return;
          this.summary = data.summary;
          this.trendData = data.trends;
          this.hierarchyData = data.hierarchy;
          this.isLoading = false;
          
          // Reset drill state
          this.resetDrillState();
          this.resetAverageDrillState();
          setTimeout(() => {
            this.createCharts();
            if (this.isIncomeView && !this.incomeHierarchyData) this.loadIncomeHierarchy();
            if (this.isInvestmentView && !this.investmentHierarchyData) this.loadInvestmentHierarchy();
          }, 100);
        },
        error: (err) => {
          if (loadId !== this.dashboardLoadId) return;
          console.error('Dashboard API error:', err);
          this.loadFallbackData(loadId);
        }
      });
  }

  loadIncomeHierarchy(): void {
    if (this.incomeHierarchyData || this.isIncomeHierarchyLoading) return;

    const loadId = this.dashboardLoadId;
    this.isIncomeHierarchyLoading = true;
    this.incomeHierarchyError = null;
    this.http.get<HierarchyResponse>(
      `${this.API_BASE}/api/categories/hierarchy${this.getDateParams('income')}`
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          if (loadId !== this.dashboardLoadId) return;
          this.isIncomeHierarchyLoading = false;
          if (!data.success) {
            this.incomeHierarchyError = data.message || 'Could not load the income breakdown.';
            return;
          }
          this.incomeHierarchyData = data;
          this.incomeTopCategories = data.hierarchy.map(category => ({
            name: category.name,
            amount: category.amount,
            averageMonthlyAmount: category.averageMonthlyAmount,
            percentage: category.percentage,
            icon: category.icon,
            color: category.color
          }));
          if (this.isIncomeView) {
            this.createCategoryChart();
            this.createAverageChart();
          }
        },
        error: (err) => {
          if (loadId !== this.dashboardLoadId) return;
          console.error('Income hierarchy API error:', err);
          this.isIncomeHierarchyLoading = false;
          this.incomeHierarchyError = 'Could not load the income breakdown. Please try again.';
        }
      });
  }

  loadInvestmentHierarchy(): void {
    if (this.investmentHierarchyData || this.isInvestmentHierarchyLoading) return;

    const loadId = this.dashboardLoadId;
    this.isInvestmentHierarchyLoading = true;
    this.investmentHierarchyError = null;
    this.http.get<HierarchyResponse>(
      `${this.API_BASE}/api/categories/hierarchy${this.getDateParams('investment')}`
    ).pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          if (loadId !== this.dashboardLoadId) return;
          this.isInvestmentHierarchyLoading = false;
          if (!data.success) {
            this.investmentHierarchyError = data.message || 'Could not load the investment breakdown.';
            return;
          }
          this.investmentHierarchyData = data;
          this.investmentTopCategories = data.hierarchy.map(category => ({
            name: category.name,
            amount: category.amount,
            averageMonthlyAmount: category.averageMonthlyAmount,
            percentage: category.percentage,
            icon: category.icon,
            color: category.color
          }));
          if (this.isInvestmentView) {
            this.createCategoryChart();
            this.createAverageChart();
          }
        },
        error: (err) => {
          if (loadId !== this.dashboardLoadId) return;
          console.error('Investment hierarchy API error:', err);
          this.isInvestmentHierarchyLoading = false;
          this.investmentHierarchyError = 'Could not load the investment breakdown. Please try again.';
        }
      });
  }

  private getDateParams(type: BreakdownType = 'expense'): string {
    const typeParam = `transaction_type=${type}`;
    if (this.selectedDateRange === 'all') {
      return `?${typeParam}`;
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
          return `?start_date=${this.formatDate(this.customStartDate)}&end_date=${this.formatDate(this.customEndDate)}&${typeParam}`;
        }
        return `?${typeParam}`;
      default:
        return `?${typeParam}`;
    }
    
    return `?start_date=${this.formatDate(startDate)}&end_date=${this.formatDate(now)}&${typeParam}`;
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

  private loadFallbackData(loadId: number): void {
    this.http.get<DashboardSummary>(`${this.API_BASE}/api/dashboard/summary`)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          if (loadId !== this.dashboardLoadId) return;
          this.summary = data;
          this.isLoading = false;
          setTimeout(() => this.createCharts(), 100);
        },
        error: () => {
          if (loadId !== this.dashboardLoadId) return;
          this.error = 'Could not connect to the server. Please make sure the backend is running.';
          this.isLoading = false;
        }
      });
  }

  private createCharts(): void {
    if (!this.summary) return;
    this.createTrendChart();
    this.createCategoryChart();
    this.createAverageChart();
  }

  private createTrendChart(): void {
    const canvas = document.getElementById('trendChart') as HTMLCanvasElement;
    if (!canvas || !this.summary) return;

    this.trendChart?.destroy();

    let months: string[];
    let incomeData: number[];
    let expenseData: number[];
    let investmentData: number[];

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
      investmentData = this.summary.monthlyTrend.map(t => t.investments || 0);
    } else {
      const now = new Date();
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      months = [monthNames[now.getMonth()]];
      incomeData = [this.summary.totalIncome];
      expenseData = [this.summary.totalExpenses];
      investmentData = [this.summary.totalInvestments];
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
          },
          {
            label: 'Investments',
            data: investmentData,
            borderColor: '#2196F3',
            backgroundColor: 'rgba(33, 150, 243, 0.1)',
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

  private createAverageChart(): void {
    const canvas = document.getElementById('averageChart') as HTMLCanvasElement;
    if (!canvas) return;

    this.averageChart?.destroy();
    this.averageChartData = this.getAverageChartDataForCurrentLevel();
    if (!this.averageChartData.length) return;

    this.averageChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: this.averageChartData.map(item => item.name),
        datasets: [{
          label: 'Average per month',
          data: this.averageChartData.map(item => item.averageMonthlyAmount),
          backgroundColor: this.averageChartData.map(item => item.color),
          borderRadius: 8,
          borderSkipped: false,
          barThickness: 22,
          maxBarThickness: 28
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: { right: 18 }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) =>
                ` ${this.formatCurrency(Number(context.parsed.x))} / month`
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            grid: { color: 'rgba(28, 42, 72, 0.06)' },
            ticks: {
              callback: (value) => '₹' + Number(value).toLocaleString('en-IN')
            }
          },
          y: {
            grid: { display: false },
            ticks: {
              color: '#344054',
              font: { size: 12, weight: 500 }
            }
          }
        },
        onClick: (_event: ChartEvent, elements: ActiveElement[]) => {
          if (elements.length) this.handleAverageChartClick(elements[0].index);
        }
      }
    });
  }

  private getAverageChartDataForCurrentLevel(): any[] {
    if (!this.activeHierarchyData?.hierarchy) {
      if (this.isIncomeView || this.isInvestmentView) return [];
      return (this.summary?.topCategories || []).map(category => ({
        ...category,
        id: category.name.replace(/\s+/g, '_').toLowerCase()
      }));
    }

    const hierarchy = this.activeHierarchyData.hierarchy;
    switch (this.averageDrillState.level) {
      case 'category':
        return hierarchy.map(category => ({
          id: category.id,
          name: category.name,
          averageMonthlyAmount: category.averageMonthlyAmount,
          color: category.color
        }));
      case 'subcategory': {
        const category = hierarchy.find(item => item.id === this.averageDrillState.categoryId);
        return (category?.subcategories || []).map(subcategory => ({
          id: subcategory.id,
          name: subcategory.name,
          averageMonthlyAmount: subcategory.averageMonthlyAmount,
          color: subcategory.color
        }));
      }
      case 'merchant': {
        const category = hierarchy.find(item => item.id === this.averageDrillState.categoryId);
        const subcategory = category?.subcategories.find(
          item => item.id === this.averageDrillState.subcategoryId
        );
        return (subcategory?.merchants || []).map(merchant => ({
          id: merchant.name,
          name: merchant.name,
          averageMonthlyAmount: merchant.averageMonthlyAmount,
          color: merchant.color
        }));
      }
      default:
        return [];
    }
  }

  handleAverageChartClick(index: number): void {
    const clickedItem = this.averageChartData[index];
    if (!clickedItem) return;

    switch (this.averageDrillState.level) {
      case 'category':
        this.averageDrillState = {
          level: 'subcategory',
          categoryId: clickedItem.id,
          categoryName: clickedItem.name,
          subcategoryId: null,
          subcategoryName: null
        };
        this.createAverageChart();
        break;
      case 'subcategory':
        this.averageDrillState = {
          ...this.averageDrillState,
          level: 'merchant',
          subcategoryId: clickedItem.id,
          subcategoryName: clickedItem.name
        };
        this.createAverageChart();
        break;
      case 'merchant':
        this.openTransactionDrawer(clickedItem, this.averageDrillState);
        break;
    }
  }

  drillUpAverage(): void {
    if (this.averageDrillState.level === 'merchant') {
      this.averageDrillState = {
        ...this.averageDrillState,
        level: 'subcategory',
        subcategoryId: null,
        subcategoryName: null
      };
    } else if (this.averageDrillState.level === 'subcategory') {
      this.resetAverageDrillState();
    }
    this.createAverageChart();
  }

  resetAverageDrillState(): void {
    this.averageDrillState = {
      level: 'category',
      categoryId: null,
      categoryName: null,
      subcategoryId: null,
      subcategoryName: null
    };
  }

  getAverageBreadcrumb(): string[] {
    const crumbs = ['All Categories'];
    if (this.averageDrillState.categoryName) crumbs.push(this.averageDrillState.categoryName);
    if (this.averageDrillState.subcategoryName) crumbs.push(this.averageDrillState.subcategoryName);
    return crumbs;
  }

  onAverageBreadcrumbClick(index: number): void {
    if (index === 0) {
      this.resetAverageDrillState();
      this.createAverageChart();
    } else if (index === 1 && this.averageDrillState.level === 'merchant') {
      this.drillUpAverage();
    }
  }

  private getChartDataForCurrentLevel(): any[] {
    if (!this.activeHierarchyData?.hierarchy) {
      // Fallback to summary data (expenses only)
      if (!this.isIncomeView && !this.isInvestmentView && this.summary?.topCategories) {
        return this.summary.topCategories.filter(c => c.name !== 'Income');
      }
      return [];
    }

    const hierarchy = this.activeHierarchyData.hierarchy;

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

  openTransactionDrawer(item: any, drillState: DrillState = this.drillState): void {
    if (!drillState.categoryName || !drillState.subcategoryName) return;
    this.loadDrawerTransactions(
      `${this.API_BASE}/api/categories/transactions-by-category`,
      {
        category: drillState.categoryName,
        subcategory: drillState.subcategoryName,
        merchant: item.name
      },
      `${item.name} - Transactions`
    );
  }

  openCategoryTransactions(categoryData: any): void {
    this.loadDrawerTransactions(
      `${this.API_BASE}/api/categories/transactions-by-category`,
      { category: categoryData.name },
      `${categoryData.name} - All Transactions`
    );
  }

  private loadDrawerTransactions(
    endpoint: string,
    filters: { category: string; subcategory?: string; merchant?: string },
    title: string
  ): void {
    this.drawerFilters = filters;
    this.drawerOffset = 0;
    this.drawerTotal = 0;
    this.drawerTransactions = [];
    this.drawerTitle = title;
    this.isDrawerOpen = true;
    this.drawerLoading = true;
    this.drawerLoadingMore = false;
    this.drawerError = null;
    this.fetchDrawerPage(endpoint, true);
  }

  loadMoreDrawerTransactions(): void {
    if (this.drawerLoadingMore || this.drawerLoading || this.drawerTransactions.length >= this.drawerTotal) return;
    this.fetchDrawerPage(`${this.API_BASE}/api/categories/transactions-by-category`, false);
  }

  private fetchDrawerPage(endpoint: string, initialLoad: boolean): void {
    if (!this.drawerFilters) return;
    const dateFilters = new URLSearchParams(this.getDateParams().replace(/^\?/, ''));
    const params = new URLSearchParams({
      category: this.drawerFilters.category,
      limit: String(this.drawerPageSize),
      offset: String(this.drawerOffset)
    });
    if (this.drawerFilters.subcategory) params.set('subcategory', this.drawerFilters.subcategory);
    if (this.drawerFilters.merchant) params.set('merchant', this.drawerFilters.merchant);
    for (const key of ['start_date', 'end_date']) {
      const value = dateFilters.get(key);
      if (value) params.set(key, value);
    }

    this.drawerLoading = initialLoad;
    this.drawerLoadingMore = !initialLoad;
    this.http.get<{ transactions: TransactionItem[]; total: number }>(`${endpoint}?${params.toString()}`)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          const page = data.transactions || [];
          this.drawerTransactions = initialLoad ? page : [...this.drawerTransactions, ...page];
          this.drawerTotal = data.total ?? this.drawerTransactions.length;
          this.drawerOffset += page.length;
          this.drawerLoading = false;
          this.drawerLoadingMore = false;
        },
        error: (error) => {
          console.error('Unable to load category transactions:', error);
          this.drawerError = 'Could not load transactions. Please try again.';
          this.drawerLoading = false;
          this.drawerLoadingMore = false;
        }
      });
  }

  closeDrawer(): void {
    this.isDrawerOpen = false;
    this.drawerTransactions = [];
    this.drawerTotal = 0;
    this.drawerFilters = null;
    this.drawerOffset = 0;
    this.drawerError = null;
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

  get isIncomeView(): boolean {
    return this.breakdownType === 'income';
  }

  get isInvestmentView(): boolean {
    return this.breakdownType === 'investment';
  }

  get isActiveHierarchyLoading(): boolean {
    if (this.isIncomeView) return this.isIncomeHierarchyLoading;
    if (this.isInvestmentView) return this.isInvestmentHierarchyLoading;
    return false;
  }

  get activeHierarchyError(): string | null {
    if (this.isIncomeView) return this.incomeHierarchyError;
    if (this.isInvestmentView) return this.investmentHierarchyError;
    return null;
  }

  get activeBreakdownLabel(): string {
    if (this.isIncomeView) return 'Income';
    if (this.isInvestmentView) return 'Investments';
    return 'Expenses';
  }

  get activeLoadingMessage(): string {
    return `Loading ${this.activeBreakdownLabel.toLowerCase()} breakdown...`;
  }

  get activeNoDataMessage(): string {
    if (this.isIncomeView) return 'No income for this period';
    if (this.isInvestmentView) return 'No investments for this period';
    return 'No expense categories for this period';
  }

  get activeUnavailableMessage(): string {
    return `${this.activeBreakdownLabel} breakdowns are unavailable.`;
  }

  retryActiveHierarchy(): void {
    if (this.isIncomeView) this.loadIncomeHierarchy();
    else if (this.isInvestmentView) this.loadInvestmentHierarchy();
  }

  get activeHierarchyData(): HierarchyResponse | null {
    if (this.isIncomeView) return this.incomeHierarchyData;
    if (this.isInvestmentView) return this.investmentHierarchyData;
    return this.hierarchyData;
  }

  // Categories listed under "Top ..." follow the active breakdown.
  get topCategoryList(): CategoryData[] {
    if (this.isIncomeView) return this.incomeTopCategories;
    if (this.isInvestmentView) return this.investmentTopCategories;
    return this.summary?.topCategories || [];
  }

  setBreakdownType(type: BreakdownType): void {
    if (type === this.breakdownType) return;
    this.breakdownType = type;
    this.resetDrillState();
    this.resetAverageDrillState();
    this.closeDrawer();
    this.createCategoryChart();
    this.createAverageChart();
    if (type === 'income' && !this.incomeHierarchyData) this.loadIncomeHierarchy();
    if (type === 'investment' && !this.investmentHierarchyData) this.loadInvestmentHierarchy();
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
