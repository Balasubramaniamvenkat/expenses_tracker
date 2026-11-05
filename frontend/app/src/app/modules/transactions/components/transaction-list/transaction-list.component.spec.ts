import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { NEVER, of, throwError } from 'rxjs';
import { Transaction } from '../../../../models/transaction.model';
import {
  TransactionListResponse,
  TransactionMetrics,
  TransactionService
} from '../../services/transaction.service';
import { TransactionListComponent } from './transaction-list.component';

describe('TransactionListComponent', () => {
  let fixture: ComponentFixture<TransactionListComponent>;
  let component: TransactionListComponent;
  let service: jasmine.SpyObj<TransactionService>;

  const transaction: Transaction = {
    id: 'txn-1',
    date: '2025-01-10',
    description: 'Grocery store',
    amount: -1250,
    category: 'Food',
    account: 'Checking',
    type: 'expense'
  };

  const response: TransactionListResponse = {
    transactions: [transaction],
    pagination: {
      total_items: 1,
      total_pages: 1,
      current_page: 1,
      page_size: 50
    }
  };

  const metrics: TransactionMetrics = {
    total_transactions: 1,
    total_income: 0,
    total_expenses: 1250,
    total_planned: 0,
    net_savings: -1250,
    monthly_averages: {
      months: 1,
      transactions: 1,
      income: 0,
      expenses: 1250,
      planned: 0,
      savings: -1250
    },
    yearly_averages: {
      years: 1,
      transactions: 1,
      income: 0,
      expenses: 1250,
      planned: 0,
      savings: -1250
    }
  };

  beforeEach(async () => {
    service = jasmine.createSpyObj('TransactionService', [
      'getFilteredTransactions',
      'getTransactionMetrics',
      'getTransactionTimeline',
      'getFilterOptions',
      'exportTransactions',
      'deleteTransaction'
    ]);
    service.getFilteredTransactions.and.returnValue(of(response));
    service.getTransactionMetrics.and.returnValue(of(metrics));
    service.getTransactionTimeline.and.returnValue(NEVER);
    service.getFilterOptions.and.returnValue(of({
      categories: ['All Categories', 'Food'],
      accounts: ['All Accounts', 'Checking'],
      persons: []
    }));
    service.exportTransactions.and.returnValue(of(new Blob()));
    service.deleteTransaction.and.returnValue(of(void 0));

    await TestBed.configureTestingModule({
      imports: [TransactionListComponent],
      providers: [{ provide: TransactionService, useValue: service }]
    }).compileComponents();

    fixture = TestBed.createComponent(TransactionListComponent);
    component = fixture.componentInstance;
  });

  it('renders the transaction menu with its filters and history sections', () => {
    fixture.detectChanges();

    const pageText = (fixture.nativeElement as HTMLElement).textContent || '';
    expect(pageText).toContain('Accounts');
    expect(pageText).toContain('Smart Filters');
    expect(pageText).toContain('Transaction History');
    expect(pageText).toContain('Cash Flow Timeline');
  });

  it('loads transactions and summary metrics using the current filter form', () => {
    component.loadTransactions();

    expect(service.getFilteredTransactions).toHaveBeenCalled();
    expect(service.getTransactionMetrics).toHaveBeenCalled();
    expect(component.dataSource.data).toEqual([transaction]);
    expect(component.metrics).toEqual(metrics);
    expect(component.isLoading).toBeFalse();
  });

  it('passes search, category, account, and amount filters to the data request', () => {
    component.filterForm.patchValue({
      search_text: '  grocery  ',
      categories: ['Food'],
      accounts: ['Checking'],
      amount_min: 100,
      amount_max: 2000
    });

    component.applyFilters();

    expect(service.getFilteredTransactions).toHaveBeenCalledWith(jasmine.objectContaining({
      search_text: 'grocery',
      categories: ['Food'],
      accounts: ['Checking'],
      amount_min: 100,
      amount_max: 2000,
      page: 1
    }));
  });

  it('applies the selected account group to transactions, metrics, and timeline requests', () => {
    component.availableAccounts = [
      { value: component.allAccountsValue, label: 'All Accounts', accountNames: [] },
      {
        value: 'account-0',
        label: '•••• 3324',
        accountNames: ['Account_2025', 'Account_2026']
      },
      { value: 'account-1', label: '•••• 4065', accountNames: ['Account XX4065'] }
    ];

    component.onAccountSelectionChange(['account-0']);
    expect(service.getFilteredTransactions).toHaveBeenCalledWith(jasmine.objectContaining({
      accounts: ['Account_2025', 'Account_2026']
    }));
    expect(service.getTransactionMetrics).toHaveBeenCalledWith(jasmine.objectContaining({
      accounts: ['Account_2025', 'Account_2026']
    }));
    expect(service.getTransactionTimeline).toHaveBeenCalledWith(jasmine.objectContaining({
      accounts: ['Account_2025', 'Account_2026']
    }));

    service.getFilteredTransactions.calls.reset();
    component.onAccountSelectionChange(['account-0', 'account-1']);
    expect(service.getFilteredTransactions).toHaveBeenCalledWith(jasmine.objectContaining({
      accounts: ['Account_2025', 'Account_2026', 'Account XX4065']
    }));
  });

  it('applies dashboard date presets to all transaction data requests', () => {
    const today = new Date();
    const start = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
    const expectedStart = [
      start.getFullYear(),
      String(start.getMonth() + 1).padStart(2, '0'),
      String(start.getDate()).padStart(2, '0')
    ].join('-');
    const expectedEnd = [
      today.getFullYear(),
      String(today.getMonth() + 1).padStart(2, '0'),
      String(today.getDate()).padStart(2, '0')
    ].join('-');

    component.onDateRangeChange('1y');

    const expectedDates = { date_from: expectedStart, date_to: expectedEnd };
    expect(service.getFilteredTransactions).toHaveBeenCalledWith(jasmine.objectContaining(expectedDates));
    expect(service.getTransactionMetrics).toHaveBeenCalledWith(jasmine.objectContaining(expectedDates));
    expect(service.getTransactionTimeline).toHaveBeenCalledWith(jasmine.objectContaining(expectedDates));
  });

  it('applies a custom date range only after both dates are selected', () => {
    component.onDateRangeChange('custom');
    component.customStartDate = new Date(2025, 0, 10);
    component.applyCustomDateRange();
    expect(service.getFilteredTransactions).not.toHaveBeenCalled();

    component.customEndDate = new Date(2025, 1, 20);
    component.applyCustomDateRange();

    const expectedDates = { date_from: '2025-01-10', date_to: '2025-02-20' };
    expect(service.getFilteredTransactions).toHaveBeenCalledWith(jasmine.objectContaining(expectedDates));
    expect(service.getTransactionMetrics).toHaveBeenCalledWith(jasmine.objectContaining(expectedDates));
    expect(service.getTransactionTimeline).toHaveBeenCalledWith(jasmine.objectContaining(expectedDates));
  });

  it('converts date-form values into API date strings', () => {
    component.filterForm.patchValue({
      date_from: new Date('2025-01-10T00:00:00.000Z'),
      date_to: new Date('2025-02-20T00:00:00.000Z')
    });

    component.loadTransactions();

    expect(service.getFilteredTransactions).toHaveBeenCalledWith(jasmine.objectContaining({
      date_from: '2025-01-10',
      date_to: '2025-02-20'
    }));
  });

  it('resets the page number when filters are applied', () => {
    component.filterForm.patchValue({ page: 4 });

    component.applyFilters();

    expect(component.filterForm.value.page).toBe(1);
    expect(service.getFilteredTransactions).toHaveBeenCalledWith(jasmine.objectContaining({ page: 1 }));
  });

  it('clears all filter inputs and returns to the first page', () => {
    component.filterForm.patchValue({
      search_text: 'grocery',
      date_from: new Date('2025-01-10T00:00:00.000Z'),
      categories: ['Food'],
      accounts: ['Checking'],
      amount_min: 500,
      page: 3
    });

    component.clearFilters();

    expect(component.filterForm.value).toEqual({
      search_text: '',
      date_from: null,
      date_to: null,
      categories: ['All Categories'],
      accounts: ['All Accounts'],
      amount_min: null,
      amount_max: null,
      page: 1,
      page_size: 50
    });
    expect(component.selectedDateRange).toBe('all');
    expect(component.selectedAccountValues).toEqual([component.allAccountsValue]);
    expect(service.getFilteredTransactions).toHaveBeenCalledWith(jasmine.objectContaining({
      search_text: undefined,
      date_from: undefined,
      categories: ['All Categories'],
      accounts: ['All Accounts'],
      page: 1
    }));
  });

  it('shows an empty transaction list and clears loading state when the request fails', () => {
    spyOn(console, 'error');
    service.getFilteredTransactions.and.returnValue(throwError(() => new Error('network failure')));

    component.loadTransactions();

    expect(component.dataSource.data).toEqual([]);
    expect(component.isLoading).toBeFalse();
  });

  it('formats currency and gives expenses and income distinct amount classes', () => {
    expect(component.formatAmount(1250)).toContain('1,250.00');
    expect(component.getAmountClass(transaction)).toBe('amount-negative');
    expect(component.getAmountClass({ ...transaction, amount: 1250, type: 'income' })).toBe('amount-positive');
  });

  it('does not delete a transaction when the confirmation is declined', () => {
    spyOn(window, 'confirm').and.returnValue(false);

    component.deleteTransaction(transaction);

    expect(service.deleteTransaction).not.toHaveBeenCalled();
  });

  it('cancels pending chart renders when leaving the transaction page', fakeAsync(() => {
    service.getTransactionTimeline.and.returnValue(of({ credits: [], debits: [] }));
    const chartError = spyOn(console, 'error');

    fixture.detectChanges();
    fixture.destroy();
    tick(600);

    expect(chartError).not.toHaveBeenCalledWith('❌ Timeline chart element not found in DOM');
  }));
});
