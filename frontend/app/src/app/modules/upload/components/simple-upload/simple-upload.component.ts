import { Component, OnInit, OnDestroy, AfterViewInit, ChangeDetectorRef, NgZone, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Subscription } from 'rxjs';
import { UploadService, UploadSummary, UploadedFileData } from '../../services/upload.service';

// Interface for file preview information (before upload)
interface FilePreview {
  file: File;
  name: string;
  size: number;
  rowCount: number;
  columns: string[];
  dateRange?: { from: string; to: string };
  monthsCovered?: number;
  isAnalyzing: boolean;
  error?: string;
}

@Component({
  selector: 'app-simple-upload',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    HttpClientModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatDividerModule,
    MatChipsModule,
    MatTooltipModule
  ],
  template: `
    <div class="upload-container">
      <!-- Enhanced Upload Card -->
      <mat-card class="upload-area-card">
        <mat-card-content>
          <!-- Upload Drop Zone -->
          <div class="upload-drop-zone" 
               [class.active]="isDragOver" 
               [class.disabled]="isUploading"
               (dragover)="onDragOver($event)" 
               (dragleave)="onDragLeave($event)"
               (drop)="onDrop($event)"
               (click)="!isUploading && triggerFileInput()">
            
            <!-- Simple static content that should always be visible -->
            <div class="upload-content-wrapper">
              <div class="upload-icon-area">
                <span class="upload-emoji">📁</span>
                <mat-icon class="upload-icon" [class.spinning]="isUploading" aria-hidden="true">
                  {{ isUploading ? 'hourglass_empty' : 'cloud_upload' }}
                </mat-icon>
              </div>
              
              <h3 class="upload-title">
                {{ isUploading ? 'Processing Files...' : 'Drag and drop CSV files here' }}
              </h3>
              
              <p class="upload-subtitle" *ngIf="!isUploading">or click to browse</p>
              <button mat-raised-button 
                      color="primary" 
                      *ngIf="!isUploading"
                      (click)="triggerFileInput(); $event.stopPropagation()"
                      class="browse-button">
                <mat-icon aria-hidden="true">folder_open</mat-icon>
                Browse Files
              </button>
              
              <input #fileInput
                     type="file" 
                     style="display: none" 
                     accept=".csv"
                     multiple
                     (change)="onFileSelected($event)">
              
              <p class="click-hint" *ngIf="!isUploading">
                <strong>Click anywhere in this box</strong> to select your bank statement CSV files
              </p>
              
              <div class="supported-formats" *ngIf="!isUploading">
                <span>Supported: CSV files up to 50MB each</span>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>
      
      <!-- Progress Area -->
      <mat-card *ngIf="isUploading" class="progress-card">
        <mat-card-content>
          <div class="progress-header">
            <mat-icon class="processing-icon">analytics</mat-icon>
            <div>
              <h4>Processing your files...</h4>
              <p>Analyzing data structure and content</p>
            </div>
          </div>
          <mat-progress-bar mode="indeterminate" color="accent"></mat-progress-bar>
        </mat-card-content>
      </mat-card>
      
      <!-- File List with Preview Details -->
      <mat-card *ngIf="filePreviews.length > 0 && !uploadSummary && !isUploading" class="file-list-card">
        <mat-card-header>
          <mat-icon mat-card-avatar color="primary">queue</mat-icon>
          <mat-card-title>Selected Files ({{ filePreviews.length }})</mat-card-title>
          <mat-card-subtitle>{{ getTotalPreviewRows() }} transactions ready for upload</mat-card-subtitle>
        </mat-card-header>
        
        <mat-card-content>
          <div class="file-list">
            <div *ngFor="let preview of filePreviews; trackBy: trackByPreview" class="file-item-detailed">
              <div class="file-info-header">
                <mat-icon class="file-icon">description</mat-icon>
                <div class="file-details">
                  <span class="file-name">{{ preview.name }}</span>
                  <span class="file-meta">{{ formatFileSize(preview.size) }}</span>
                </div>
                <button mat-icon-button 
                        color="warn" 
                        (click)="removeFilePreview(preview)"
                        matTooltip="Remove file">
                  <mat-icon>close</mat-icon>
                </button>
              </div>
              
              <!-- File Analysis Stats -->
              <div class="file-preview-stats" *ngIf="!preview.isAnalyzing && !preview.error">
                <div class="preview-stat">
                  <mat-icon class="stat-icon-small">receipt_long</mat-icon>
                  <span class="stat-value">{{ preview.rowCount.toLocaleString() }}</span>
                  <span class="stat-name">Transactions</span>
                </div>
                <div class="preview-stat" *ngIf="preview.monthsCovered">
                  <mat-icon class="stat-icon-small">calendar_month</mat-icon>
                  <span class="stat-value">{{ preview.monthsCovered }}</span>
                  <span class="stat-name">Months</span>
                </div>
                <div class="preview-stat" *ngIf="preview.dateRange">
                  <mat-icon class="stat-icon-small">date_range</mat-icon>
                  <span class="stat-value-small">{{ formatDateRangeShort(preview.dateRange) }}</span>
                  <span class="stat-name">Date Range</span>
                </div>
                <div class="preview-stat" *ngIf="preview.columns.length > 0">
                  <mat-icon class="stat-icon-small">view_column</mat-icon>
                  <span class="stat-value">{{ preview.columns.length }}</span>
                  <span class="stat-name">Columns</span>
                </div>
              </div>
              
              <!-- Analyzing indicator -->
              <div class="file-analyzing" *ngIf="preview.isAnalyzing">
                <mat-progress-bar mode="indeterminate"></mat-progress-bar>
                <span>Analyzing file...</span>
              </div>
              
              <!-- Error message -->
              <div class="file-error" *ngIf="preview.error">
                <mat-icon>warning</mat-icon>
                <span>{{ preview.error }}</span>
              </div>
            </div>
          </div>
          
          <!-- Combined Preview Summary -->
          <div class="preview-summary" *ngIf="filePreviews.length > 0">
            <div class="summary-row">
              <span class="summary-label">Total Transactions:</span>
              <span class="summary-value">{{ getTotalPreviewRows().toLocaleString() }}</span>
            </div>
            <div class="summary-row" *ngIf="getCombinedDateRange()">
              <span class="summary-label">Date Range:</span>
              <span class="summary-value">{{ formatDateRange(getCombinedDateRange()!) }}</span>
            </div>
            <div class="summary-row" *ngIf="getCombinedMonths() > 0">
              <span class="summary-label">Total Months:</span>
              <span class="summary-value">{{ getCombinedMonths() }}</span>
            </div>
          </div>
          
          <mat-divider></mat-divider>
          <div class="action-buttons">
            <button mat-raised-button 
                    color="primary" 
                    [disabled]="isUploading || filePreviews.length === 0 || isAnyFileAnalyzing()"
                    (click)="uploadFiles()"
                    class="upload-btn">
              <mat-icon>upload</mat-icon>
              Upload {{ filePreviews.length }} File{{ filePreviews.length !== 1 ? 's' : '' }}
            </button>
            
            <button mat-stroked-button 
                    [disabled]="isUploading"
                    (click)="clearFiles()"
                    class="clear-btn">
              <mat-icon>clear</mat-icon>
              Clear All
            </button>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Enhanced Upload Summary -->
      <mat-card *ngIf="uploadSummary" class="summary-card">
        <mat-card-content>
          <div class="summary-header">
            <div class="success-animation">
              <mat-icon class="success-icon">check_circle</mat-icon>
            </div>
            <h3>Upload Successful!</h3>
            <p>Your files have been processed and analyzed</p>
          </div>

          <mat-divider></mat-divider>

          <!-- Enhanced Summary Stats -->
          <div class="summary-stats">
            <div class="stat-card">
              <div class="stat-icon">
                <mat-icon>description</mat-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ uploadSummary.totalFiles }}</div>
                <div class="stat-label">Files Uploaded</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">
                <mat-icon>receipt_long</mat-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ uploadSummary.totalRecords.toLocaleString() }}</div>
                <div class="stat-label">Transactions</div>
              </div>
            </div>

            <div class="stat-card" *ngIf="uploadSummary.monthsCovered">
              <div class="stat-icon">
                <mat-icon>calendar_month</mat-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number">{{ uploadSummary.monthsCovered }}</div>
                <div class="stat-label">Months Covered</div>
              </div>
            </div>

            <div class="stat-card" *ngIf="uploadSummary.dateRange">
              <div class="stat-icon">
                <mat-icon>date_range</mat-icon>
              </div>
              <div class="stat-content">
                <div class="stat-number small-text">{{ formatDateRange(uploadSummary.dateRange) }}</div>
                <div class="stat-label">Date Range</div>
              </div>
            </div>
          </div>

          <mat-divider></mat-divider>

          <!-- File Details -->
          <div class="file-details-section">
            <h4>File Details</h4>
            <div class="uploaded-files">
              <div *ngFor="let file of uploadSummary.files" class="uploaded-file-item">
                <div class="file-header">
                  <mat-icon class="success-file-icon">check_circle_outline</mat-icon>
                  <div class="file-info">
                    <span class="file-name">{{ file.fileName }}</span>
                    <span class="file-stats">{{ file.recordCount.toLocaleString() }} records • {{ formatFileSize(file.fileSize) }}</span>
                  </div>
                </div>
                <div class="file-columns" *ngIf="file.columns.length > 0">
                  <mat-chip-listbox>
                    <mat-chip *ngFor="let column of file.columns.slice(0, 4)">{{ column }}</mat-chip>
                    <mat-chip *ngIf="file.columns.length > 4" class="more-chip">
                      +{{ file.columns.length - 4 }} more
                    </mat-chip>
                  </mat-chip-listbox>
                </div>
              </div>
            </div>
          </div>

          <!-- Next Steps -->
          <div class="next-steps">
            <h4>What's Next?</h4>
            <div class="next-step-buttons">
              <button mat-raised-button color="primary" routerLink="/transactions">
                <mat-icon>table_view</mat-icon>
                View Transactions
              </button>
              <button mat-stroked-button (click)="uploadMore()">
                <mat-icon>add</mat-icon>
                Upload More Files
              </button>
            </div>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,  styles: [`
    /* ====================================================
       SIMPLE UPLOAD COMPONENT MODERN STYLING
       ==================================================== */
    .upload-container {
      max-width: 800px;
      margin: 0 auto;
      padding: var(--spacing-md);
    }

    /* Enhanced Upload Area Card */
    .upload-area-card {
      border-radius: var(--radius-large);
      overflow: hidden;
      box-shadow: var(--shadow-elevation);
      transition: all var(--transition-normal);
      background: var(--surface);
      border: 2px solid transparent;
    }

    .upload-area-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }

    .upload-drop-zone {
      padding: var(--spacing-xxl);
      border: 2px dashed rgba(25, 118, 210, 0.3);
      border-radius: var(--radius-medium);
      background: linear-gradient(135deg, rgba(25, 118, 210, 0.02), rgba(0, 137, 123, 0.02));
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      cursor: pointer;
      position: relative;
      min-height: 300px;
    }

    .upload-drop-zone.active {
      border-color: var(--primary-color);
      background: linear-gradient(135deg, rgba(25, 118, 210, 0.08), rgba(0, 137, 123, 0.08));
      transform: scale(1.02);
    }

    .upload-drop-zone.disabled {
      cursor: not-allowed;
      opacity: 0.7;
    }

    /* Content wrapper to ensure visibility */
    .upload-content-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 100%;
    }

    .upload-icon-area {
      margin-bottom: var(--spacing-lg);
      position: relative;
      min-height: 4rem;
      min-width: 4rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    /* Emoji fallback always visible */
    .upload-emoji {
      font-size: 3rem;
      position: absolute;
      z-index: 1;
    }

    .upload-icon-container {
      margin-bottom: var(--spacing-lg);
      position: relative;
      min-height: 4rem;
      min-width: 4rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .upload-icon {
      font-size: 4rem;
      height: 4rem;
      width: 4rem;
      color: var(--primary-color);
    }

    /* Fallback emoji shown immediately, hidden once Material Icon loads */
    .upload-icon-fallback {
      font-size: 3.5rem;
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      opacity: 1;
      transition: opacity 0.3s ease;
    }

    /* Hide fallback once Material Icon font is loaded */
    .upload-icon:not(:empty) ~ .upload-icon-fallback,
    .mat-icon.upload-icon ~ .upload-icon-fallback {
      opacity: 0;
      pointer-events: none;
    }

    .upload-icon.spinning {
      animation: spin 1s linear infinite;
    }

    .upload-title {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: var(--spacing-sm);
      color: var(--on-surface);
      line-height: 1.4;
    }

    .upload-subtitle {
      font-size: 1rem;
      margin-bottom: var(--spacing-md);
      color: var(--on-surface-medium);
    }

    /* Click hint text for new users */
    .click-hint {
      font-size: 0.9rem;
      color: var(--primary-color);
      margin: var(--spacing-sm) 0 var(--spacing-md) 0;
      padding: var(--spacing-sm) var(--spacing-md);
      background: rgba(25, 118, 210, 0.08);
      border-radius: var(--radius-small);
      border: 1px dashed rgba(25, 118, 210, 0.3);
    }

    .click-hint strong {
      color: var(--primary-dark);
    }

    .browse-button {
      padding: 0 var(--spacing-xl);
      height: 48px;
      border-radius: var(--radius-pill);
      font-weight: 500;
      font-size: 1rem;
      margin-bottom: var(--spacing-md);
      box-shadow: var(--shadow-medium);
      transition: all var(--transition-normal);
    }

    .browse-button:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-large);
    }

    .browse-button mat-icon {
      margin-right: 8px;
    }

    .supported-formats {
      font-size: 0.875rem;
      color: var(--on-surface-medium);
      opacity: 0.8;
    }

    /* Progress Card */
    .progress-card {
      margin-top: var(--spacing-lg);
      border-radius: var(--radius-large);
      box-shadow: var(--shadow-medium);
    }

    .progress-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      margin-bottom: var(--spacing-md);
    }

    .processing-icon {
      font-size: 2rem;
      height: 2rem;
      width: 2rem;
      color: var(--secondary-color);
      animation: pulse 1.5s ease-in-out infinite;
    }

    .progress-header h4 {
      margin: 0;
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--on-surface);
    }

    .progress-header p {
      margin: 0;
      font-size: 0.9rem;
      color: var(--on-surface-medium);
    }

    /* File List Card */
    .file-list-card {
      margin-top: var(--spacing-lg);
      border-radius: var(--radius-large);
      box-shadow: var(--shadow-medium);
    }

    .file-list {
      margin-bottom: var(--spacing-lg);
    }

    .file-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--spacing-md);
      border-radius: var(--radius-medium);
      transition: all var(--transition-fast);
      background: var(--surface-hover);
      margin-bottom: var(--spacing-sm);
    }

    .file-item:hover {
      background: rgba(25, 118, 210, 0.04);
    }

    /* Enhanced File Item with Preview Details */
    .file-item-detailed {
      background: var(--surface-hover);
      border-radius: var(--radius-medium);
      padding: var(--spacing-md);
      margin-bottom: var(--spacing-md);
      border: 1px solid rgba(0, 0, 0, 0.08);
      transition: all var(--transition-fast);
    }

    .file-item-detailed:hover {
      border-color: var(--primary-color);
      box-shadow: var(--shadow-small);
    }

    .file-info-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      margin-bottom: var(--spacing-sm);
    }

    .file-info-header .file-details {
      flex: 1;
    }

    .file-meta {
      font-size: 0.8rem;
      color: var(--on-surface-medium);
      display: block;
    }

    /* File Preview Stats */
    .file-preview-stats {
      display: flex;
      flex-wrap: wrap;
      gap: var(--spacing-md);
      padding: var(--spacing-sm) 0;
      margin-left: calc(1.5rem + var(--spacing-md));
    }

    .preview-stat {
      display: flex;
      align-items: center;
      gap: var(--spacing-xs);
      background: rgba(25, 118, 210, 0.08);
      padding: var(--spacing-xs) var(--spacing-sm);
      border-radius: var(--radius-small);
      font-size: 0.85rem;
    }

    .stat-icon-small {
      font-size: 1rem !important;
      height: 1rem !important;
      width: 1rem !important;
      color: var(--primary-color);
    }

    .stat-value {
      font-weight: 600;
      color: var(--on-surface);
    }

    .stat-value-small {
      font-weight: 500;
      color: var(--on-surface);
      font-size: 0.8rem;
    }

    .stat-name {
      color: var(--on-surface-medium);
      font-size: 0.75rem;
    }

    /* File Analyzing State */
    .file-analyzing {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      margin-left: calc(1.5rem + var(--spacing-md));
      color: var(--on-surface-medium);
      font-size: 0.85rem;
    }

    .file-analyzing mat-progress-bar {
      width: 100px;
    }

    /* File Error State */
    .file-error {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm);
      margin-left: calc(1.5rem + var(--spacing-md));
      color: var(--error-color);
      font-size: 0.85rem;
    }

    .file-error mat-icon {
      font-size: 1rem;
      height: 1rem;
      width: 1rem;
    }

    /* Preview Summary Box */
    .preview-summary {
      background: linear-gradient(135deg, rgba(25, 118, 210, 0.05), rgba(0, 137, 123, 0.05));
      border-radius: var(--radius-medium);
      padding: var(--spacing-md);
      margin: var(--spacing-md) 0;
      border: 1px solid rgba(25, 118, 210, 0.2);
    }

    .summary-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--spacing-xs) 0;
    }

    .summary-row:not(:last-child) {
      border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    }

    .summary-label {
      font-weight: 500;
      color: var(--on-surface-medium);
    }

    .summary-value {
      font-weight: 600;
      color: var(--primary-color);
    }

    .file-info {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      flex: 1;
    }

    .file-icon {
      color: var(--primary-color);
      font-size: 1.5rem;
    }

    .file-details {
      display: flex;
      flex-direction: column;
    }

    .file-name {
      font-weight: 500;
      color: var(--on-surface);
      font-size: 0.95rem;
    }

    .file-size {
      font-size: 0.8rem;
      color: var(--on-surface-medium);
    }

    .action-buttons {
      display: flex;
      gap: var(--spacing-md);
      justify-content: center;
      margin-top: var(--spacing-lg);
    }    .upload-btn, .clear-btn {
      min-width: 140px;
      height: 44px;
      border-radius: var(--radius-medium);
      font-weight: 500;
    }

    .upload-btn mat-icon,
    .clear-btn mat-icon {
      margin-right: 8px;
    }

    /* Summary Card */
    .summary-card {
      margin-top: var(--spacing-lg);
      border-radius: var(--radius-large);
      box-shadow: var(--shadow-elevation);
      border: 1px solid rgba(76, 175, 80, 0.2);
    }

    .summary-header {
      text-align: center;
      margin-bottom: var(--spacing-lg);
    }

    .success-animation {
      margin-bottom: var(--spacing-md);
    }

    .success-icon {
      font-size: 3rem;
      height: 3rem;
      width: 3rem;
      color: var(--success-color);
      animation: successPulse 1s ease-out;
    }

    .summary-header h3 {
      font-size: 1.5rem;
      font-weight: 600;
      margin: 0 0 var(--spacing-sm) 0;
      color: var(--on-surface);
    }

    .summary-header p {
      margin: 0;
      color: var(--on-surface-medium);
      font-size: 1rem;
    }    .summary-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: var(--spacing-md);
      margin: var(--spacing-lg) 0;
      overflow: visible;
    }.stat-card {
      background: var(--surface-hover);
      padding: var(--spacing-lg);
      border-radius: var(--radius-medium);
      text-align: center;
      transition: all var(--transition-normal);
      border: 1px solid rgba(0, 0, 0, 0.08);
      overflow: visible;
      min-width: 150px;
    }

    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-medium);
    }

    .stat-icon {
      margin-bottom: var(--spacing-sm);
    }

    .stat-icon mat-icon {
      font-size: 2rem;
      height: 2rem;
      width: 2rem;
      color: var(--primary-color);
    }

    .stat-content {
      overflow: visible;
      width: 100%;
    }

    .stat-number {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--on-surface);
      margin-bottom: var(--spacing-xs);
      overflow: visible;
      white-space: nowrap;
    }

    .stat-number.small-text {
      font-size: 0.95rem;
      font-weight: 600;
    }

    .stat-label {
      font-size: 0.875rem;
      color: var(--on-surface-medium);
      font-weight: 500;
      overflow: visible;
      white-space: normal;
      text-overflow: clip;
      width: 100%;
      min-width: 100px;
    }

    .file-details-section h4,
    .next-steps h4 {
      font-size: 1.2rem;
      font-weight: 600;
      margin: var(--spacing-lg) 0 var(--spacing-md) 0;
      color: var(--on-surface);
    }

    .uploaded-file-item {
      background: var(--surface-hover);
      padding: var(--spacing-md);
      border-radius: var(--radius-medium);
      margin-bottom: var(--spacing-md);
    }

    .file-header {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      margin-bottom: var(--spacing-sm);
    }

    .success-file-icon {
      color: var(--success-color);
    }

    .file-stats {
      font-size: 0.85rem;
      color: var(--on-surface-medium);
    }

    .next-step-buttons {
      display: flex;
      gap: var(--spacing-md);
      justify-content: center;
      flex-wrap: wrap;
    }

    .next-step-buttons button {
      min-width: 160px;
      height: 44px;
      border-radius: var(--radius-medium);
      font-weight: 500;
    }

    /* Animations - only for spinner */
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    /* Responsive Design */
    @media (max-width: 768px) {
      .upload-container {
        padding: var(--spacing-sm);
      }

      .upload-drop-zone {
        padding: var(--spacing-lg);
        min-height: 250px;
      }

      .upload-icon {
        font-size: 3rem;
        height: 3rem;
        width: 3rem;
      }

      .upload-pulse-ring {
        width: 4rem;
        height: 4rem;
      }

      .action-buttons {
        flex-direction: column;
      }

      .summary-stats {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: var(--spacing-sm);
      }

      .next-step-buttons {
        flex-direction: column;
      }
    }

    @media (max-width: 480px) {
      .upload-title {
        font-size: 1.25rem;
      }

      .stat-card {
        padding: var(--spacing-md);
      }

      .stat-number {
        font-size: 1.25rem;
      }
    }
  `]
})
export class SimpleUploadComponent implements OnInit, OnDestroy, AfterViewInit {
  files: File[] = [];
  filePreviews: FilePreview[] = [];
  isDragOver = false;
  isUploading = false;
  uploadSummary: UploadSummary | null = null;
  isContentReady = false; // Track when content should be visible
  private apiUrl = 'http://localhost:8000/api/upload';
  private summarySubscription: Subscription | null = null;

  constructor(
    private snackBar: MatSnackBar, 
    private http: HttpClient,
    private uploadService: UploadService,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone,
    private elementRef: ElementRef
  ) {}

  ngOnInit(): void {
    // Subscribe to upload summary from service to persist across navigation
    this.summarySubscription = this.uploadService.uploadSummary$.subscribe(summary => {
      console.log('Received summary from service:', summary);
      this.uploadSummary = summary;
    });
  }

  ngAfterViewInit(): void {
    // Force content to be visible after view initialization
    // This fixes a rendering issue where content doesn't appear until user interaction
    this.ngZone.runOutsideAngular(() => {
      // Use requestAnimationFrame to ensure DOM is ready
      requestAnimationFrame(() => {
        // Force a repaint by reading and writing to the DOM
        const element = this.elementRef.nativeElement;
        if (element) {
          // Trigger reflow
          element.offsetHeight;
          
          // Then trigger change detection in Angular zone
          this.ngZone.run(() => {
            this.isContentReady = true;
            this.cdr.detectChanges();
          });
        }
      });
    });
  }

  ngOnDestroy(): void {
    if (this.summarySubscription) {
      this.summarySubscription.unsubscribe();
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;

    const files = Array.from(event.dataTransfer?.files || []);
    this.addFiles(files);
  }

  triggerFileInput(): void {
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    fileInput?.click();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      const files = Array.from(input.files);
      this.addFiles(files);
    }
  }

  private addFiles(files: File[]): void {
    const csvFiles = files.filter(file => file.name.toLowerCase().endsWith('.csv'));
    
    if (csvFiles.length !== files.length) {
      this.snackBar.open('Only CSV files are supported', 'Close', { duration: 3000 });
    }

    // Check file size (50MB limit)
    const oversizedFiles = csvFiles.filter(file => file.size > 50 * 1024 * 1024);
    if (oversizedFiles.length > 0) {
      this.snackBar.open(`Some files exceed 50MB limit and were skipped`, 'Close', { duration: 3000 });
    }

    const validFiles = csvFiles.filter(file => file.size <= 50 * 1024 * 1024);
    
    // Add only new files (avoid duplicates)
    const newFiles = validFiles.filter(file => 
      !this.filePreviews.some(existing => existing.name === file.name && existing.size === file.size)
    );

    // Create preview entries and analyze each file
    newFiles.forEach(file => {
      const preview: FilePreview = {
        file: file,
        name: file.name,
        size: file.size,
        rowCount: 0,
        columns: [],
        isAnalyzing: true
      };
      this.filePreviews.push(preview);
      this.files.push(file);
      
      // Analyze file in background
      this.analyzeCSVFile(preview);
    });

    if (newFiles.length > 0) {
      this.snackBar.open(`${newFiles.length} file(s) added - analyzing...`, 'Close', { duration: 2000 });
    }
  }

  /**
   * Analyze CSV file to extract preview information (row count, columns, date range)
   */
  private analyzeCSVFile(preview: FilePreview): void {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        if (!content) {
          preview.isAnalyzing = false;
          preview.error = 'Could not read file';
          return;
        }

        const lines = content.split(/\r?\n/).filter(line => line.trim() !== '');
        
        if (lines.length < 2) {
          preview.isAnalyzing = false;
          preview.error = 'File appears to be empty';
          return;
        }

        // Parse header
        const headerLine = lines[0];
        const columns = this.parseCSVLine(headerLine);
        preview.columns = columns;
        
        // Count data rows (excluding header)
        preview.rowCount = lines.length - 1;

        // Try to find date column and extract date range
        const dateColumnIndex = this.findDateColumnIndex(columns);
        if (dateColumnIndex >= 0) {
          const dates = this.extractDates(lines.slice(1), dateColumnIndex);
          if (dates.length > 0) {
            dates.sort((a, b) => a.getTime() - b.getTime());
            const fromDate = dates[0];
            const toDate = dates[dates.length - 1];
            
            preview.dateRange = {
              from: this.formatISODate(fromDate),
              to: this.formatISODate(toDate)
            };
            
            // Calculate months covered
            preview.monthsCovered = this.calculateMonthsDiff(fromDate, toDate);
          }
        }

        preview.isAnalyzing = false;
      } catch (error) {
        console.error('Error analyzing CSV:', error);
        preview.isAnalyzing = false;
        preview.error = 'Error analyzing file';
      }
    };

    reader.onerror = () => {
      preview.isAnalyzing = false;
      preview.error = 'Error reading file';
    };

    reader.readAsText(preview.file);
  }

  /**
   * Parse a CSV line handling quoted fields
   */
  private parseCSVLine(line: string): string[] {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    
    result.push(current.trim());
    return result;
  }

  /**
   * Find the index of the date column
   */
  private findDateColumnIndex(columns: string[]): number {
    const dateColumnNames = ['date', 'transaction date', 'trans date', 'txn date', 'value date', 'posting date'];
    const lowerColumns = columns.map(c => c.toLowerCase().trim());
    
    for (const name of dateColumnNames) {
      const index = lowerColumns.findIndex(c => c === name || c.includes(name));
      if (index >= 0) return index;
    }
    
    // If no explicit date column, check first column
    return 0;
  }

  /**
   * Extract dates from CSV lines
   */
  private extractDates(lines: string[], columnIndex: number): Date[] {
    const dates: Date[] = [];
    const dateFormats = [
      /(\d{2})\/(\d{2})\/(\d{4})/, // DD/MM/YYYY
      /(\d{2})-(\d{2})-(\d{4})/, // DD-MM-YYYY
      /(\d{4})-(\d{2})-(\d{2})/, // YYYY-MM-DD
      /(\d{2})\/(\d{2})\/(\d{2})/, // DD/MM/YY
    ];
    
    for (const line of lines.slice(0, 100)) { // Sample first 100 rows for performance
      const values = this.parseCSVLine(line);
      if (values.length > columnIndex) {
        const dateStr = values[columnIndex].trim().replace(/"/g, '');
        const date = this.parseDate(dateStr);
        if (date && !isNaN(date.getTime())) {
          dates.push(date);
        }
      }
    }
    
    return dates;
  }

  /**
   * Parse date string in various formats
   */
  private parseDate(dateStr: string): Date | null {
    // Try DD/MM/YYYY or DD-MM-YYYY
    let match = dateStr.match(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/);
    if (match) {
      return new Date(parseInt(match[3]), parseInt(match[2]) - 1, parseInt(match[1]));
    }
    
    // Try YYYY-MM-DD
    match = dateStr.match(/(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})/);
    if (match) {
      return new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3]));
    }
    
    // Try DD/MM/YY
    match = dateStr.match(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2})/);
    if (match) {
      const year = parseInt(match[3]);
      const fullYear = year > 50 ? 1900 + year : 2000 + year;
      return new Date(fullYear, parseInt(match[2]) - 1, parseInt(match[1]));
    }
    
    return null;
  }

  /**
   * Format date as ISO string (YYYY-MM-DD)
   */
  private formatISODate(date: Date): string {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }

  /**
   * Calculate months difference between two dates
   */
  private calculateMonthsDiff(from: Date, to: Date): number {
    return (to.getFullYear() - from.getFullYear()) * 12 + (to.getMonth() - from.getMonth()) + 1;
  }

  // Preview helper methods
  getTotalPreviewRows(): number {
    return this.filePreviews.reduce((sum, p) => sum + p.rowCount, 0);
  }

  getCombinedDateRange(): { from: string; to: string } | null {
    const allDates: string[] = [];
    this.filePreviews.forEach(p => {
      if (p.dateRange) {
        allDates.push(p.dateRange.from, p.dateRange.to);
      }
    });
    
    if (allDates.length === 0) return null;
    
    allDates.sort();
    return {
      from: allDates[0],
      to: allDates[allDates.length - 1]
    };
  }

  getCombinedMonths(): number {
    const dateRange = this.getCombinedDateRange();
    if (!dateRange) return 0;
    
    const from = new Date(dateRange.from);
    const to = new Date(dateRange.to);
    return this.calculateMonthsDiff(from, to);
  }

  isAnyFileAnalyzing(): boolean {
    return this.filePreviews.some(p => p.isAnalyzing);
  }

  formatDateRangeShort(dateRange: { from: string; to: string }): string {
    try {
      const fromDate = new Date(dateRange.from);
      const toDate = new Date(dateRange.to);
      const fromMonth = fromDate.toLocaleString('default', { month: 'short' });
      const toMonth = toDate.toLocaleString('default', { month: 'short' });
      return `${fromMonth} ${fromDate.getFullYear()} - ${toMonth} ${toDate.getFullYear()}`;
    } catch {
      return `${dateRange.from} - ${dateRange.to}`;
    }
  }

  removeFilePreview(preview: FilePreview): void {
    this.filePreviews = this.filePreviews.filter(p => p !== preview);
    this.files = this.files.filter(f => f !== preview.file);
  }

  trackByPreview(index: number, preview: FilePreview): string {
    return preview.name + preview.size;
  }

  removeFile(file: File): void {
    this.files = this.files.filter(f => f !== file);
    this.filePreviews = this.filePreviews.filter(p => p.file !== file);
  }

  clearFiles(): void {
    this.files = [];
    this.filePreviews = [];
    this.uploadService.clearUploadSummary();
  }

  uploadFiles(): void {
    if (this.files.length === 0) return;

    this.isUploading = true;

    // Upload files one by one to the backend API
    const uploadPromises = this.files.map(file => {
      const formData = new FormData();
      formData.append('file', file);
      return this.http.post<any>(`${this.apiUrl}/single`, formData).toPromise();
    });

    Promise.all(uploadPromises)
      .then(results => {
        this.isUploading = false;
        this.createUploadSummaryFromResults(results);
        this.snackBar.open('Files uploaded and processed successfully!', 'Close', { duration: 3000 });
      })
      .catch(error => {
        this.isUploading = false;
        console.error('Upload error:', error);
        this.snackBar.open('Error uploading files. Please try again.', 'Close', { duration: 5000 });
      });
  }

  private createUploadSummaryFromResults(results: any[]): void {
    console.log('Upload results:', results);
    
    const successfulUploads = results.filter(r => r && r.success);
    console.log('Successful uploads:', successfulUploads);
    
    const fileData: UploadedFileData[] = successfulUploads.map(result => {
      // Get columns from preview_data if available
      let columns: string[] = [];
      if (result.preview_data && result.preview_data.length > 0) {
        columns = Object.keys(result.preview_data[0]);
      }
      
      return {
        fileName: result.filename || 'Unknown',
        recordCount: result.records_processed || 0,
        columns: columns,
        fileSize: result.file_size || 0,
        dateRange: result.summary?.date_range
      };
    });
    
    console.log('File data:', fileData);

    // Collect all unique columns from all files
    const allColumns = new Set<string>();
    fileData.forEach(f => f.columns.forEach(c => allColumns.add(c)));

    // Calculate combined date range and months covered from all files
    let combinedDateRange: { from: string; to: string } | undefined = undefined;
    let monthsCovered = 0;
    
    // Get months_covered from the first successful result's summary
    if (successfulUploads.length > 0 && successfulUploads[0].summary) {
      monthsCovered = successfulUploads[0].summary.months_covered || 0;
      combinedDateRange = successfulUploads[0].summary.date_range;
    }
    
    // If we have multiple files, calculate the combined range
    if (fileData.length > 1) {
      const allDates: string[] = [];
      fileData.forEach(f => {
        if (f.dateRange) {
          allDates.push(f.dateRange.from, f.dateRange.to);
        }
      });
      
      if (allDates.length > 0) {
        allDates.sort();
        combinedDateRange = {
          from: allDates[0],
          to: allDates[allDates.length - 1]
        };
        
        // Recalculate months covered
        const fromDate = new Date(combinedDateRange.from);
        const toDate = new Date(combinedDateRange.to);
        monthsCovered = (toDate.getFullYear() - fromDate.getFullYear()) * 12 + 
                        (toDate.getMonth() - fromDate.getMonth()) + 1;
      }
    }

    const summary: UploadSummary = {
      totalFiles: fileData.length,
      totalRecords: fileData.reduce((sum, file) => sum + file.recordCount, 0),
      uniqueColumns: Array.from(allColumns),
      totalFileSize: fileData.reduce((sum, file) => sum + file.fileSize, 0),
      monthsCovered: monthsCovered,
      dateRange: combinedDateRange,
      files: fileData
    };
    
    console.log('Final summary:', summary);

    // Persist summary in service so it survives navigation
    this.uploadService.setUploadSummary(summary);

    this.files = []; // Clear files after successful upload
    this.filePreviews = []; // Clear previews after successful upload
  }

  private createUploadSummary(): void {
    const mockColumns = ['Date', 'Description', 'Amount', 'Category', 'Account'];
    const mockFileData: UploadedFileData[] = this.files.map(file => ({
      fileName: file.name,
      recordCount: Math.floor(Math.random() * 500) + 100,
      columns: mockColumns,
      fileSize: file.size,
      dateRange: {
        from: '2024-01-01',
        to: '2024-12-31'
      }
    }));

    this.uploadSummary = {
      totalFiles: this.files.length,
      totalRecords: mockFileData.reduce((sum, file) => sum + file.recordCount, 0),
      uniqueColumns: mockColumns,
      totalFileSize: this.files.reduce((sum, file) => sum + file.size, 0),
      dateRange: {
        from: '2024-01-01',
        to: '2024-12-31'
      },
      files: mockFileData
    };

    this.files = []; // Clear files after successful upload
  }

  uploadMore(): void {
    this.uploadService.clearUploadSummary();
    this.files = [];
    this.filePreviews = [];
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatDateRange(dateRange: { from: string; to: string }): string {
    try {
      const fromDate = new Date(dateRange.from);
      const toDate = new Date(dateRange.to);
      
      const formatShortDate = (date: Date): string => {
        const month = date.toLocaleString('default', { month: 'short' });
        const day = date.getDate();
        const year = date.getFullYear();
        return `${month} ${day}, ${year}`;
      };
      
      return `${formatShortDate(fromDate)} - ${formatShortDate(toDate)}`;
    } catch (error) {
      return `${dateRange.from} - ${dateRange.to}`;
    }
  }

  trackByFile(index: number, file: File): string {
    return file.name + file.size;
  }
}
