import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject, of, throwError } from 'rxjs';
import { delay, tap } from 'rxjs/operators';
import { 
  UploadFile, 
  BatchUploadResult, 
  AccountSummary, 
  UploadProgress,
  FileProcessingResult 
} from '../../../models/upload.model';

/**
 * Mock implementation of UploadService for UI testing
 * This service simulates API calls without requiring a backend
 */
@Injectable({
  providedIn: 'root'
})
export class UploadService {
  // State management
  private uploadQueueSubject = new BehaviorSubject<UploadFile[]>([]);
  private uploadProgressSubject = new BehaviorSubject<UploadProgress | null>(null);
  private accountsSubject = new BehaviorSubject<AccountSummary[]>([]);
  
  public uploadQueue$ = this.uploadQueueSubject.asObservable();
  public uploadProgress$ = this.uploadProgressSubject.asObservable();
  public accounts$ = this.accountsSubject.asObservable();

  constructor() {
    console.log('Using mock UploadService');
  }

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
   * Upload a single file - MOCK IMPLEMENTATION
   */
  uploadSingleFile(uploadFile: UploadFile): Observable<FileProcessingResult> {
    // Simulate file upload with progress
    this.updateFileStatus(uploadFile.id, 'uploading', 0);
    
    // Mock result to return after "processing"
    const mockResult: FileProcessingResult = {
      filename: uploadFile.name,
      account_name: `Account ${Math.floor(Math.random() * 9000) + 1000}`,
      record_count: Math.floor(Math.random() * 200) + 50,
      date_range: ['2025-01-01', '2025-03-31'],
      total_expenses: Math.floor(Math.random() * 5000) + 1000,
      total_income: Math.floor(Math.random() * 7000) + 3000,
      categories: ['Groceries', 'Utilities', 'Entertainment', 'Transport'],
      category_counts: {
        'Groceries': 12,
        'Utilities': 6,
        'Entertainment': 8,
        'Transport': 10
      },
      columns: ['Date', 'Description', 'Amount', 'Balance', 'Category']
    };
    
    // Simulate progress updates
    let progress = 0;
    const progressInterval = setInterval(() => {
      progress += 10;
      if (progress <= 100) {
        this.updateFileProgress(uploadFile.id, progress, 'uploading');
      } else {
        clearInterval(progressInterval);
      }
    }, 300);
    
    // Return mock result after "processing" delay
    return of(mockResult).pipe(
      delay(4000),
      tap(() => {
        this.updateFileStatus(uploadFile.id, 'success', 100, mockResult);
        clearInterval(progressInterval);
      })
    );
  }

