import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { CategoryService } from '../services/category.service';
import { CategoryAnalytics } from '../models/category.model';

describe('CategoryService API Integration', () => {
  let service: CategoryService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [CategoryService]
    });
    
    service = TestBed.inject(CategoryService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should call the correct API endpoint', () => {
    const mockApiResponse = [
      {
        category_id: 'income',
        category_name: 'INCOME',
        icon: '💰',
        color: '#4CAF50',
        monthly_amount: 85000,
        percentage_of_income: 100,
        budget_target: 85000,
        budget_variance: 0,
        trend: 'up',
        trend_value: 8,
        subcategories: [],
        insights: []
      }
    ];

    const expectedAnalytics: CategoryAnalytics[] = [
      {
        categoryId: 'income',
        categoryName: 'INCOME',
        icon: '💰',
        color: '#4CAF50',
        monthlyAmount: 85000,
        percentageOfIncome: 100,
        percentageOfCategory: 0,
        budgetTarget: 85000,
        budgetVariance: 0,
        trend: 'up',
        trendValue: 8,
        subcategories: [],
        insights: []
      }
    ];

    const dateRange = {
      startDate: new Date('2024-01-01'),
      endDate: new Date('2024-12-31')
    };

    service.getCategoryAnalytics(dateRange).subscribe(analytics => {
      expect(analytics).toEqual(expectedAnalytics);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/categories/analytics?start_date=2024-01-01&end_date=2024-12-31');
    expect(req.request.method).toBe('GET');
    req.flush(mockApiResponse);
  });

  it('should fallback to mock data when API fails', () => {
    const dateRange = {
      startDate: new Date('2024-01-01'),
      endDate: new Date('2024-12-31')
    };

    service.getCategoryAnalytics(dateRange).subscribe(analytics => {
      expect(analytics.length).toBeGreaterThan(0);
      expect(analytics[0].categoryId).toBeDefined();
    });

    const req = httpMock.expectOne('http://localhost:8000/api/categories/analytics?start_date=2024-01-01&end_date=2024-12-31');
    req.error(new ErrorEvent('Network error'));
  });
});
