import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { SimpleUploadComponent } from '../../modules/upload/components/simple-upload/simple-upload.component';

@Component({
  selector: 'app-upload-page',
  standalone: true,
  imports: [
    CommonModule, 
    MatCardModule, 
    MatButtonModule, 
    MatIconModule, 
    MatDividerModule, 
    MatProgressBarModule,
    SimpleUploadComponent
  ],
  template: `
    <div class="upload-page-container">
      <!-- Hero Section -->
      <div class="hero-section">
        <div class="hero-content">
          <div class="hero-icon">
            <mat-icon aria-hidden="true">account_balance_wallet</mat-icon>
          </div>
          <h1 class="hero-title">Family Finance Tracker</h1>
          <p class="hero-subtitle">Take control of your family finances with smart expense tracking</p>          <div class="hero-features">
            <span class="feature-badge" style="--badge-index: 0;">
              <mat-icon class="feature-icon" aria-hidden="true">lock</mat-icon>
              <span class="badge-text">100% Local</span>
            </span>
            <span class="feature-badge" style="--badge-index: 1;">
              <mat-icon class="feature-icon" aria-hidden="true">speed</mat-icon>
              <span class="badge-text">Fast Analysis</span>
            </span>
            <span class="feature-badge" style="--badge-index: 2;">
              <mat-icon class="feature-icon" aria-hidden="true">security</mat-icon>
              <span class="badge-text">Secure</span>
            </span>
          </div>
        </div>
        <div class="hero-background"></div>
      </div>

      <!-- Upload Section -->
      <div class="upload-section">
        <div class="upload-wrapper">
          <app-simple-upload></app-simple-upload>
        </div>
      </div>
      
      <!-- Info Cards Section -->
      <div class="info-section">
        <div class="section-header">
          <h2>Getting Started</h2>
          <p>Everything you need to know for successful import</p>
        </div>
        
        <div class="info-grid">
          <mat-card class="info-card">
            <div class="card-icon">
              <mat-icon>description</mat-icon>
            </div>
            <mat-card-content>
              <h3>Supported Formats</h3>
              <p>CSV files from major banks are supported. Upload your bank statements easily with drag & drop.</p>
            </mat-card-content>
          </mat-card>
          
          <mat-card class="info-card">
            <div class="card-icon">
              <mat-icon>account_balance</mat-icon>
            </div>
            <mat-card-content>
              <h3>Multiple Accounts</h3>
              <p>Combine statements from different accounts for a complete financial overview and analysis.</p>
            </mat-card-content>
          </mat-card>
          
          <mat-card class="info-card">
            <div class="card-icon">
              <mat-icon>trending_up</mat-icon>
            </div>
            <mat-card-content>
              <h3>Smart Analytics</h3>
              <p>Get insights with automatic categorization, spending trends, and detailed financial reports.</p>
            </mat-card-content>
          </mat-card>
          
          <mat-card class="info-card">
            <div class="card-icon">
              <mat-icon>shield</mat-icon>
            </div>
            <mat-card-content>
              <h3>Privacy First</h3>
              <p>Your data never leaves your device. All processing happens locally for maximum security.</p>
            </mat-card-content>
          </mat-card>
        </div>
      </div>
    </div>
  `,  styles: [`
    /* ====================================================
       UPLOAD PAGE MODERN STYLING
       ==================================================== */
    .upload-page-container {
      min-height: 100vh;
      background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
      position: relative;
      overflow-x: hidden;
    }

    /* Enhanced Hero Section */
    .hero-section {
      background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
      padding: var(--spacing-xxl) var(--spacing-lg) var(--spacing-xl);
      position: relative;
      text-align: center;
      overflow: hidden;
    }

    .hero-background {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: 
        radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
    }

    .hero-content {
      position: relative;
      z-index: 2;
      max-width: 800px;
      margin: 0 auto;
    }

    .hero-icon {
      margin-bottom: var(--spacing-lg);
    }

    .hero-icon mat-icon {
      font-size: 4rem;
      height: 4rem;
      width: 4rem;
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
      border-radius: 50%;
      padding: var(--spacing-md);
      border: 2px solid rgba(255, 255, 255, 0.3);
      box-shadow: 0 8px 32px rgba(255, 255, 255, 0.1);
      color: white;
    }

    .hero-title {
      font-size: 3rem;
      font-weight: 700;
      margin: 0 0 var(--spacing-md) 0;
      color: #ffffff;
      text-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
      letter-spacing: -1px;
      line-height: 1.2;
    }

    .hero-subtitle {
      font-size: 1.25rem;
      margin: 0 0 var(--spacing-xl) 0;
      color: rgba(255, 255, 255, 0.9);
      font-weight: 400;
      text-shadow: 0 2px 16px rgba(0, 0, 0, 0.2);
      max-width: 600px;
      margin-left: auto;
      margin-right: auto;
    }

    .hero-features {
      display: flex;
      justify-content: center;
      gap: var(--spacing-md);
      flex-wrap: wrap;
      margin-top: var(--spacing-lg);
    }    .feature-badge {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      background: rgba(255, 255, 255, 0.15);
      padding: var(--spacing-md) var(--spacing-lg);
      border-radius: var(--radius-pill);
      font-size: 0.9rem;
      font-weight: 500;
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      transition: all var(--transition-normal);
      color: #ffffff;
      text-shadow: 0 1px 8px rgba(0, 0, 0, 0.2);
      animation: badgeFloat 3s ease-in-out infinite;
      animation-delay: calc(var(--badge-index, 0) * 0.3s);
      cursor: pointer;
      white-space: nowrap;
      min-width: 140px;
      overflow: visible;
    }

    .feature-icon {
      font-size: 1.2rem !important;
      height: 1.2rem !important;
      width: 1.2rem !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      margin-right: 8px !important;
    }

    .badge-text {
      white-space: nowrap;
      overflow: visible;
      text-overflow: clip;
      flex: 1;
    }

    .feature-badge:hover {
      background: rgba(255, 255, 255, 0.25);
      transform: translateY(-4px);
      box-shadow: 0 12px 32px rgba(255, 255, 255, 0.15);
    }

    .feature-badge mat-icon {
      font-size: 1.2rem;
      height: 1.2rem;
      width: 1.2rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    /* Upload Section with Enhanced Design */
    .upload-section {
      background: var(--background);
      padding: var(--spacing-xxl) var(--spacing-lg);
      position: relative;
      z-index: 5;
      margin-top: -2rem;
      border-radius: 2rem 2rem 0 0;
    }

    .upload-wrapper {
      max-width: 1000px;
      margin: 0 auto;
      position: relative;
      z-index: 2;
    }

    /* Info Section with Modern Cards */
    .info-section {
      background: var(--background);
      padding: var(--spacing-xl) var(--spacing-lg) var(--spacing-xxl);
      position: relative;
      z-index: 5;
    }

    .section-header {
      text-align: center;
      max-width: 700px;
      margin: 0 auto var(--spacing-xxl);
    }

    .section-header h2 {
      font-size: 2.5rem;
      margin: 0 0 var(--spacing-md) 0;
      color: var(--on-surface);
      font-weight: 700;
      letter-spacing: -0.5px;
    }

    .section-header p {
      font-size: 1.2rem;
      color: var(--on-surface-medium);
      margin: 0;
      font-weight: 400;
      line-height: 1.6;
    }

    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: var(--spacing-lg);
      max-width: 1200px;
      margin: 0 auto;
    }

    .info-card {
      border-radius: var(--radius-large);
      padding: var(--spacing-xl);
      text-align: center;
      background: var(--surface);
      border: 1px solid rgba(0, 0, 0, 0.08);
      box-shadow: var(--shadow-medium);
      transition: all var(--transition-normal);
      position: relative;
      overflow: hidden;
      cursor: pointer;
    }

    .info-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, var(--primary-color), var(--secondary-color), var(--accent-color));
      transform: scaleX(0);
      transition: transform var(--transition-normal);
    }

    .info-card:hover::before {
      transform: scaleX(1);
    }

    .info-card:hover {
      transform: translateY(-8px);
      box-shadow: var(--shadow-elevation);
      border-color: rgba(25, 118, 210, 0.2);
    }

    .card-icon {
      margin-bottom: var(--spacing-lg);
      position: relative;
    }

    .card-icon mat-icon {
      font-size: 3rem;
      height: 3rem;
      width: 3rem;
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      color: white;
      border-radius: 50%;
      padding: var(--spacing-md);
      box-shadow: 0 8px 24px rgba(25, 118, 210, 0.3);
      transition: all var(--transition-normal);
    }

    .info-card:hover .card-icon mat-icon {
      transform: scale(1.1) rotate(5deg);
      box-shadow: 0 12px 32px rgba(25, 118, 210, 0.4);
    }

    .info-card h3 {
      margin: 0 0 var(--spacing-md) 0;
      font-size: 1.3rem;
      color: var(--on-surface);
      font-weight: 600;
      line-height: 1.4;
    }

    .info-card p {
      margin: 0;
      color: var(--on-surface-medium);
      line-height: 1.6;
      font-size: 1rem;
    }

    /* Enhanced Animations */
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(40px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @keyframes float {
      0%, 100% { 
        transform: translateY(0px);
      }
      50% { 
        transform: translateY(-15px);
      }
    }

    @keyframes badgeFloat {
      0%, 100% {
        transform: translateY(0px);
      }
      50% {
        transform: translateY(-8px);
      }
    }

    .info-card {
      transition: transform 0.2s ease;
    }

    .info-card:hover {
      transform: translateY(-4px);
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .hero-section {
        padding: var(--spacing-xl) var(--spacing-md);
      }
      
      .hero-title {
        font-size: 2.5rem;
      }
      
      .hero-subtitle {
        font-size: 1.1rem;
      }
      
      .hero-features {
        flex-direction: column;
        align-items: center;
        gap: var(--spacing-md);
      }
        .feature-badge {
        width: auto;
        min-width: 150px;
        justify-content: center;
        white-space: nowrap;
      }
      
      .section-header h2 {
        font-size: 2rem;
      }
      
      .info-grid {
        grid-template-columns: 1fr;
        gap: var(--spacing-md);
      }
      
      .upload-section,
      .info-section {
        padding-left: var(--spacing-md);
        padding-right: var(--spacing-md);
      }
    }

    @media (max-width: 480px) {
      .hero-section {
        padding: var(--spacing-lg) var(--spacing-md);
      }
      
      .hero-title {
        font-size: 2rem;
      }
      
      .hero-subtitle {
        font-size: 1rem;
      }
      
      .hero-icon mat-icon {
        font-size: 3rem;
        height: 3rem;
        width: 3rem;
        padding: var(--spacing-sm);
      }
      
      .info-card {
        padding: var(--spacing-lg);
      }
    }
  `]
})
export class UploadPageComponent {}