  /**
   * Upload multiple files in batch - MOCK IMPLEMENTATION
   */
  uploadBatch(): Observable<BatchUploadResult> {
    const queue = this.getCurrentQueue();
    const pendingFiles = queue.filter(file => file.status === 'pending');
    
    if (pendingFiles.length === 0) {
      return throwError(() => new Error('No files to upload'));
    }

    // Initialize upload progress
    this.uploadProgressSubject.next({
      current_file: 0,
      total_files: pendingFiles.length,
      current_file_name: pendingFiles[0]?.name || '',
      current_file_progress: 0,
      overall_progress: 0,
      status: 'uploading'
    });

    // Process each file with simulated delay
    let currentFileIndex = 0;
    let overallProgress = 0;
    
    const processNextFile = () => {
      if (currentFileIndex >= pendingFiles.length) {
        // All files processed
        return;
      }
      
      const currentFile = pendingFiles[currentFileIndex];
      this.updateFileStatus(currentFile.id, 'uploading', 0);
      
      // Update progress tracker
      this.uploadProgressSubject.next({
        current_file: currentFileIndex + 1,
        total_files: pendingFiles.length,
        current_file_name: currentFile.name,
        current_file_progress: 0,
        overall_progress: Math.floor(overallProgress / pendingFiles.length),
        status: 'uploading'
      });
      
      // Simulate file upload progress
      let fileProgress = 0;
      const progressInterval = setInterval(() => {
        fileProgress += 5;
        
        // Update file progress
        this.updateFileProgress(currentFile.id, fileProgress, 'uploading');
        
        // Update overall progress
        overallProgress = (currentFileIndex * 100 + fileProgress) / pendingFiles.length;
        this.uploadProgressSubject.next({
          current_file: currentFileIndex + 1,
          total_files: pendingFiles.length,
          current_file_name: currentFile.name,
          current_file_progress: fileProgress,
          overall_progress: Math.floor(overallProgress),
          status: 'uploading'
        });
        
        if (fileProgress >= 100) {
          clearInterval(progressInterval);
          
          // Create mock result for this file
          const mockResult: FileProcessingResult = {
            filename: currentFile.name,
            account_name: `Account ${Math.floor(Math.random() * 9000) + 1000}`,
            record_count: Math.floor(Math.random() * 200) + 50,
            date_range: ['2025-01-01', '2025-03-31'],
            total_expenses: Math.floor(Math.random() * 5000) + 1000,
            total_income: Math.floor(Math.random() * 7000) + 3000,
            categories: ['Groceries', 'Utilities', 'Entertainment', 'Transport'],
            category_counts: {
              'Groceries': 12,
              'Utilities': 6,
              'Entertainment': 8,
              'Transport': 10
            },
            columns: ['Date', 'Description', 'Amount', 'Balance', 'Category']
          };
          
          // Update file status to success
          this.updateFileStatus(currentFile.id, 'success', 100, mockResult);
          
          // Move to next file after delay
          setTimeout(() => {
            currentFileIndex++;
            processNextFile();
          }, 500);
        }
      }, 200);
    };
    
    // Start processing files
    processNextFile();
    
    // Return mock batch result after all files are "processed"
    const mockBatchResult: BatchUploadResult = {
      success: true,
      total_files: pendingFiles.length,
      successful_files: pendingFiles.length,
      failed_files: 0,
      results: pendingFiles.map(file => ({
        filename: file.name,
        account_name: `Account ${Math.floor(Math.random() * 9000) + 1000}`,
        record_count: Math.floor(Math.random() * 200) + 50,
        date_range: ['2025-01-01', '2025-03-31'],
        total_expenses: Math.floor(Math.random() * 5000) + 1000,
        total_income: Math.floor(Math.random() * 7000) + 3000,
        categories: ['Groceries', 'Utilities', 'Entertainment', 'Transport'],
        category_counts: {
          'Groceries': 12,
          'Utilities': 6,
          'Entertainment': 8,
          'Transport': 10
        },
        columns: ['Date', 'Description', 'Amount', 'Balance', 'Category']
      }))
    };
    
    return of(mockBatchResult).pipe(
      delay(pendingFiles.length * 2000),
      tap(() => {
        // Clear progress
        this.uploadProgressSubject.next(null);
        
        // Update accounts
        this.getAccountsSummary().subscribe();
      })
    );
  }

  /**
   * Get accounts summary - MOCK IMPLEMENTATION
   */
  getAccountsSummary(): Observable<AccountSummary[]> {
    // Generate mock accounts based on successfully uploaded files
    const successfulFiles = this.getCurrentQueue().filter(file => file.status === 'success');
    
    const mockAccounts: AccountSummary[] = successfulFiles.map((file, index) => ({
      id: `acc-${index}`,
      account_name: file.result?.account_name || `Account ${Math.floor(Math.random() * 9000) + 1000}`,
      account_number: `XXXX${Math.floor(1000 + Math.random() * 9000)}`,
      person_id: `person-${index % 3}`,
      person_name: ['John Doe', 'Jane Smith', 'Family Joint'][index % 3],
      date_range: ['2025-01-01', '2025-03-31'],
      total_transactions: Math.floor(Math.random() * 200) + 50,
      total_income: Math.floor(Math.random() * 10000) + 5000,
      total_expenses: Math.floor(Math.random() * 8000) + 3000,
      balance: Math.floor(Math.random() * 15000) - 5000,
      categories: ['Groceries', 'Utilities', 'Entertainment', 'Transport', 'Dining', 'Healthcare'],
      file_source: file.name
    }));
    
    return of(mockAccounts).pipe(
      delay(800),
      tap(accounts => this.accountsSubject.next(accounts))
    );
  }

  /**
   * Clear all uploaded data - MOCK IMPLEMENTATION
   */
  clearAllData(): Observable<void> {
    // Clear queue and accounts
    this.clearQueue();
    this.accountsSubject.next([]);
    
    return of(undefined).pipe(delay(500));
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
}
