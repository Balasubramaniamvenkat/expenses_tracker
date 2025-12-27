import { Component, OnInit, ViewChild, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatDatepickerModule, MatDatepickerInputEvent } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Transaction, TransactionFilter, TransactionSummary } from '../../../../models/transaction.model';
import { TransactionService, FilterOptions, TransactionMetrics, TimelineData, TransactionListResponse } from '../../services/transaction.service';
import { debounceTime, distinctUntilChanged, map } from 'rxjs/operators';
import { Subscription, Subject } from 'rxjs';

// Helper function to compare filter values for distinctUntilChanged
function compareFilters(prev: any, curr: any): boolean {
  return JSON.stringify(prev) === JSON.stringify(curr);
}
import Chart from 'chart.js/auto';
import { ChartConfiguration, ChartOptions, ChartData } from 'chart.js';

@Component({
  selector: 'app-transaction-list',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatProgressSpinnerModule,
    MatTooltipModule
  ],
  templateUrl: './transaction-list.component.html',
  styleUrls: ['./transaction-list.component.scss']
})
export class TransactionListComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  displayedColumns: string[] = [
    'date', 
    'description', 
    'category', 
    'amount', 
    'account',
    'balance'
  ];

  dataSource = new MatTableDataSource<Transaction>([]);
  filterForm: FormGroup;
  metrics: TransactionMetrics | null = null;
  timelineData: TimelineData | null = null;
  timelineChart: Chart | null = null;
  isLoading = false;
  
  // Filter options
  availableCategories: string[] = ['All Categories'];
  availableAccounts: string[] = ['All Accounts'];
  
  // Explicitly stored date strings for filtering
  private dateFromString: string | undefined = undefined;
  private dateToString: string | undefined = undefined;
  
  private filterSubscription: Subscription | null = null;
  private unsubscribe$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private transactionService: TransactionService
  ) {
    this.filterForm = this.fb.group({
      search_text: [''],
      date_from: [''],
      date_to: [''],
      categories: [['All Categories']],
      accounts: [['All Accounts']],
      amount_min: [''],
      amount_max: [''],
      page: [1],
      page_size: [50]
    });
  }

  ngOnInit(): void {
    this.loadTransactions();
    this.loadFilterOptions();
    this.setupFilterSubscription();
  }

  ngAfterViewInit(): void {
    // Note: We're doing SERVER-SIDE pagination, so we DO NOT connect
    // the dataSource to the paginator (that would enable client-side pagination)
    // this.dataSource.paginator = this.paginator;  // DISABLED for server-side pagination
    this.dataSource.sort = this.sort;
    
    // Listen for pagination events - we handle pagination manually via API calls
    if (this.paginator) {
      this.paginator.page.subscribe((event: PageEvent) => {
        this.filterForm.patchValue({
          page: event.pageIndex + 1,
          page_size: event.pageSize
        });
        this.loadTransactions();
      });
    }
    
    // Listen for sort events
    if (this.sort) {
      this.sort.sortChange.subscribe(() => {
        if (this.paginator) {
          this.paginator.pageIndex = 0;
          this.filterForm.patchValue({ page: 1 });
        }
        this.loadTransactions();
      });
    }

    // Initialize chart if data already exists
    if (this.timelineData) {
      // Use longer delay and requestAnimationFrame for better timing
      requestAnimationFrame(() => {
        setTimeout(() => this.renderTimelineChart(), 500);
      });
    }

    // Set up a resize listener for the chart
    window.addEventListener('resize', () => {
      if (this.timelineChart) {
        this.timelineChart.resize();
      }
    });

    // Debug: Add click listener to category select to check if it's working
    setTimeout(() => {
      const categorySelect = document.querySelector('.category-filter mat-select');
      if (categorySelect) {
        console.log('Category select found:', categorySelect);
        categorySelect.addEventListener('click', () => {
          console.log('Category select clicked');
          setTimeout(() => {
            const panel = document.querySelector('.mat-mdc-select-panel');
            console.log('Panel after click:', panel);
            if (panel) {
              console.log('Panel styles:', window.getComputedStyle(panel));
            }
          }, 100);
        });
      }
    }, 1000);
  }

  ngOnDestroy(): void {
    // Clean up any subscriptions
    this.unsubscribe$.next();
    this.unsubscribe$.complete();
    
    // Reset the state to avoid persistence issues
    this.dataSource.data = [];
    this.isLoading = false;
    
    if (this.filterSubscription) {
      this.filterSubscription.unsubscribe();
    }
    
    if (this.timelineChart) {
      this.timelineChart.destroy();
    }

    // Remove the resize listener
    window.removeEventListener('resize', () => {
      if (this.timelineChart) {
        this.timelineChart.resize();
      }
    });
    
    console.log('TransactionList component destroyed and cleaned up');
  }

  private setupFilterSubscription(): void {
    // Track previous filter values to detect actual filter changes (not pagination)
    let previousFilters: any = null;
    
    this.filterSubscription = this.filterForm.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged(compareFilters)
      )
      .subscribe((formValue) => {
        // Extract only the filter fields (exclude pagination fields)
        const currentFilters = {
          search_text: formValue.search_text,
          date_from: formValue.date_from,
          date_to: formValue.date_to,
          categories: formValue.categories,
          accounts: formValue.accounts,
          amount_min: formValue.amount_min,
          amount_max: formValue.amount_max
        };
        
        // Check if actual filters changed (not just pagination)
        const filtersChanged = JSON.stringify(currentFilters) !== JSON.stringify(previousFilters);
        
        if (filtersChanged) {
          console.log('Filter values changed (not pagination):', currentFilters);
          previousFilters = { ...currentFilters };
          
          // Reset to first page only when actual filters change
          if (this.paginator) {
            this.paginator.pageIndex = 0;
            this.filterForm.patchValue({ page: 1 }, { emitEvent: false });
          }
          this.loadTransactions();
        }
        // If only pagination changed, do nothing - pagination is handled by paginator.page subscription
      });
  }

  loadTransactions(): void {
    this.isLoading = true;
    const filters: TransactionFilter = this.getFilters();
    
    console.log('Component filters:', filters);
    console.log('Form value:', this.filterForm.value);
    
    // Get transactions
    this.transactionService.getFilteredTransactions(filters).subscribe({
      next: (response) => {
        console.log('=== Transactions Response ===');
        console.log('Full response:', response);
        console.log('Pagination:', response.pagination);
        console.log('Transactions count:', response.transactions?.length);
        
        // Ensure we have transactions array even if empty
        if (!response.transactions) {
          response.transactions = [];
        }
        
        this.dataSource.data = response.transactions;
        
        // Update paginator with server-side pagination info
        if (this.paginator && response.pagination) {
          console.log('Updating paginator - total_items:', response.pagination.total_items);
          this.paginator.length = response.pagination.total_items;
          this.paginator.pageSize = response.pagination.page_size;
          this.paginator.pageIndex = response.pagination.current_page - 1;
          console.log('Paginator after update - length:', this.paginator.length);
        }
        
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading transactions:', error);
        this.dataSource.data = []; // Set empty array on error
        this.isLoading = false;
      }
    });
    
    // Get metrics
    this.transactionService.getTransactionMetrics(filters).subscribe({
      next: (metrics) => {
        this.metrics = metrics;
      },
      error: (error) => {
        console.error('Error loading metrics:', error);
      }
    });
    
    // Get timeline data
    this.transactionService.getTransactionTimeline(filters).subscribe({
      next: (data) => {
        console.log('Timeline data received:', data);
        this.timelineData = data;
        
        // Check if we have valid data for the chart
        const hasValidData = data && 
            ((data.credits && data.credits.length > 0) || 
             (data.debits && data.debits.length > 0));
        
        console.log('Timeline has valid data:', hasValidData);
        
        // Wait for the next rendering cycle to make sure the DOM is ready
        // Use requestAnimationFrame for better timing
        requestAnimationFrame(() => {
          setTimeout(() => this.renderTimelineChart(), 100);
        });
      },
      error: (error) => {
        console.error('Error loading timeline data:', error);
        // Set empty data and still try to render an empty chart
        this.timelineData = { credits: [], debits: [] };
        requestAnimationFrame(() => {
          setTimeout(() => this.renderTimelineChart(), 100);
        });
      }
    });
  }

  private loadFilterOptions(): void {
    console.log('Loading filter options...');
    this.transactionService.getFilterOptions().subscribe({
      next: (options) => {
        console.log('Filter options received:', options);
        this.availableCategories = options.categories;
        this.availableAccounts = options.accounts;
        console.log('Available categories:', this.availableCategories);
        console.log('Available accounts:', this.availableAccounts);
      },
      error: (error) => {
        console.error('Error loading filter options:', error);
      }
    });
  }

  // Date change event handlers - capture dates directly when selected
  onDateFromChange(event: MatDatepickerInputEvent<Date>): void {
    if (event.value) {
      const d = event.value;
      this.dateFromString = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      console.log('Date FROM changed:', this.dateFromString);
    } else {
      this.dateFromString = undefined;
      console.log('Date FROM cleared');
    }
  }

  onDateToChange(event: MatDatepickerInputEvent<Date>): void {
    if (event.value) {
      const d = event.value;
      this.dateToString = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      console.log('Date TO changed:', this.dateToString);
    } else {
      this.dateToString = undefined;
      console.log('Date TO cleared');
    }
  }

  private getFilters(): TransactionFilter {
    const formValue = this.filterForm.value;
    
    // Use the explicitly stored date strings (most reliable)
    // Fall back to parsing form values if date strings not set
    let dateFrom: string | undefined = this.dateFromString;
    let dateTo: string | undefined = this.dateToString;
    
    // If dates not captured via event handlers, try to parse from form
    if (!dateFrom && formValue.date_from) {
      dateFrom = this.formatDateValue(formValue.date_from);
    }
    if (!dateTo && formValue.date_to) {
      dateTo = this.formatDateValue(formValue.date_to);
    }
    
    console.log('=== getFilters() ===');
    console.log('dateFromString (stored):', this.dateFromString);
    console.log('dateToString (stored):', this.dateToString);
    console.log('Final dateFrom:', dateFrom);
    console.log('Final dateTo:', dateTo);
    
    const filters: TransactionFilter = {
      search_text: formValue.search_text?.trim() || undefined,
      date_from: dateFrom,
      date_to: dateTo,
      categories: formValue.categories || ['All Categories'],
      accounts: formValue.accounts || ['All Accounts'],
      amount_min: formValue.amount_min !== null && formValue.amount_min !== '' ? formValue.amount_min : undefined,
      amount_max: formValue.amount_max !== null && formValue.amount_max !== '' ? formValue.amount_max : undefined,
      page: formValue.page || 1,
      page_size: formValue.page_size || 50
    };
    
    console.log('Generated filters:', filters);
    return filters;
  }

  // Helper function to convert any date-like value to YYYY-MM-DD string
  private formatDateValue(value: any): string | undefined {
    if (!value) return undefined;
    
    let d: Date;
    
    // Check if it's a Date object
    if (value instanceof Date) {
      d = value;
    }
    // Check if it's a Moment object (has toDate method)
    else if (value && typeof value.toDate === 'function') {
      d = value.toDate();
    }
    // Check if it's a string already in YYYY-MM-DD format
    else if (typeof value === 'string') {
      // If already in YYYY-MM-DD format, return as is
      if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        return value;
      }
      // Try to parse the string as a date
      d = new Date(value);
    }
    // Try converting to string and parsing
    else {
      d = new Date(String(value));
    }
    
    // Validate the date
    if (isNaN(d.getTime())) {
      console.warn('Invalid date value:', value);
      return undefined;
    }
    
    // Format as YYYY-MM-DD using local timezone
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  applyFilters(): void {
    console.log('Apply filters clicked, current form value:', this.filterForm.value);
    console.log('Date strings - from:', this.dateFromString, 'to:', this.dateToString);
    // Reset to first page when applying filters
    if (this.paginator) {
      this.paginator.pageIndex = 0;
    }
    this.filterForm.patchValue({ page: 1 }, { emitEvent: false });
    this.loadTransactions();
  }

  clearFilters(): void {
    console.log('Clearing all filters...');
    
    // Reset the stored date strings
    this.dateFromString = undefined;
    this.dateToString = undefined;
    
    // Reset paginator first
    if (this.paginator) {
      this.paginator.pageIndex = 0;
    }
    
    // Reset form to default values
    this.filterForm.reset({
      search_text: '',
      date_from: null,
      date_to: null,
      categories: ['All Categories'],
      accounts: ['All Accounts'],
      amount_min: null,
      amount_max: null,
      page: 1,
      page_size: 50
    }, { emitEvent: false });
    
    console.log('Filters cleared, form value:', this.filterForm.value);
    
    // Reload all data without filters
    this.loadTransactions();
  }

  exportTransactions(): void {
    const filters: TransactionFilter = this.getFilters();
    this.transactionService.exportTransactions(filters).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      },
      error: (error) => {
        console.error('Error exporting transactions:', error);
      }
    });
  }

  deleteTransaction(transaction: Transaction): void {
    if (confirm(`Are you sure you want to delete this transaction: ${transaction.description}?`)) {
      this.transactionService.deleteTransaction(transaction.id).subscribe({
        next: () => {
          this.loadTransactions();
        },
        error: (error: any) => {
          console.error('Error deleting transaction:', error);
          }
        });
    }
  }

  editTransaction(transaction: Transaction): void {
    // TODO: Open edit dialog
    console.log('Edit transaction:', transaction);
  }

  formatAmount(amount: number): string {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  }

  getAmountClass(transaction: Transaction): string {
    return transaction.amount >= 0 ? 'amount-positive' : 'amount-negative';
  }

  // Tracking functions for better performance
  trackByCategory(index: number, category: string): string {
    return category;
  }

  trackByAccount(index: number, account: string): string {
    return account;
  }

  // Comparison functions for mat-select
  compareCategories(c1: string, c2: string): boolean {
    return c1 === c2;
  }

  compareAccounts(a1: string, a2: string): boolean {
    return a1 === a2;
  }

  // Helper functions to check if options are selected
  isSelectedCategory(category: string): boolean {
    const selectedCategories = this.filterForm.get('categories')?.value || [];
    return selectedCategories.includes(category);
  }

  isSelectedAccount(account: string): boolean {
    const selectedAccounts = this.filterForm.get('accounts')?.value || [];
    return selectedAccounts.includes(account);
  }

  private renderTimelineChart(): void {
    console.log('📊 Rendering Chart.js timeline chart...');
    
    // Check if chart container exists
    const chartElement = document.getElementById('timelineChart') as HTMLCanvasElement;
    if (!chartElement) {
      console.error('❌ Timeline chart element not found in DOM');
      // Retry with exponential backoff
      setTimeout(() => this.renderTimelineChart(), 1000);
      return;
    }
    
    // Destroy previous chart if exists
    if (this.timelineChart) {
      console.log('🔄 Destroying previous chart instance');
      this.timelineChart.destroy();
      this.timelineChart = null;
    }
    
    // Get canvas context
    const ctx = chartElement.getContext('2d');
    if (!ctx) {
      console.error('❌ Could not get 2D context from canvas');
      return;
    }
    
    // Validate timeline data
    if (!this.timelineData) {
      console.log('⚠️ No timeline data available, creating empty chart');
      this.createEmptyChart(ctx);
      return;
    }
    
    // Validate data structure
    if (!this.timelineData.credits || !this.timelineData.debits) {
      console.error('❌ Invalid timeline data structure:', this.timelineData);
      this.createEmptyChart(ctx);
      return;
    }
    
    const credits = this.timelineData.credits || [];
    const debits = this.timelineData.debits || [];
    
    console.log(`📈 Processing chart data: ${credits.length} credits, ${debits.length} debits`);
    
    // If no data, show empty chart with message
    if (credits.length === 0 && debits.length === 0) {
      console.log('📊 No data points to display');
      this.createEmptyChart(ctx);
      return;
    }
    
    try {
      // Process data for Chart.js
      const { creditsData, debitsData } = this.processChartData(credits, debits);
      
      // Create chart configuration
      const chartConfig: ChartConfiguration = {
        type: 'scatter',
        data: {
          datasets: [
            {
              label: '💰 Income',
              data: creditsData,
              backgroundColor: 'rgba(76, 175, 80, 0.8)',
              borderColor: 'rgba(76, 175, 80, 1)',
              pointRadius: 5,
              pointHoverRadius: 8,
              pointBorderWidth: 2,
              pointBorderColor: 'white'
            },
            {
              label: '💳 Expenses',
              data: debitsData,
              backgroundColor: 'rgba(244, 67, 54, 0.8)',
              borderColor: 'rgba(244, 67, 54, 1)',
              pointRadius: 5,
              pointHoverRadius: 8,
              pointBorderWidth: 2,
              pointBorderColor: 'white'
            }
          ]
        },
        options: this.getChartOptions()
      };
      
      // Create the chart
      this.timelineChart = new Chart(ctx, chartConfig);
      
      console.log('✅ Chart.js timeline chart created successfully');
      
    } catch (error) {
      console.error('❌ Error creating Chart.js timeline chart:', error);
      this.renderFallbackChart(ctx);
    }
  }
  
  private processChartData(credits: any[], debits: any[]): { creditsData: any[], debitsData: any[] } {
    const creditsData = credits.map(point => {
      try {
        const dateValue = new Date(point.x);
        if (isNaN(dateValue.getTime())) {
          console.warn('⚠️ Invalid date in credits:', point.x);
          return null;
        }
        return {
          x: dateValue.getTime(),
          y: Math.abs(point.y),
          description: point.description || 'Credit transaction',
          category: point.category || 'Income',
          originalDate: point.x
        };
      } catch (error) {
        console.warn('⚠️ Error processing credit point:', point, error);
        return null;
      }
    }).filter(point => point !== null);
    
    const debitsData = debits.map(point => {
      try {
        const dateValue = new Date(point.x);
        if (isNaN(dateValue.getTime())) {
          console.warn('⚠️ Invalid date in debits:', point.x);
          return null;
        }
        return {
          x: dateValue.getTime(),
          y: Math.abs(point.y),
          description: point.description || 'Debit transaction',
          category: point.category || 'Expense',
          originalDate: point.x
        };
      } catch (error) {
        console.warn('⚠️ Error processing debit point:', point, error);
        return null;
      }
    }).filter(point => point !== null);
    
    console.log(`📊 Chart data processed: ${creditsData.length} credits, ${debitsData.length} debits`);
    return { creditsData, debitsData };
  }
  
  private getChartOptions(): ChartOptions {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'point'
      },
      scales: {
        x: {
          type: 'linear',
          title: {
            display: true,
            text: '📅 Date',
            font: {
              size: 14,
              weight: 'bold'
            }
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.1)'
          },
          ticks: {
            callback: (value: any) => {
              const date = new Date(value);
              return date.toLocaleDateString('en-IN', {
                month: 'short',
                day: 'numeric'
              });
            }
          }
        },
        y: {
          title: {
            display: true,
            text: '💰 Amount (₹)',
            font: {
              size: 14,
              weight: 'bold'
            }
          },
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.1)'
          },
          ticks: {
            callback: (value: any) => {
              return '₹' + Number(value).toLocaleString('en-IN');
            }
          }
        }
      },
      plugins: {
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          titleColor: 'white',
          bodyColor: 'white',
          borderColor: 'rgba(255, 255, 255, 0.2)',
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: true,
          callbacks: {
            title: (context: any) => {
              const point = context[0];
              return new Date(point.parsed.x).toLocaleDateString('en-IN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              });
            },
            label: (context: any) => {
              const point = context.raw as {x: number, y: number, description?: string, category?: string};
              const isIncome = context.dataset.label?.includes('Income');
              const prefix = isIncome ? '+' : '-';
              const amount = `₹${Math.abs(point.y).toLocaleString('en-IN')}`;
              
              let lines = [`${context.dataset.label}: ${prefix}${amount}`];
              if (point.description) {
                lines.push(`Description: ${point.description}`);
              }
              if (point.category) {
                lines.push(`Category: ${point.category}`);
              }
              return lines;
            }
          }
        },
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 15,
            font: {
              size: 13
            }
          }
        }
      }
    };
  }
  
  private createEmptyChart(ctx: CanvasRenderingContext2D): void {
    console.log('📊 Creating empty Chart.js chart');
    
    this.timelineChart = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [
          {
            label: '💰 Income',
            data: [],
            backgroundColor: 'rgba(76, 175, 80, 0.8)',
            borderColor: 'rgba(76, 175, 80, 1)',
            pointRadius: 5
          },
          {
            label: '💳 Expenses', 
            data: [],
            backgroundColor: 'rgba(244, 67, 54, 0.8)',
            borderColor: 'rgba(244, 67, 54, 1)',
            pointRadius: 5
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: '📊 No transaction data available for the selected filters',
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          legend: {
            display: true,
            position: 'top'
          }
        }
      }
    });
  }
  
  private renderFallbackChart(ctx: CanvasRenderingContext2D): void {
    console.log('📊 Rendering Chart.js fallback chart');
    
    try {
      // Create a simple bar chart as fallback
      this.timelineChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: ['💰 Income', '💳 Expenses'],
          datasets: [{
            label: '📊 Amount (₹)',
            data: [
              Math.abs(this.metrics?.total_income || 0),
              Math.abs(this.metrics?.total_expenses || 0)
            ],
            backgroundColor: [
              'rgba(76, 175, 80, 0.8)',
              'rgba(244, 67, 54, 0.8)'
            ],
            borderColor: [
              'rgba(76, 175, 80, 1)',
              'rgba(244, 67, 54, 1)'
            ],
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: '📊 Transaction Overview (Fallback)',
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: '💰 Amount (₹)'
              },
              ticks: {
                callback: (value: any) => {
                  return '₹' + Number(value).toLocaleString('en-IN');
                }
              }
            }
          }
        }
      });
      
      console.log('✅ Chart.js fallback chart created successfully');
    } catch (error) {
      console.error('❌ Error creating Chart.js fallback chart:', error);
    }
  }
  
  // ...existing code...
}
