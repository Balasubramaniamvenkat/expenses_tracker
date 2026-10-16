import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { Subject, takeUntil } from 'rxjs';
import { Chart, ChartConfiguration, ChartType, registerables } from 'chart.js';
import { CategoryService, SimpleCategoryData } from '../../services/category.service';

// Register Chart.js components
Chart.register(...registerables);

@Component({
  selector: 'app-monthly-bar-chart',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatProgressSpinnerModule,
    MatIconModule
  ],
  template: `
    <div class="chart-container">
      <mat-card class="chart-card">
        <mat-card-header>
          <mat-card-title>
            <mat-icon>bar_chart</mat-icon>
            Monthly Category Averages
          </mat-card-title>
          <mat-card-subtitle>Income, Expenditure, Investment & Education</mat-card-subtitle>
        </mat-card-header>
        
        <mat-card-content>
          <div class="chart-wrapper" *ngIf="!isLoading && !errorMessage && categoryData.length > 0; else loadingTemplate">
            <canvas #chartCanvas id="monthlyBarChart"></canvas>
          </div>
          
          <ng-template #loadingTemplate>
            <div class="loading-container" *ngIf="isLoading">
              <mat-spinner diameter="50"></mat-spinner>
              <p>Loading category data...</p>
            </div>
          </ng-template>
          <p class="error-message" *ngIf="!isLoading && errorMessage">{{ errorMessage }}</p>
          
          <!-- Summary Cards -->
          <div class="summary-cards" *ngIf="!isLoading && categoryData.length > 0">
            <div class="summary-card" *ngFor="let category of categoryData">
              <div class="category-icon">{{ category.icon }}</div>
              <div class="category-info">
                <h4>{{ category.category_name }}</h4>
                <p class="amount">₹{{ category.monthly_amount | number:'1.0-0' }}</p>
                <p class="percentage">{{ category.percentage_of_income }}% of income</p>
              </div>
              <div class="trend-indicator" [class]="'trend-' + category.trend">
                <mat-icon>{{ getTrendIcon(category.trend) }}</mat-icon>
                <span>{{ category.trend_value }}%</span>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .chart-container {
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }

    .chart-card {
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      border-radius: 12px;
    }

    .chart-card mat-card-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 12px 12px 0 0;
    }

    .chart-card mat-card-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 1.5rem;
      margin: 0;
    }

    .chart-card mat-card-subtitle {
      color: rgba(255, 255, 255, 0.8);
      margin-top: 5px;
    }

    .chart-wrapper {
      position: relative;
      height: 400px;
      margin: 20px 0;
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 60px 20px;
      gap: 20px;
    }

    .loading-container p {
      color: #666;
      font-size: 1.1rem;
    }

    .summary-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-top: 24px;
    }

    .summary-card {
      background: #f8f9fa;
      border-radius: 8px;
      padding: 16px;
      display: flex;
      align-items: center;
      gap: 16px;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .summary-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .category-icon {
      font-size: 2rem;
      width: 60px;
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: white;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .category-info {
      flex: 1;
    }

    .category-info h4 {
      margin: 0 0 4px 0;
      color: #333;
      font-weight: 600;
    }

    .amount {
      font-size: 1.2rem;
      font-weight: 700;
      color: #2196F3;
      margin: 0;
    }

    .percentage {
      font-size: 0.9rem;
      color: #666;
      margin: 0;
    }

    .trend-indicator {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 0.9rem;
      font-weight: 600;
      padding: 4px 8px;
      border-radius: 4px;
    }

    .trend-up {
      color: #4CAF50;
      background: rgba(76, 175, 80, 0.1);
    }

    .trend-down {
      color: #f44336;
      background: rgba(244, 67, 54, 0.1);
    }

    .trend-stable {
      color: #FF9800;
      background: rgba(255, 152, 0, 0.1);
    }

    /* Responsive design */
    @media (max-width: 768px) {
      .chart-container {
        padding: 10px;
      }

      .summary-cards {
        grid-template-columns: 1fr;
      }

      .chart-wrapper {
        height: 300px;
      }
    }
  `]
})
export class MonthlyBarChartComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  chart: Chart | null = null;
  categoryData: SimpleCategoryData[] = [];
  isLoading = true;
  errorMessage: string | null = null;

  constructor(private categoryService: CategoryService) {}

  ngOnInit() {
    this.loadCategoryData();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
    
    if (this.chart) {
      this.chart.destroy();
    }
  }

  private loadCategoryData() {
    this.isLoading = true;
    this.errorMessage = null;
    console.log('🚀 Loading category data...');
    
    // Use a wide date range to capture all available data
    // The backend will calculate averages from whatever data is available
    const endDate = new Date();
    const startDate = new Date('2024-01-01'); // Start from beginning of data

    const dateRange = { startDate, endDate };
    console.log('📅 Date range:', dateRange);
    
    this.categoryService.getCategoryAnalytics(dateRange)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          console.log('✅ Received category data from API:', data);
          
          // Filter for the 4 required categories
          const targetCategories = ['income', 'expenditure', 'investment', 'education'];
          this.categoryData = data.filter(item => 
            targetCategories.includes(item.category_id?.toLowerCase())
          );
          
          console.log('🎯 Filtered data for target categories:', this.categoryData);
          
          if (this.categoryData.length === 0) {
            this.errorMessage = 'No category data is available for this date range.';
          }
          
          // Log the actual amounts being displayed
          console.log('💰 Amounts being displayed:');
          this.categoryData.forEach(item => {
            console.log(`  - ${item.category_name}: ₹${item.monthly_amount.toLocaleString()}`);
          });
          
          this.isLoading = false;
          
          if (this.categoryData.length > 0) {
            setTimeout(() => this.createChart(), 100);
          }
        },
        error: (error) => {
          console.error('❌ Error loading category data:', error);
          this.errorMessage = 'Could not load category data from the server.';
          this.isLoading = false;
        }
      });
  }

  private createChart() {
    const canvas = document.getElementById('monthlyBarChart') as HTMLCanvasElement;
    if (!canvas) return;

    // Destroy existing chart if it exists
    if (this.chart) {
      this.chart.destroy();
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const chartConfig: ChartConfiguration = {
      type: 'bar' as ChartType,
      data: {
        labels: this.categoryData.map(item => item.category_name),
        datasets: [{
          label: 'Monthly Average (₹)',
          data: this.categoryData.map(item => item.monthly_amount),
          backgroundColor: this.categoryData.map(item => item.color + '80'), // Add transparency
          borderColor: this.categoryData.map(item => item.color),
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Monthly Category Averages',
            font: {
              size: 16,
              weight: 'bold'
            },
            padding: 20
          },
          legend: {
            display: true,
            position: 'top',
            labels: {
              usePointStyle: true,
              padding: 20
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = context.parsed.y;
                const category = this.categoryData[context.dataIndex];
                return [
                  `${category.category_name}: ₹${value.toLocaleString()}`,
                  `${category.percentage_of_income}% of income`,
                  `Trend: ${category.trend} ${category.trend_value}%`
                ];
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => '₹' + (value as number).toLocaleString()
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        },
        animation: {
          duration: 1000,
          easing: 'easeInOutQuart'
        }
      }
    };

    this.chart = new Chart(ctx, chartConfig);
  }

  getTrendIcon(trend: string): string {
    switch (trend) {
      case 'up': return 'trending_up';
      case 'down': return 'trending_down';
      case 'stable': return 'trending_flat';
      default: return 'trending_flat';
    }
  }
}
