import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AIChatComponent } from './components/ai-chat/ai-chat.component';

const routes: Routes = [
  {
    path: '',
    component: AIChatComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AIInsightsRoutingModule { }
