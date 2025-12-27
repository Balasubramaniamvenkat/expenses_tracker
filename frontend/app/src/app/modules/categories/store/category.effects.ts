import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, switchMap } from 'rxjs/operators';
import { of } from 'rxjs';
import { CategoryActions } from './category.actions';
import { CategoryService } from '../services/category.service';
import { CategoryAnalytics } from '../models/category.model';

@Injectable()
export class CategoryEffects {

  loadAnalytics$ = createEffect(() =>
    this.actions$.pipe(
      ofType(CategoryActions.loadAnalytics),
      switchMap(({ dateRange }) =>
        this.categoryService.getCategoryAnalytics(dateRange).pipe(
          map((analytics: CategoryAnalytics[]) => CategoryActions.loadAnalyticsSuccess({ analytics })),
          catchError(error => of(CategoryActions.loadAnalyticsFailure({ 
            error: error.message || 'Failed to load category analytics' 
          })))
        )
      )
    )
  );

  constructor(
    private actions$: Actions,
    private categoryService: CategoryService
  ) {}
}
