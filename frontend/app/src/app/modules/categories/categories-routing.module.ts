import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// Import components
import { BlankCategoryComponent } from './components/blank-category/blank-category.component';

// Define routes - Categories tab reset to be completely empty
export const categoriesRoutes: Routes = [
  {
    path: '',
    component: BlankCategoryComponent
  },
  {
    path: '**',
    redirectTo: '',
    pathMatch: 'full'
  }
];

@NgModule({
  imports: [RouterModule.forChild(categoriesRoutes)],
  exports: [RouterModule]
})
export class CategoriesRoutingModule { }
