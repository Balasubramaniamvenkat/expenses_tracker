import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/upload',
    pathMatch: 'full'
  },
  {
    path: 'upload',
    loadComponent: () => import('./pages/upload/upload-page.component').then(m => m.UploadPageComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'transactions',
    loadComponent: () => import('./modules/transactions/components/transaction-list/transaction-list.component').then(m => m.TransactionListComponent)
  },
  {
    path: 'ai-insights',
    loadChildren: () => import('./modules/ai-insights/ai-insights.module').then(m => m.AIInsightsModule)
  },
  {
    path: 'categories',
    redirectTo: '/ai-insights',
    pathMatch: 'full'
  },
  {
    path: '**',
    redirectTo: '/upload'
  }
];
