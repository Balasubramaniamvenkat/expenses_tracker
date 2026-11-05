import { Component, OnInit, ViewChild, AfterViewInit, OnDestroy, ElementRef } from '@angular/core';
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
import {
  ALL_ACCOUNTS_LABEL,
  ALL_ACCOUNTS_VALUE,
  AccountFilterOption,
  createAccountFilterOptions
} from '../../../../shared/account-filter-options';

// Helper function to compare filter values for distinctUntilChanged
function compareFilters(prev: any, curr: any): boolean {
  return JSON.stringify(prev) === JSON.stringify(curr);
}

type TransactionDateRange = '1m' | '3m' | '6m' | '1y' | 'all' | 'custom';
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
  @ViewChild('timelineChart') timelineChartCanvas?: ElementRef<HTMLCanvasElement>;

  displayedColumns: string[] = [
    'date', 
    'description', 
    'category', 
    'amount', 
    'account'
  ];

  dataSource = new MatTableDataSource<Transaction>([]);
  filterForm: FormGroup;
  metrics: TransactionMetrics | null = null;
  timelineData: TimelineData | null = null;
  timelineChart: Chart | null = null;
  isLoading = false;
  
  // Filter options
  availableCategories: string[] = ['All Categories'];
  readonly allAccountsLabel = ALL_ACCOUNTS_LABEL;
  readonly allAccountsValue = ALL_ACCOUNTS_VALUE;
  availableAccounts: AccountFilterOption[] = [
    { value: this.allAccountsValue, label: this.allAccountsLabel, accountNames: [] }
  ];
  selectedAccountValues: string[] = [this.allAccountsValue];
  accountOptionsLoading = true;
  accountOptionsError: string | null = null;
  readonly dateRangeOptions: { value: TransactionDateRange; label: string }[] = [
    { value: '1m', label: 'Last Month' },
    { value: '3m', label: 'Last 3 Months' },
    { value: '6m', label: 'Last 6 Months' },
    { value: '1y', label: 'Last Year' },
    { value: 'all', label: 'All Time' },
    { value: 'custom', label: 'Custom Range' }
  ];
  selectedDateRange: TransactionDateRange = 'all';
  customStartDate: Date | null = null;
  customEndDate: Date | null = null;
  
  // Explicitly stored date strings for filtering
  private dateFromString: string | undefined = undefined;
  private dateToString: string | undefined = undefined;
  
  private filterSubscription: Subscription | null = null;
  private unsubscribe$ = new Subject<void>();
  private chartRenderTimer: number | null = null;
  private readonly resizeHandler = (): void => {
    this.timelineChart?.resize();
  };

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
      this.scheduleTimelineChartRender(500);
    }

    // Set up a resize listener for the chart
    window.addEventListener('resize', this.resizeHandler);

  }

  ngOnDestroy(): void {
    // Clean up any subscriptions
    this.unsubscribe$.next();
    this.unsubscribe$.complete();
    if (this.chartRenderTimer !== null) {
      window.clearTimeout(this.chartRenderTimer);
      this.chartRenderTimer = null;
    }
    
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
    window.removeEventListener('resize', this.resizeHandler);
    
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
    
    // Get transactions
    this.transactionService.getFilteredTransactions(filters).subscribe({
      next: (response) => {
        // Ensure we have transactions array even if empty
        if (!response.transactions) {
          response.transactions = [];
        }
        
        this.dataSource.data = response.transactions;
        
        // Update paginator with server-side pagination info
        if (this.paginator && response.pagination) {
          this.paginator.length = response.pagination.total_items;
          this.paginator.pageSize = response.pagination.page_size;
          this.paginator.pageIndex = response.pagination.current_page - 1;
        }
        
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading transactions:', error.message);
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
        console.error('Error loading metrics:', error.message);
      }
    });
    
    // Get timeline data
    this.transactionService.getTransactionTimeline(filters).subscribe({
      next: (data) => {
        this.timelineData = data;
        this.scheduleTimelineChartRender(100);
      },
      error: (error) => {
        console.error('Error loading timeline data:', error.message);
        // Set empty data and still try to render an empty chart
        this.timelineData = { credits: [], debits: [] };
        this.scheduleTimelineChartRender(100);
      }
    });
  }

  private loadFilterOptions(): void {
    this.accountOptionsLoading = true;
    this.accountOptionsError = null;
    this.transactionService.getFilterOptions().subscribe({
      next: (options) => {
        this.availableCategories = options.categories;
        this.availableAccounts = [
          { value: this.allAccountsValue, label: this.allAccountsLabel, accountNames: [] },
          ...createAccountFilterOptions(options.accounts)
        ];
        this.accountOptionsLoading = false;
      },
      error: (error) => {
        console.error('Error loading filter options:', error.message);
        this.accountOptionsError = 'Account options could not be loaded. Showing all accounts.';
        this.accountOptionsLoading = false;
      }
    });
  }

  onDateRangeChange(range: TransactionDateRange = this.selectedDateRange): void {
    this.selectedDateRange = range;
    if (range === 'custom') return;

    const endDate = new Date();
    let startDate: Date | undefined;
    switch (range) {
      case '1m':
        startDate = new Date(endDate.getFullYear(), endDate.getMonth() - 1, endDate.getDate());
        break;
      case '3m':
        startDate = new Date(endDate.getFullYear(), endDate.getMonth() - 3, endDate.getDate());
        break;
      case '6m':
        startDate = new Date(endDate.getFullYear(), endDate.getMonth() - 6, endDate.getDate());
        break;
      case '1y':
        startDate = new Date(endDate.getFullYear() - 1, endDate.getMonth(), endDate.getDate());
        break;
      case 'all':
        break;
    }

    this.setDateFilters(startDate, range === 'all' ? undefined : endDate);
    this.loadTransactions();
  }

  onCustomStartDateChange(event: MatDatepickerInputEvent<Date>): void {
    this.customStartDate = event.value ?? null;
  }

  onCustomEndDateChange(event: MatDatepickerInputEvent<Date>): void {
    this.customEndDate = event.value ?? null;
  }

  applyCustomDateRange(): void {
    if (!this.customStartDate || !this.customEndDate) return;
    this.setDateFilters(this.customStartDate, this.customEndDate);
    this.loadTransactions();
  }

  private setDateFilters(startDate?: Date, endDate?: Date): void {
    this.dateFromString = startDate ? this.formatDateValue(startDate) : undefined;
    this.dateToString = endDate ? this.formatDateValue(endDate) : undefined;
    this.filterForm.patchValue({
      date_from: startDate ?? null,
      date_to: endDate ?? null,
      page: 1
    }, { emitEvent: false });

    if (this.paginator) {
      this.paginator.pageIndex = 0;
    }
  }

  onAccountSelectionChange(selection: string[]): void {
    const hadAllAccounts = this.selectedAccountValues.includes(this.allAccountsValue);
    const selectedAllAccounts = selection.includes(this.allAccountsValue);

    if (selectedAllAccounts && hadAllAccounts && selection.length > 1) {
      this.selectedAccountValues = selection.filter(value => value !== this.allAccountsValue);
    } else if (selectedAllAccounts || selection.length === 0) {
      this.selectedAccountValues = [this.allAccountsValue];
    } else {
      this.selectedAccountValues = selection;
    }

    const accountNames = this.availableAccounts
      .filter(option => this.selectedAccountValues.includes(option.value))
      .flatMap(option => option.accountNames);
    this.filterForm.patchValue({
      accounts: accountNames.length ? [...new Set(accountNames)] : [this.allAccountsLabel],
      page: 1
    }, { emitEvent: false });

    if (this.paginator) {
      this.paginator.pageIndex = 0;
    }
    this.loadTransactions();
  }

  getSelectedAccountsLabel(): string {
    if (!this.selectedAccountValues.length || this.selectedAccountValues.includes(this.allAccountsValue)) {
      return this.allAccountsLabel;
    }
    if (this.selectedAccountValues.length > 1) {
      return `${this.selectedAccountValues.length} accounts`;
    }
    return this.availableAccounts.find(option => option.value === this.selectedAccountValues[0])?.label
      ?? 'Account';
  }

  getSelectedDateRangeLabel(): string {
    return this.dateRangeOptions.find(option => option.value === this.selectedDateRange)?.label ?? 'All Time';
  }

  getDateRangeIcon(value: string): string {
    const icons: Record<string, string> = {
      '1m': 'today',
      '3m': 'date_range',
      '6m': 'event_note',
      '1y': 'calendar_month',
      'all': 'all_inclusive',
      'custom': 'edit_calendar'
    };
    return icons[value] ?? 'calendar_today';
  }

  // Date change event handlers - capture dates directly when selected
  onDateFromChange(event: MatDatepickerInputEvent<Date>): void {
    if (event.value) {
      const d = event.value;
      this.dateFromString = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    } else {
      this.dateFromString = undefined;
    }
  }

  onDateToChange(event: MatDatepickerInputEvent<Date>): void {
    if (event.value) {
      const d = event.value;
      this.dateToString = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    } else {
      this.dateToString = undefined;
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
      console.warn('Invalid date value in transaction filter.');
      return undefined;
    }
    
    // Format as YYYY-MM-DD using local timezone
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  applyFilters(): void {
    // Reset to first page when applying filters
    if (this.paginator) {
      this.paginator.pageIndex = 0;
    }
    this.filterForm.patchValue({ page: 1 }, { emitEvent: false });
    this.loadTransactions();
  }

  clearFilters(): void {
    // Reset the stored date strings
    this.dateFromString = undefined;
    this.dateToString = undefined;
    this.selectedDateRange = 'all';
    this.customStartDate = null;
    this.customEndDate = null;
    this.selectedAccountValues = [this.allAccountsValue];
    
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
        console.error('Error exporting transactions:', error.message);
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
          console.error('Error deleting transaction:', error.message);
          }
        });
    }
  }

  editTransaction(transaction: Transaction): void {
    // TODO: Open edit dialog
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

  trackByAccount(index: number, account: AccountFilterOption): string {
    return account.value;
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

  private scheduleTimelineChartRender(delay: number): void {
    if (this.chartRenderTimer !== null) {
      window.clearTimeout(this.chartRenderTimer);
    }

    this.chartRenderTimer = window.setTimeout(() => {
      this.chartRenderTimer = null;
      this.renderTimelineChart();
    }, delay);
  }

  private renderTimelineChart(): void {
    const chartElement = this.timelineChartCanvas?.nativeElement;
    if (!chartElement?.isConnected) return;
    
    // Destroy previous chart if exists
    if (this.timelineChart) {
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
      this.createEmptyChart(ctx);
      return;
    }
    
    // Validate data structure
    if (!this.timelineData.credits || !this.timelineData.debits) {
      console.error('Invalid transaction timeline data structure.');
      this.createEmptyChart(ctx);
      return;
    }
    
    const credits = this.timelineData.credits || [];
    const debits = this.timelineData.debits || [];
    
    // If no data, show empty chart with message
    if (credits.length === 0 && debits.length === 0) {
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
    } catch (error) {
      console.error(
        'Error creating transaction timeline chart:',
        error instanceof Error ? error.message : String(error)
      );
      this.renderFallbackChart(ctx);
    }
  }
  
  private processChartData(credits: any[], debits: any[]): { creditsData: any[], debitsData: any[] } {
    const creditsData = credits.map(point => {
      try {
        const dateValue = new Date(point.x);
        if (isNaN(dateValue.getTime())) {
          console.warn('Invalid date in transaction credit timeline point.');
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
        console.warn(
          'Error processing transaction credit timeline point:',
          error instanceof Error ? error.message : String(error)
        );
        return null;
      }
    }).filter(point => point !== null);
    
    const debitsData = debits.map(point => {
      try {
        const dateValue = new Date(point.x);
        if (isNaN(dateValue.getTime())) {
          console.warn('Invalid date in transaction debit timeline point.');
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
        console.warn(
          'Error processing transaction debit timeline point:',
          error instanceof Error ? error.message : String(error)
        );
        return null;
      }
    }).filter(point => point !== null);
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
    } catch (error) {
      console.error(
        'Error creating transaction fallback chart:',
        error instanceof Error ? error.message : String(error)
      );
    }
  }
  
  // ...existing code...
}
