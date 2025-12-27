import { createActionGroup, props, emptyProps } from '@ngrx/store';
import { CategoryAnalytics, DateRange } from '../models/category.model';

export const CategoryActions = createActionGroup({
  source: 'Category',
  events: {
    'Load Analytics': props<{ dateRange: DateRange }>(),
    'Load Analytics Success': props<{ analytics: CategoryAnalytics[] }>(),
    'Load Analytics Failure': props<{ error: string }>(),
    'Select Categories': props<{ categoryIds: string[] }>(),
    'Update Date Range': props<{ dateRange: DateRange }>(),
    'Toggle Display Mode': props<{ mode: 'amount' | 'percentage' }>(),
    'Change Chart Type': props<{ chartType: string }>(),
    'Toggle Comparison': props<{ showComparison: boolean }>(),
    'Set Budget Target': props<{ categoryId: string; target: number }>(),
    'Clear Error': emptyProps()
  }
});
