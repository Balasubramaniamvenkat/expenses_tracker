import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { CategoryService } from '../services/category.service';

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

    const dateRange = {
      startDate: new Date('2024-01-01'),
      endDate: new Date('2024-12-31')
    };

    service.getCategoryAnalytics(dateRange).subscribe(analytics => {
      expect(analytics).toEqual(mockApiResponse);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/categories/analytics?start_date=2024-01-01&end_date=2024-12-31');
    expect(req.request.method).toBe('GET');
    req.flush(mockApiResponse);
  });

  it('should surface API errors instead of returning stale fallback data', (done) => {
    const dateRange = {
      startDate: new Date('2024-01-01'),
      endDate: new Date('2024-12-31')
    };

    service.getCategoryAnalytics(dateRange).subscribe({
      next: () => fail('Expected the API error to be surfaced'),
      error: error => {
        expect(error.status).toBe(0);
        done();
      }
    });

    const req = httpMock.expectOne('http://localhost:8000/api/categories/analytics?start_date=2024-01-01&end_date=2024-12-31');
    req.error(new ErrorEvent('Network error'));
  });
});
