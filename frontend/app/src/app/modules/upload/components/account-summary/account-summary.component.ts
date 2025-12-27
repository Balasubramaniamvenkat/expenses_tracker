import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatButtonModule } from '@angular/material/button';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { RouterLink } from '@angular/router';

import { UploadService } from '../../services/upload.service';
import { AccountSummary } from '../../../../models/upload.model';

@Component({
  selector: 'app-account-summary',
  templateUrl: './account-summary.component.html',
  styleUrls: ['./account-summary.component.scss'],
  standalone: true,  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatDividerModule,
    MatButtonModule,
    MatExpansionModule,
    MatChipsModule,
    RouterLink
  ]
})
export class AccountSummaryComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  accounts$: Observable<AccountSummary[]>;
  totalAccounts = 0;
  totalTransactions = 0;
  totalIncome = 0;
  totalExpenses = 0;
  overallBalance = 0;

  constructor(private uploadService: UploadService) {
    this.accounts$ = this.uploadService.accounts$;
  }

  ngOnInit(): void {
    // Subscribe to accounts to calculate summary statistics
    this.accounts$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(accounts => {
      this.calculateSummaryStats(accounts);
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Calculate summary statistics from all accounts
   */
  private calculateSummaryStats(accounts: AccountSummary[]): void {
    this.totalAccounts = accounts.length;
    this.totalTransactions = accounts.reduce((sum, account) => sum + account.total_transactions, 0);
    this.totalIncome = accounts.reduce((sum, account) => sum + account.total_income, 0);
    this.totalExpenses = accounts.reduce((sum, account) => sum + account.total_expenses, 0);
    this.overallBalance = this.totalIncome - this.totalExpenses;
  }

  /**
   * Format currency for display
   */  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  }

  /**
   * Format large numbers with commas
   */  formatNumber(num: number): string {
    return new Intl.NumberFormat('en-US').format(num);
  }

  /**
   * Get account display name
   */
  getAccountDisplayName(account: AccountSummary): string {
    return account.account_name || `Account ${account.account_number || account.id}`;
  }

  /**
   * Get balance color based on positive/negative
   */
  getBalanceColor(balance: number): string {
    return balance >= 0 ? 'primary' : 'warn';
  }

  /**
   * Get account initials for avatar
   */
  getAccountInitials(account: AccountSummary): string {
    const name = this.getAccountDisplayName(account);
    return name.split(' ').map(word => word.charAt(0)).join('').substring(0, 2).toUpperCase();
  }

  /**
   * Get date range display
   */  getDateRangeDisplay(dateRange: [string, string]): string {
    if (!dateRange || dateRange.length !== 2) return 'N/A';
    
    const startDate = new Date(dateRange[0]);
    const endDate = new Date(dateRange[1]);
    
    const startFormatted = startDate.toLocaleDateString('en-US', { 
      day: '2-digit', 
      month: 'short', 
      year: 'numeric' 
    });
    
    const endFormatted = endDate.toLocaleDateString('en-US', { 
      day: '2-digit', 
      month: 'short', 
      year: 'numeric' 
    });
    
    return `${startFormatted} - ${endFormatted}`;
  }
  /**
   * Get categories display (first few categories)
   */
  getCategoriesDisplay(categories: string[]): string {
    if (!categories || categories.length === 0) return 'No categories';
    
    if (categories.length <= 3) {
      return categories.join(', ');
    }
    
    return `${categories.slice(0, 3).join(', ')} +${categories.length - 3} more`;
  }

  /**
   * Track by function for account list
   */
  trackByAccountId(index: number, account: AccountSummary): string {
    return account.id;
  }
}
