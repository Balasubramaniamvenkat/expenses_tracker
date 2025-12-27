export interface UploadFile {
  file: File;
  id: string;
  name: string;
  size: number;
  status: 'pending' | 'uploading' | 'processing' | 'success' | 'error';
  progress: number;
  error?: string;
  result?: FileProcessingResult;
}

// Alias for backward compatibility
export interface UploadedFile extends UploadFile {}

export interface ColumnMapping {
  fileId: string;
  mappings: {
    date?: string;
    description?: string;
    amount?: string;
    balance?: string;
    category?: string;
    reference?: string;
    debit?: string;
    credit?: string;
  };
}

export interface FileProcessingResult {
  filename: string;
  account_name: string;
  record_count: number;
  date_range: [string, string];
  total_expenses: number;
  total_income: number;
  categories: string[];
  category_counts: { [key: string]: number };
  columns: string[];
}

export interface BatchUploadResult {
  success: boolean;
  total_files: number;
  successful_files: number;
  failed_files: number;
  results: FileProcessingResult[];
  errors?: string[];
}

export interface AccountSummary {
  id: string;
  account_name: string;
  account_number?: string;
  person_id?: string;
  person_name?: string;
  date_range: [string, string];
  total_transactions: number;
  total_income: number;
  total_expenses: number;
  balance: number;
  categories: string[];
  file_source: string;
}

export interface UploadProgress {
  current_file: number;
  total_files: number;
  current_file_name: string;
  current_file_progress: number;
  overall_progress: number;
  status: string;
}
