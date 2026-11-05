import { HttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NEVER, of } from 'rxjs';
import { DashboardEnhancedComponent } from './dashboard-enhanced.component';

describe('DashboardEnhancedComponent', () => {
  let fixture: ComponentFixture<DashboardEnhancedComponent>;
  let component: DashboardEnhancedComponent;
  let http: jasmine.SpyObj<HttpClient>;

  beforeEach(async () => {
    http = jasmine.createSpyObj('HttpClient', ['get']);
    http.get.and.returnValue(NEVER);

    await TestBed.configureTestingModule({
      imports: [DashboardEnhancedComponent],
      providers: [
        provideRouter([]),
        { provide: HttpClient, useValue: http }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardEnhancedComponent);
    component = fixture.componentInstance;
  });

  it('starts on the all-time range and provides labels and icons for the range selector', () => {
    expect(component.selectedDateRange).toBe('all');
    expect(component.getSelectedDateRangeLabel()).toBe('All Time');
    expect(component.getDateRangeIcon('3m')).toBe('date_range');
    expect(component.getDateRangeIcon('custom')).toBe('edit_calendar');
    expect(component.getDateRangeIcon('unknown')).toBe('calendar_today');
  });

  it('formats dashboard values using Indian currency grouping', () => {
    expect(component.formatCurrency(1234567)).toBe('₹12,34,567');
    expect(component.formatCurrency(0)).toBe('₹0');
  });

  it('updates breakdown plot values for monthly average, yearly average, and cumulative sum', () => {
    const item = { amount: 3600, averageMonthlyAmount: 100 };

    component.plotMetric = 'monthly-average';
    expect(component.getPlotValue(item)).toBe(100);

    component.setPlotMetric('yearly-average');
    expect(component.getPlotValue(item)).toBe(1200);

    component.setPlotMetric('sum');
    expect(component.getPlotValue(item)).toBe(3600);
    expect(component.activePlotMetricLabel).toBe('Cumulative sum');
  });

  it('loads summary, trends, and category data with the selected all-time range', () => {
    component.error = 'previous error';
    component.loadAllData();

    const urls = http.get.calls.allArgs().map(args => String(args[0]));
    expect(urls).toContain('http://localhost:8000/api/dashboard/summary');
    expect(urls).toContain('http://localhost:8000/api/categories/trend-comparison');
    expect(urls).toContain('http://localhost:8000/api/categories/hierarchy?transaction_type=expense');
    expect(component.isLoading).toBeTrue();
    expect(component.error).toBeNull();
  });

  it('includes the chosen dates in custom-range dashboard and hierarchy requests', () => {
    component.selectedDateRange = 'custom';
    component.customStartDate = new Date('2025-01-10T00:00:00.000Z');
    component.customEndDate = new Date('2025-02-20T00:00:00.000Z');
    component.loadAllData();

    const urls = http.get.calls.allArgs().map(args => String(args[0]));
    expect(urls).toContain('http://localhost:8000/api/dashboard/summary?start_date=2025-01-10&end_date=2025-02-20');
    expect(urls).toContain('http://localhost:8000/api/categories/hierarchy?start_date=2025-01-10&end_date=2025-02-20&transaction_type=expense');
  });

  it('includes selected accounts in summary, trend, and hierarchy requests', () => {
    component.availableAccounts = [
      { value: component.allAccountsValue, label: 'All Accounts', accountNames: [] },
      { value: 'primary', label: '•••• 1234', accountNames: ['Primary'] },
      { value: 'savings', label: '•••• 5678', accountNames: ['Savings'] }
    ];
    component.selectedAccounts = ['primary', 'savings'];
    component.loadAllData();

    const urls = http.get.calls.allArgs().map(args => String(args[0]));
    expect(urls).toContain('http://localhost:8000/api/dashboard/summary?account=Primary%2CSavings');
    expect(urls).toContain('http://localhost:8000/api/categories/trend-comparison?account=Primary%2CSavings');
    expect(urls).toContain('http://localhost:8000/api/categories/hierarchy?transaction_type=expense&account=Primary%2CSavings');
  });

  it('excludes the all-accounts placeholder and groups year-suffixed account names', () => {
    http.get.and.returnValue(of({
      accounts: [
        'All Accounts',
        '916010056973324_2025',
        '916010056973324_2026',
        'Account XX4065',
        'Raji_2025_mod',
        'Raji_2026_mod'
      ]
    }));
    spyOn(component, 'loadAllData');

    component.ngOnInit();

    expect(component.availableAccounts.map(account => account.label)).toEqual([
      'All Accounts',
      '•••• 3324',
      '•••• 4065',
      'Account 1'
    ]);
    expect(component.availableAccounts.length).toBe(4);
    expect(component.availableAccounts[3].accountNames).toEqual([
      'Raji_2025_mod',
      'Raji_2026_mod'
    ]);
  });

  it('switches from all accounts to specific accounts and restores all when none remain selected', () => {
    const reload = spyOn(component, 'loadAllData');

    component.onAccountSelectionChange([component.allAccountsValue, 'primary']);
    expect(component.selectedAccounts).toEqual(['primary']);

    component.onAccountSelectionChange([]);
    expect(component.selectedAccounts).toEqual([component.allAccountsValue]);
    expect(reload).toHaveBeenCalledTimes(2);
  });

  it('reloads automatically for preset ranges but waits for explicit custom-range application', () => {
    const reload = spyOn(component, 'loadAllData');

    component.selectedDateRange = 'custom';
    component.onDateRangeChange();
    expect(reload).not.toHaveBeenCalled();

    component.selectedDateRange = '6m';
    component.onDateRangeChange();
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('applies a custom range only after both dates are selected', () => {
    const reload = spyOn(component, 'loadAllData');
    component.selectedDateRange = 'custom';
    component.customStartDate = new Date('2025-01-10T00:00:00.000Z');

    component.applyCustomDateRange();
    expect(reload).not.toHaveBeenCalled();

    component.customEndDate = new Date('2025-02-20T00:00:00.000Z');
    component.applyCustomDateRange();
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('selects the matching breakdown data, label, and empty-state message', () => {
    component.breakdownType = 'income';
    expect(component.activeBreakdownLabel).toBe('Income');
    expect(component.activeNoDataMessage).toBe('No income categories for this period');

    component.breakdownType = 'investment';
    expect(component.activeBreakdownLabel).toBe('Investment');
    expect(component.activeNoDataMessage).toBe('No investment categories for this period');
    expect(component.activeUnavailableMessage).toBe('Investment breakdown is unavailable.');

    component.breakdownType = 'planned';
    expect(component.activeBreakdownLabel).toBe('Planned');
    expect(component.activeTopCategoriesLabel).toBe('Planned Categories');

    component.breakdownType = 'expense';
    expect(component.activeBreakdownLabel).toBe('Expense');

    component.breakdownType = 'transfer';
    expect(component.activeBreakdownLabel).toBe('Transfer');
    expect(component.activeNoDataMessage).toBe('No transfer categories for this period');
  });

  it('loads planned and transfer hierarchies when their groups are selected', () => {
    component.setBreakdownType('planned');
    expect(component.isActiveHierarchyLoading).toBeTrue();
    expect(component.activeLoadingMessage).toBe('Loading planned breakdown...');

    component.setBreakdownType('transfer');
    expect(component.isActiveHierarchyLoading).toBeTrue();
    expect(component.activeLoadingMessage).toBe('Loading transfer breakdown...');

    const urls = http.get.calls.allArgs().map(args => String(args[0]));
    expect(urls).toContain('http://localhost:8000/api/categories/hierarchy?transaction_type=planned');
    expect(urls).toContain('http://localhost:8000/api/categories/hierarchy?transaction_type=transfer');
  });
});
