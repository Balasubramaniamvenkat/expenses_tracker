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
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Transaction, TransactionFilter, TransactionSummary } from '../../../../models/transaction.model';
import { TransactionService, FilterOptions, TransactionMetrics, TimelineData } from '../../services/transaction.service';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { Subscription } from 'rxjs';
import Chart from 'chart.js/auto';

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
  
  private filterSubscription: Subscription | null = null;

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
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
    
    // Listen for pagination events
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
  }

  ngOnDestroy(): void {
    if (this.filterSubscription) {
      this.filterSubscription.unsubscribe();
    }
    
    if (this.timelineChart) {
      this.timelineChart.destroy();
    }
  }

  private setupFilterSubscription(): void {
    this.filterSubscription = this.filterForm.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged()
      )
      .subscribe(() => {
        // Reset to first page when filters change
        if (this.paginator) {
          this.paginator.pageIndex = 0;
          this.filterForm.patchValue({ page: 1 }, { emitEvent: false });
        }
        this.loadTransactions();
      });
  }

  loadTransactions(): void {
    this.isLoading = true;
    const filters: TransactionFilter = this.getFilters();
    
    // Get transactions
    this.transactionService.getFilteredTransactions(filters).subscribe({
      next: (response) => {
        this.dataSource.data = response.transactions;
        
        // Update paginator with server-side pagination info
        if (this.paginator) {
          this.paginator.length = response.pagination.total_items;
          this.paginator.pageSize = response.pagination.page_size;
          this.paginator.pageIndex = response.pagination.current_page - 1;
        }
        
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading transactions:', error);
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
        this.timelineData = data;
        setTimeout(() => this.renderTimelineChart(), 100);
      },
      error: (error) => {
        console.error('Error loading timeline data:', error);
      }
    });
  }

  private loadFilterOptions(): void {
    this.transactionService.getFilterOptions().subscribe({
      next: (options) => {
        this.availableCategories = options.categories;
        this.availableAccounts = options.accounts;
      },
      error: (error) => {
        console.error('Error loading filter options:', error);
      }
    });
  }

  private getFilters(): TransactionFilter {
    const formValue = this.filterForm.value;
    return {
      search_text: formValue.search_text || '',
      date_from: formValue.date_from ? this.formatDate(formValue.date_from) : '',
      date_to: formValue.date_to ? this.formatDate(formValue.date_to) : '',
      categories: formValue.categories || ['All Categories'],
      accounts: formValue.accounts || ['All Accounts'],
      amount_min: formValue.amount_min || undefined
    };
  }

  private formatDate(date: any): string {
    if (!date) return '';
    const d = new Date(date);
    return d.toISOString().split('T')[0];
  }

  applyFilters(): void {
    this.loadTransactions();
  }

  clearFilters(): void {
    this.filterForm.reset({
      search_text: '',
      date_from: '',
      date_to: '',
      categories: ['All Categories'],
      accounts: ['All Accounts'],
      amount_min: '',
      page: 1,
      page_size: 50
    });
    
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
        error: (error) => {
          console.error('Error deleting transaction:', error);
        }
      });
    }
  }

  editTransaction(transaction: Transaction): void {
    // TODO: Open edit dialog
    console.log('Edit transaction:', transaction);
  }

  getAmountClass(transaction: Transaction): string {
    return transaction.type === 'income' ? 'amount-positive' : 'amount-negative';
  }

  formatAmount(amount: number): string {
    return '₹' + Math.abs(amount).toLocaleString('en-IN');
  }

  private renderTimelineChart(): void {
    if (!this.timelineData || !document.getElementById('timelineChart')) {
      return;
    }
    
    // Destroy previous chart if exists
    if (this.timelineChart) {
      this.timelineChart.destroy();
    }
    
    const ctx = (document.getElementById('timelineChart') as HTMLCanvasElement)?.getContext('2d');
    if (!ctx) return;
    
    // Prepare data for scatter plot
    const incomeData = [];
    const expenseData = [];
    
    for (let i = 0; i < this.timelineData.dates.length; i++) {
      const point = {
        x: new Date(this.timelineData.dates[i]),
        y: this.timelineData.amounts[i]
      };
      
      if (this.timelineData.types[i] === 'income') {
        incomeData.push(point);
      } else {
        expenseData.push(point);
      }
    }
    
    this.timelineChart = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [
          {
            label: 'Income',
            data: incomeData,
            backgroundColor: 'rgba(0, 0, 255, 0.7)',
            borderColor: 'rgba(0, 0, 255, 1)',
            pointRadius: 5,
            pointHoverRadius: 7
          },
          {
            label: 'Expenses',
            data: expenseData,
            backgroundColor: 'rgba(255, 165, 0, 0.7)',
            borderColor: 'rgba(255, 165, 0, 1)',
            pointRadius: 5,
            pointHoverRadius: 7
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day',
              displayFormats: {
                day: 'MMM dd'
              }
            },
            title: {
              display: true,
              text: 'Date'
            }
          },
          y: {
            title: {
              display: true,
              text: 'Amount (₹)'
            },
            beginAtZero: true
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                const point = context.raw as {x: Date, y: number};
                return `${context.dataset.label}: ₹${point.y.toLocaleString('en-IN')}`;
              },
              title: function(context) {
                const point = context[0].raw as {x: Date, y: number};
                return new Date(point.x).toLocaleDateString('en-IN', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric'
                });
              }
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
}
