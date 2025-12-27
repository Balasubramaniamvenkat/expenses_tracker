import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  // Home route redirects to transactions by default
  { path: '', redirectTo: 'transactions', pathMatch: 'full' },
  
  // Transactions module with lazy loading
  {
    path: 'transactions',
    loadChildren: () => import('./modules/transactions/transactions.module').then(m => m.TransactionsModule)
  },
  
  // Upload module with lazy loading
  {
    path: 'upload',
    loadChildren: () => import('./modules/upload/upload.module').then(m => m.UploadModule)
  },
  
  // Categories module with lazy loading - Redirects to AI Insights
  {
    path: 'categories',
    redirectTo: 'ai-insights',
    pathMatch: 'full'
  },
  
  // AI Insights module - Chat with your financial data
  {
    path: 'ai-insights',
    loadChildren: () => import('./modules/ai-insights/ai-insights.module').then(m => m.AIInsightsModule)
  },
  
  // Insights module with lazy loading
  {
    path: 'insights',
    loadChildren: () => import('./modules/insights/insights.module').then(m => m.InsightsModule)
  },
  
  // Fallback for any unmatched routes
  { path: '**', redirectTo: 'transactions' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
