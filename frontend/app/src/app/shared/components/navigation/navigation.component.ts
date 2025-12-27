import { Component } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

interface NavItem {
  label: string;
  icon: string;
  route: string;
  description: string;
}

@Component({
  selector: 'app-navigation',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatTooltipModule, RouterLink, RouterLinkActive],
  templateUrl: './navigation.component.html',
  styleUrls: ['./navigation.component.scss']
})
export class NavigationComponent {
  navItems: NavItem[] = [
    {
      label: 'Upload',
      icon: 'cloud_upload',
      route: '/upload',
      description: 'Upload bank statements'
    },
    {
      label: 'Dashboard',
      icon: 'dashboard',
      route: '/dashboard',
      description: 'Financial overview and insights'
    },
    {
      label: 'Transactions',
      icon: 'receipt_long',
      route: '/transactions',
      description: 'View and manage transactions'
    },
    {
      label: 'AI Insights',
      icon: 'auto_awesome',
      route: '/ai-insights',
      description: 'Chat with your financial data'
    }
  ];

  constructor(private router: Router) {}

  navigateTo(route: string): void {
    this.router.navigate([route]);
  }

  isActive(route: string): boolean {
    return this.router.url.startsWith(route);
  }
}
