import { Component, OnInit, OnDestroy } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { UploadService } from '../../services/upload.service';
import { UploadProgress } from '../../../../models/upload.model';

@Component({
  selector: 'app-processing-status',
  templateUrl: './processing-status.component.html',
  styleUrls: ['./processing-status.component.scss']
})
export class ProcessingStatusComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  uploadProgress$: Observable<UploadProgress | null>;
  isProcessing = false;

  constructor(private uploadService: UploadService) {
    this.uploadProgress$ = this.uploadService.uploadProgress$;
  }

  ngOnInit(): void {
    this.uploadProgress$.pipe(
      takeUntil(this.destroy$)
    ).subscribe(progress => {
      this.isProcessing = !!progress;
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Get progress percentage as integer
   */
  getProgressPercentage(progress: UploadProgress): number {
    return Math.round(progress.overall_progress);
  }

  /**
   * Get status icon based on current status
   */
  getStatusIcon(status: string): string {
    const iconMap: { [key: string]: string } = {
      'uploading': 'cloud_upload',
      'processing': 'hourglass_empty',
      'completed': 'check_circle',
      'error': 'error'
    };
    return iconMap[status] || 'upload';
  }

  /**
   * Get status color
   */
  getStatusColor(status: string): string {
    const colorMap: { [key: string]: string } = {
      'uploading': 'primary',
      'processing': 'accent',
      'completed': 'primary',
      'error': 'warn'
    };
    return colorMap[status] || 'primary';
  }

  /**
   * Get human readable status text
   */
  getStatusText(status: string): string {
    const textMap: { [key: string]: string } = {
      'uploading': 'Uploading files...',
      'processing': 'Processing data...',
      'completed': 'Processing completed',
      'error': 'Processing failed'
    };
    return textMap[status] || 'Processing...';
  }
}
