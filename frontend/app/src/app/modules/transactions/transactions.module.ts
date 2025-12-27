import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// Routing
import { TransactionsRoutingModule } from './transactions-routing.module';

// Services
import { TransactionService } from './services/transaction.service';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    TransactionsRoutingModule
  ],
  providers: [
    TransactionService
  ]
})
export class TransactionsModule { }
