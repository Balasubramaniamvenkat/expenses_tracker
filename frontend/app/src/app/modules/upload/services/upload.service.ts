import { Injectable } from '@angular/core';
import { HttpClient, HttpEventType, HttpResponse } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError, of } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { 
  UploadFile, 
  BatchUploadResult, 
  AccountSummary, 
  UploadProgress,
  FileProcessingResult 
} from '../../../models/upload.model';

// Upload summary interfaces
export interface UploadedFileData {
  fileName: string;
  recordCount: number;
  columns: string[];
  fileSize: number;
  dateRange?: {
    from: string;
    to: string;
  };
  accounts?: string[];
}

export interface UploadSummary {
  totalFiles: number;
  totalRecords: number;
  uniqueColumns: string[];
  totalFileSize: number;
  monthsCovered?: number;
  dateRange?: {
    from: string;
    to: string;
  };
  files: UploadedFileData[];
}

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private readonly apiUrl = '/api/upload';
  
  // State management
  private uploadQueueSubject = new BehaviorSubject<UploadFile[]>([]);
  private uploadProgressSubject = new BehaviorSubject<UploadProgress | null>(null);
  private accountsSubject = new BehaviorSubject<AccountSummary[]>([]);
  private uploadSummarySubject = new BehaviorSubject<UploadSummary | null>(null);
  
  public uploadQueue$ = this.uploadQueueSubject.asObservable();
  public uploadProgress$ = this.uploadProgressSubject.asObservable();
  public accounts$ = this.accountsSubject.asObservable();
  public uploadSummary$ = this.uploadSummarySubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Add files to upload queue
   */
  addFilesToQueue(files: File[]): void {
    const currentQueue = this.uploadQueueSubject.value;
    const newFiles: UploadFile[] = files.map(file => ({
      file,
      id: this.generateFileId(),
      name: file.name,
      size: file.size,
      status: 'pending',
      progress: 0
    }));
    
    this.uploadQueueSubject.next([...currentQueue, ...newFiles]);
  }

  /**
   * Remove file from queue
   */
  removeFileFromQueue(fileId: string): void {
    const currentQueue = this.uploadQueueSubject.value;
    const updatedQueue = currentQueue.filter(file => file.id !== fileId);
    this.uploadQueueSubject.next(updatedQueue);
  }

  /**
   * Clear entire upload queue
   */
  clearQueue(): void {
    this.uploadQueueSubject.next([]);
  }

  /**
   * Get current upload queue
   */
  getCurrentQueue(): UploadFile[] {
    return this.uploadQueueSubject.value;
  }
  /**
   * Upload a single file
   */
  uploadSingleFile(uploadFile: UploadFile): Observable<FileProcessingResult> {
    const formData = new FormData();
    formData.append('file', uploadFile.file);
    
    return this.http.post<FileProcessingResult>(`${this.apiUrl}/single`, formData, {
      reportProgress: true,
      observe: 'events'
    }).pipe(
      map(event => {
        if (event.type === HttpEventType.UploadProgress && event.total) {
          // Update file progress
          const progress = Math.round(100 * event.loaded / event.total);
          this.updateFileProgress(uploadFile.id, progress, 'uploading');
          throw new Error('Progress event');
        } else if (event.type === HttpEventType.Response) {
          // Upload completed
          const response = event as HttpResponse<FileProcessingResult>;
          this.updateFileStatus(uploadFile.id, 'success', 100, response.body || undefined);
          return response.body!;
        }
        throw new Error('Unexpected event type');
      }),      catchError(error => {
        if (error.message === 'Progress event') {
          // This is not a real error, just a progress update
          return throwError(() => error);
        }
        this.updateFileStatus(uploadFile.id, 'error', 0, undefined, error.message);
        return throwError(() => error);
      })
    );
  }

  /**
   * Upload multiple files in batch
   */
  uploadBatch(): Observable<BatchUploadResult> {
    const queue = this.getCurrentQueue();
    const pendingFiles = queue.filter(file => file.status === 'pending');
    
    if (pendingFiles.length === 0) {
      return throwError(() => new Error('No files to upload'));
    }

    const formData = new FormData();
    pendingFiles.forEach((uploadFile, index) => {
      formData.append('files', uploadFile.file);
      this.updateFileStatus(uploadFile.id, 'uploading', 0);
    });

    // Initialize upload progress
    this.uploadProgressSubject.next({
      current_file: 0,
      total_files: pendingFiles.length,
      current_file_name: pendingFiles[0]?.name || '',
      current_file_progress: 0,
      overall_progress: 0,
      status: 'uploading'
    });

    return this.http.post<BatchUploadResult>(`${this.apiUrl}/batch`, formData, {
      reportProgress: true,
      observe: 'events'
    }).pipe(
      map(event => {
        if (event.type === HttpEventType.UploadProgress) {
          const progress = Math.round(100 * event.loaded / (event.total || 1));
          this.updateOverallProgress(progress);
          throw new Error('Progress event');
        } else if (event instanceof HttpResponse) {
          // Process completed
          this.processBatchResult(event.body!, pendingFiles);
          this.uploadProgressSubject.next(null); // Clear progress
          return event.body!;
        }
        throw new Error('Unexpected event type');
      }),
      catchError(error => {
        if (error.message === 'Progress event') {
          return throwError(() => error);
        }
        this.uploadProgressSubject.next(null);
        return throwError(() => error);
      })
    );
  }

  /**
   * Get accounts summary
   */
  getAccountsSummary(): Observable<AccountSummary[]> {
    return this.http.get<{accounts: AccountSummary[]}>(`${this.apiUrl}/accounts`).pipe(
      map(response => response.accounts),
      tap(accounts => this.accountsSubject.next(accounts))
    );
  }

  /**
   * Clear all uploaded data
   */
  clearAllData(): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/clear`).pipe(
      tap(() => {
        this.accountsSubject.next([]);
        this.clearQueue();
      })
    );
  }

  /**
   * Validate file before upload
   */
  validateFile(file: File): { valid: boolean; error?: string } {
    // Check file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
      return { valid: false, error: 'Only CSV files are supported' };
    }

    // Check file size (max 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      return { valid: false, error: 'File size must be less than 50MB' };
    }

    // Check if file is empty
    if (file.size === 0) {
      return { valid: false, error: 'File cannot be empty' };
    }

    return { valid: true };
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get current upload summary
   */
  getUploadSummary(): UploadSummary | null {
    return this.uploadSummarySubject.value;
  }

  /**
   * Set upload summary (persists across navigation)
   */
  setUploadSummary(summary: UploadSummary | null): void {
    this.uploadSummarySubject.next(summary);
  }

  /**
   * Clear upload summary
   */
  clearUploadSummary(): void {
    this.uploadSummarySubject.next(null);
  }

  // Private helper methods

  private generateFileId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }
  private updateFileProgress(fileId: string, progress: number, status?: UploadFile['status']): void {
    const currentQueue = this.uploadQueueSubject.value;
    const updatedQueue = currentQueue.map(file => 
      file.id === fileId 
        ? { ...file, progress, status: status || file.status }
        : file
    );
    this.uploadQueueSubject.next(updatedQueue);
  }

  private updateFileStatus(
    fileId: string, 
    status: UploadFile['status'], 
    progress?: number,
    result?: FileProcessingResult,
    error?: string
  ): void {
    const currentQueue = this.uploadQueueSubject.value;
    const updatedQueue = currentQueue.map(file => 
      file.id === fileId 
        ? { 
            ...file, 
            status, 
            progress: progress !== undefined ? progress : file.progress,
            result,
            error 
          }
        : file
    );
    this.uploadQueueSubject.next(updatedQueue);
  }

  private updateOverallProgress(progress: number): void {
    const currentProgress = this.uploadProgressSubject.value;
    if (currentProgress) {
      this.uploadProgressSubject.next({
        ...currentProgress,
        overall_progress: progress
      });
    }
  }

  private processBatchResult(result: BatchUploadResult, uploadedFiles: UploadFile[]): void {
    // Update individual file statuses based on batch result
    if (result.results) {
      result.results.forEach((fileResult, index) => {
        if (index < uploadedFiles.length) {
          const uploadFile = uploadedFiles[index];
          this.updateFileStatus(
            uploadFile.id, 
            'success', 
            100, 
            fileResult
          );
        }
      });
    }

    // Handle any errors
    if (result.errors && result.errors.length > 0) {
      result.errors.forEach((error, index) => {
        if (index < uploadedFiles.length) {
          const uploadFile = uploadedFiles[index];
          this.updateFileStatus(
            uploadFile.id, 
            'error', 
            0, 
            undefined,
            error
          );
        }
      });
    }
  }
}
