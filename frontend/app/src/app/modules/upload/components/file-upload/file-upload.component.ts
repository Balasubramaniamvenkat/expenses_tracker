import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';

import { UploadService } from '../../services/upload.service';
import { UploadFile, UploadProgress, AccountSummary } from '../../../../models/upload.model';
import { AccountSummaryComponent } from '../account-summary/account-summary.component';

@Component({
  selector: 'app-file-upload',
  templateUrl: './file-upload.component.simple.html',
  styleUrls: ['./file-upload.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatProgressBarModule,
    MatDividerModule,
    MatSnackBarModule,
    MatTooltipModule,
    AccountSummaryComponent
  ]
})
export class FileUploadComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // Observables
  uploadQueue$: Observable<UploadFile[]>;
  uploadProgress$: Observable<UploadProgress | null>;
  accounts$: Observable<AccountSummary[]>;

  // Component state
  isDragOver = false;
  isUploading = false;
  hasAccounts = false;

  constructor(
    private uploadService: UploadService,
    private snackBar: MatSnackBar
  ) {
    this.uploadQueue$ = this.uploadService.uploadQueue$;
    this.uploadProgress$ = this.uploadService.uploadProgress$;
    this.accounts$ = this.uploadService.accounts$;
  }

  ngOnInit(): void {
    this.loadExistingAccounts();
    
    // Subscribe to upload progress to manage uploading state
    this.uploadProgress$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(progress => {
      this.isUploading = !!progress;
    });

    // Subscribe to accounts to check if any exist
    this.accounts$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(accounts => {
      this.hasAccounts = accounts.length > 0;
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  /**
   * Handle file drop (simplified for direct use without ngx-file-drop)
   */
  onFileDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;
    
    if (event.dataTransfer?.files) {
      this.addFilesToQueue(Array.from(event.dataTransfer.files));
    }
  }
          if (validFiles.length > 0) {
            this.uploadService.addFilesToQueue(validFiles);
            this.showSuccess(`${validFiles.length} file(s) added to upload queue`);
          }
        });
      }
    }
  }

  /**
   * Handle traditional file input
   */
  onFileSelected(event: Event): void {
    const target = event.target as HTMLInputElement;
    const files = target.files;
    
    if (files) {
      this.addFilesToQueue(Array.from(files));
      // Clear the input to allow re-selecting the same files
      target.value = '';
    }
  }

  /**
   * Add files to upload queue with validation
   */
  private addFilesToQueue(files: File[]): void {
    const validFiles: File[] = [];
    const errors: string[] = [];
    
    files.forEach(file => {
      const validation = this.uploadService.validateFile(file);
      if (validation.valid) {
        validFiles.push(file);
      } else {
        errors.push(`${file.name}: ${validation.error}`);
      }
    });
    
    if (validFiles.length > 0) {
      this.uploadService.addFilesToQueue(validFiles);
      this.showSuccess(`${validFiles.length} file(s) added to upload queue`);
    }
    
    if (errors.length > 0) {
      errors.forEach(error => this.showError(error));
    }
  }

  /**
   * Start batch upload
   */
  startBatchUpload(): void {
    const queue = this.uploadService.getCurrentQueue();
    const pendingFiles = queue.filter(file => file.status === 'pending');
    
    if (pendingFiles.length === 0) {
      this.showError('No files ready for upload');
      return;
    }

    this.uploadService.uploadBatch().subscribe({
      next: (result) => {
        this.showSuccess(`Successfully processed ${result.successful_files} file(s)`);
        this.loadExistingAccounts(); // Refresh accounts after upload
      },
      error: (error) => {
        this.showError(`Upload failed: ${error.message}`);
      }
    });
  }

  /**
   * Remove file from queue
   */
  removeFile(fileId: string): void {
    this.uploadService.removeFileFromQueue(fileId);
    this.showSuccess('File removed from queue');
  }

  /**
   * Clear entire queue
   */
  clearQueue(): void {
    this.uploadService.clearQueue();
    this.showSuccess('Upload queue cleared');
  }

  /**
   * Clear all uploaded data
   */
  clearAllData(): void {
    if (confirm('Are you sure you want to clear all uploaded data? This action cannot be undone.')) {
      this.uploadService.clearAllData().subscribe({
        next: () => {
          this.showSuccess('All data cleared successfully');
        },
        error: (error) => {
          this.showError(`Failed to clear data: ${error.message}`);
        }
      });
    }
  }
  /**
   * Trigger file input click
   */
  triggerFileInput(): void {
    const fileInput = document.getElementById('file-input') as HTMLInputElement;
    if (fileInput) {
      fileInput.click();
    } else {
      this.showError('Could not find file input element');
    }
  }

  /**
   * Get file icon based on status
   */
  getFileStatusIcon(status: UploadFile['status']): string {
    const iconMap = {
      'pending': 'schedule',
      'uploading': 'upload',
      'processing': 'hourglass_empty',
      'success': 'check_circle',
      'error': 'error'
    };
    return iconMap[status] || 'description';
  }

  /**
   * Get status color
   */
  getStatusColor(status: UploadFile['status']): string {
    const colorMap = {
      'pending': 'primary',
      'uploading': 'accent',
      'processing': 'accent',
      'success': 'primary',
      'error': 'warn'
    };
    return colorMap[status] || 'primary';
  }
  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    return this.uploadService.formatFileSize(bytes);
  }
  /**
   * Track by function for file list
   */
  trackByFileId(index: number, file: UploadFile): string {
    return file.id;
  }

  /**
   * Load existing accounts
   */
  private loadExistingAccounts(): void {
    this.uploadService.getAccountsSummary().subscribe({
      error: (error) => {
        console.error('Failed to load accounts:', error);
      }
    });
  }

  /**
   * Show success message
   */
  private showSuccess(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 3000,
      panelClass: ['success-snackbar']
    });
  }

  /**
   * Show error message
   */
  private showError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  /**
   * Handle file over event from ngx-file-drop
   */
  fileOver(event: any): void {
    this.isDragOver = true;
  }

  /**
   * Handle file leave event from ngx-file-drop
   */
  fileLeave(event: any): void {
    this.isDragOver = false;
  }
}
