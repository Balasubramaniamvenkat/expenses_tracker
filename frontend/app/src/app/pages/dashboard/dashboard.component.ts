import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { HttpClient } from '@angular/common/http';
import { Subject, takeUntil } from 'rxjs';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

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
  topCategories: Array<{
    name: string;
    amount: number;
    percentage: number;
    icon: string;
    color: string;
  }>;
  monthlyTrend: Array<{
    month: string;
    income: number;
    expenses: number;
  }>;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDividerModule
  ],
  template: `
    <div class="dashboard-container">
      <!-- Header -->
      <div class="dashboard-header">
        <div class="header-content">
          <h1>
            <mat-icon>dashboard</mat-icon>
            Financial Dashboard
          </h1>
          <p class="subtitle" *ngIf="summary">
            {{ summary.dateRange.from | date:'MMM yyyy' }} - {{ summary.dateRange.to | date:'MMM yyyy' }}
          </p>
        </div>
        <button mat-raised-button color="primary" routerLink="/upload">
          <mat-icon>cloud_upload</mat-icon>
          Upload Statement
        </button>
      </div>

      <!-- Loading State -->
      <div class="loading-container" *ngIf="isLoading">
        <mat-spinner diameter="50"></mat-spinner>
        <p>Loading your financial data...</p>
      </div>

      <!-- Error State -->
      <div class="error-container" *ngIf="error && !isLoading">
        <mat-icon>error_outline</mat-icon>
        <h3>Unable to load data</h3>
        <p>{{ error }}</p>
        <button mat-raised-button color="primary" (click)="loadDashboardData()">
          <mat-icon>refresh</mat-icon>
          Retry
        </button>
      </div>

      <!-- Dashboard Content -->
      <div class="dashboard-content" *ngIf="!isLoading && !error && summary">
        <!-- Summary Cards -->
        <div class="summary-cards">
          <mat-card class="summary-card income">
            <mat-card-content>
              <div class="card-icon">
                <mat-icon>trending_up</mat-icon>
              </div>
              <div class="card-info">
                <span class="card-label">Total Income</span>
                <span class="card-value">₹{{ summary.totalIncome | number:'1.0-0' }}</span>
              </div>
            </mat-card-content>
          </mat-card>

          <mat-card class="summary-card expenses">
            <mat-card-content>
              <div class="card-icon">
                <mat-icon>trending_down</mat-icon>
              </div>
              <div class="card-info">
                <span class="card-label">Total Expenses</span>
                <span class="card-value">₹{{ summary.totalExpenses | number:'1.0-0' }}</span>
              </div>
            </mat-card-content>
          </mat-card>

          <mat-card class="summary-card investments">
            <mat-card-content>
              <div class="card-icon">
                <mat-icon>savings</mat-icon>
              </div>
              <div class="card-info">
                <span class="card-label">Investments</span>
                <span class="card-value">₹{{ summary.totalInvestments | number:'1.0-0' }}</span>
              </div>
            </mat-card-content>
          </mat-card>

          <mat-card class="summary-card savings" [class.negative]="summary.netSavings < 0">
            <mat-card-content>
              <div class="card-icon">
                <mat-icon>{{ summary.netSavings >= 0 ? 'account_balance_wallet' : 'warning' }}</mat-icon>
              </div>
              <div class="card-info">
                <span class="card-label">Net Savings</span>
                <span class="card-value">₹{{ summary.netSavings | number:'1.0-0' }}</span>
              </div>
            </mat-card-content>
          </mat-card>
        </div>

        <!-- Charts Section -->
        <div class="charts-section">
          <!-- Monthly Trend Chart -->
          <mat-card class="chart-card">
            <mat-card-header>
              <mat-card-title>
                <mat-icon>show_chart</mat-icon>
                Monthly Income vs Expenses
              </mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="chart-wrapper">
                <canvas id="trendChart"></canvas>
              </div>
            </mat-card-content>
          </mat-card>

          <!-- Category Breakdown Chart -->
          <mat-card class="chart-card">
            <mat-card-header>
              <mat-card-title>
                <mat-icon>pie_chart</mat-icon>
                Expense Categories
              </mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="chart-wrapper">
                <canvas id="categoryChart"></canvas>
              </div>
            </mat-card-content>
          </mat-card>
        </div>

        <!-- Top Categories List -->
        <mat-card class="categories-card">
          <mat-card-header>
            <mat-card-title>
              <mat-icon>category</mat-icon>
              Top Spending Categories
            </mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="category-list">
              <div class="category-item" *ngFor="let cat of summary.topCategories">
                <div class="category-icon" [style.background-color]="cat.color + '20'" [style.color]="cat.color">
                  {{ cat.icon }}
                </div>
                <div class="category-info">
                  <span class="category-name">{{ cat.name }}</span>
                  <div class="category-bar">
                    <div class="bar-fill" [style.width.%]="cat.percentage" [style.background-color]="cat.color"></div>
                  </div>
                </div>
                <div class="category-amount">
                  <span class="amount">₹{{ cat.amount | number:'1.0-0' }}</span>
                  <span class="percentage">{{ cat.percentage | number:'1.1-1' }}%</span>
                </div>
              </div>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- Quick Stats -->
        <mat-card class="stats-card">
          <mat-card-header>
            <mat-card-title>
              <mat-icon>insights</mat-icon>
              Quick Stats
            </mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="stats-grid">
              <div class="stat-item">
                <mat-icon>receipt_long</mat-icon>
                <span class="stat-value">{{ summary.transactionCount }}</span>
                <span class="stat-label">Transactions</span>
              </div>
              <div class="stat-item">
                <mat-icon>calendar_month</mat-icon>
                <span class="stat-value">{{ getMonthsCount() }}</span>
                <span class="stat-label">Months of Data</span>
              </div>
              <div class="stat-item">
                <mat-icon>percent</mat-icon>
                <span class="stat-value">{{ getSavingsRate() | number:'1.0-0' }}%</span>
                <span class="stat-label">Savings Rate</span>
              </div>
              <div class="stat-item">
                <mat-icon>avg_pace</mat-icon>
                <span class="stat-value">₹{{ getAvgDailyExpense() | number:'1.0-0' }}</span>
                <span class="stat-label">Avg Daily Expense</span>
              </div>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <!-- Empty State -->
      <div class="empty-state" *ngIf="!isLoading && !error && !summary">
        <mat-icon>account_balance_wallet</mat-icon>
        <h2>Welcome to Family Finance Tracker!</h2>
        <p>Upload your bank statement to get started with tracking your finances.</p>
        <button mat-raised-button color="primary" routerLink="/upload">
          <mat-icon>cloud_upload</mat-icon>
          Upload Your First Statement
        </button>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 24px;
      max-width: 1400px;
      margin: 0 auto;
      min-height: calc(100vh - 80px);
    }

    .dashboard-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }

    .header-content h1 {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 0;
      font-size: 28px;
      font-weight: 600;
      color: #1a1a2e;
    }

    .header-content h1 mat-icon {
      font-size: 32px;
      width: 32px;
      height: 32px;
      color: #667eea;
    }

    .subtitle {
      margin: 4px 0 0 44px;
      color: #666;
      font-size: 14px;
    }

    /* Loading & Error States */
    .loading-container, .error-container, .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 80px 24px;
      text-align: center;
    }

    .loading-container p, .error-container p {
      margin-top: 16px;
      color: #666;
    }

    .error-container mat-icon, .empty-state mat-icon {
      font-size: 64px;
      width: 64px;
      height: 64px;
      color: #ccc;
    }

    .error-container h3, .empty-state h2 {
      margin: 16px 0 8px;
      color: #333;
    }

    .error-container button, .empty-state button {
      margin-top: 16px;
    }

    /* Summary Cards */
    .summary-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
    }

    .summary-card {
      border-radius: 16px;
      overflow: hidden;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .summary-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }

    .summary-card mat-card-content {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 20px;
    }

    .card-icon {
      width: 56px;
      height: 56px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .card-icon mat-icon {
      font-size: 28px;
      width: 28px;
      height: 28px;
      color: white;
    }

    .income .card-icon { background: linear-gradient(135deg, #4CAF50, #2E7D32); }
    .expenses .card-icon { background: linear-gradient(135deg, #FF9800, #F57C00); }
    .investments .card-icon { background: linear-gradient(135deg, #2196F3, #1565C0); }
    .savings .card-icon { background: linear-gradient(135deg, #9C27B0, #6A1B9A); }
    .savings.negative .card-icon { background: linear-gradient(135deg, #f44336, #c62828); }

    .card-info {
      display: flex;
      flex-direction: column;
    }

    .card-label {
      font-size: 14px;
      color: #666;
      margin-bottom: 4px;
    }

    .card-value {
      font-size: 24px;
      font-weight: 700;
      color: #1a1a2e;
    }

    /* Charts Section */
    .charts-section {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
    }

    .chart-card {
      border-radius: 16px;
    }

    .chart-card mat-card-header {
      padding: 16px 20px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
    }

    .chart-card mat-card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      margin: 0;
    }

    .chart-wrapper {
      padding: 20px;
      height: 300px;
    }

    /* Categories Card */
    .categories-card {
      border-radius: 16px;
      margin-bottom: 24px;
    }

    .categories-card mat-card-header {
      padding: 16px 20px;
    }

    .categories-card mat-card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 18px;
      color: #1a1a2e;
    }

    .category-list {
      padding: 8px 0;
    }

    .category-item {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 12px 20px;
      border-bottom: 1px solid #f0f0f0;
    }

    .category-item:last-child {
      border-bottom: none;
    }

    .category-icon {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
    }

    .category-info {
      flex: 1;
    }

    .category-name {
      display: block;
      font-weight: 500;
      margin-bottom: 6px;
      color: #333;
    }

    .category-bar {
      height: 6px;
      background: #f0f0f0;
      border-radius: 3px;
      overflow: hidden;
    }

    .bar-fill {
      height: 100%;
      border-radius: 3px;
      transition: width 0.5s ease;
    }

    .category-amount {
      text-align: right;
    }

    .category-amount .amount {
      display: block;
      font-weight: 600;
      color: #1a1a2e;
    }

    .category-amount .percentage {
      font-size: 12px;
      color: #888;
    }

    /* Stats Card */
    .stats-card {
      border-radius: 16px;
    }

    .stats-card mat-card-header {
      padding: 16px 20px;
    }

    .stats-card mat-card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 18px;
      color: #1a1a2e;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 24px;
      padding: 20px;
    }

    .stat-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: 16px;
      background: #f8f9fa;
      border-radius: 12px;
    }

    .stat-item mat-icon {
      font-size: 28px;
      width: 28px;
      height: 28px;
      color: #667eea;
      margin-bottom: 8px;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: #1a1a2e;
    }

    .stat-label {
      font-size: 12px;
      color: #666;
      margin-top: 4px;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .dashboard-container {
        padding: 16px;
      }

      .dashboard-header {
        flex-direction: column;
        align-items: flex-start;
      }

      .header-content h1 {
        font-size: 22px;
      }

      .charts-section {
        grid-template-columns: 1fr;
      }

      .chart-wrapper {
        height: 250px;
      }
    }
  `]
})
export class DashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private trendChart: Chart | null = null;
  private categoryChart: Chart | null = null;

  summary: DashboardSummary | null = null;
  isLoading = true;
  error: string | null = null;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadDashboardData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.trendChart?.destroy();
    this.categoryChart?.destroy();
  }

  loadDashboardData(): void {
    this.isLoading = true;
    this.error = null;

    this.http.get<DashboardSummary>('http://localhost:8000/api/dashboard/summary')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.summary = data;
          this.isLoading = false;
          // Wait for view to render before creating charts
          setTimeout(() => this.createCharts(), 100);
        },
        error: (err) => {
          console.error('Dashboard API error:', err);
          // Try to load with fallback data
          this.loadFallbackData();
        }
      });
  }

  private loadFallbackData(): void {
    // Load from categories API as fallback
    this.http.get<any>('http://localhost:8000/api/categories/analytics')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.summary = this.transformCategoryData(data);
          this.isLoading = false;
          setTimeout(() => this.createCharts(), 100);
        },
        error: () => {
          this.error = 'Could not connect to the server. Please make sure the backend is running.';
          this.isLoading = false;
        }
      });
  }

  private transformCategoryData(data: any[]): DashboardSummary {
    const income = data.find(d => d.category_id === 'income')?.monthly_amount || 0;
    const expenses = data.find(d => d.category_id === 'expenditure')?.monthly_amount || 0;
    const investments = data.find(d => d.category_id === 'investment')?.monthly_amount || 0;

    return {
      totalIncome: income,
      totalExpenses: expenses,
      totalInvestments: investments,
      netSavings: income - expenses,
      transactionCount: 757,
      dateRange: {
        from: '2024-01-01',
        to: '2025-01-01'
      },
      topCategories: data.map(d => ({
        name: d.category_name,
        amount: d.monthly_amount,
        percentage: d.percentage_of_income || 0,
        icon: d.icon || '📊',
        color: d.color || '#667eea'
      })),
      monthlyTrend: []
    };
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

    // Use actual monthly trend data from API
    let months: string[];
    let incomeData: number[];
    let expenseData: number[];

    if (this.summary.monthlyTrend && this.summary.monthlyTrend.length > 0) {
      // Use real data from API
      months = this.summary.monthlyTrend.map(t => {
        // Format "2024-11" to "Nov '24" for clarity when spanning multiple years
        const parts = t.month.split('-');
        if (parts.length === 2) {
          const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
          const monthIndex = parseInt(parts[1], 10) - 1;
          const year = parts[0].slice(-2); // Get last 2 digits of year
          return `${monthNames[monthIndex]} '${year}`;
        }
        return t.month;
      });
      incomeData = this.summary.monthlyTrend.map(t => t.income);
      expenseData = this.summary.monthlyTrend.map(t => t.expenses);
    } else {
      // Fallback: show single current month with totals
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
    if (!canvas || !this.summary) return;

    this.categoryChart?.destroy();

    const categories = this.summary.topCategories.filter(c => c.name !== 'Income');

    this.categoryChart = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: categories.map(c => c.name),
        datasets: [{
          data: categories.map(c => c.amount),
          backgroundColor: categories.map(c => c.color),
          borderWidth: 2,
          borderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right'
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = context.parsed;
                return `${context.label}: ₹${value.toLocaleString('en-IN')}`;
              }
            }
          }
        }
      }
    });
  }

  getMonthsCount(): number {
    if (!this.summary?.dateRange) return 0;
    const from = new Date(this.summary.dateRange.from);
    const to = new Date(this.summary.dateRange.to);
    return Math.ceil((to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24 * 30));
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
}
