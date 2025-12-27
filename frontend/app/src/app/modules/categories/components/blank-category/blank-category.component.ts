import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MonthlyBarChartComponent } from '../monthly-bar-chart/monthly-bar-chart.component';

@Component({
  selector: 'app-blank-category',
  standalone: true,
  imports: [
    CommonModule,
    MonthlyBarChartComponent
  ],
  template: `
    <app-monthly-bar-chart></app-monthly-bar-chart>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }
  `]
})
export class BlankCategoryComponent {}
