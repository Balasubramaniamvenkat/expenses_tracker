import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UploadedFile, ColumnMapping } from '../../../../models/upload.model';

@Component({
  selector: 'app-column-mapping',
  templateUrl: './column-mapping.component.html',
  styleUrls: ['./column-mapping.component.scss']
})
export class ColumnMappingComponent implements OnInit {
  @Input() file!: UploadedFile;
  @Input() availableColumns: string[] = [];
  @Output() mappingComplete = new EventEmitter<ColumnMapping>();
  @Output() cancel = new EventEmitter<void>();

  mappingForm: FormGroup;
  
  // Standard column types we expect
  requiredColumns = [
    { key: 'date', label: 'Date', required: true },
    { key: 'description', label: 'Description', required: true },
    { key: 'amount', label: 'Amount', required: true },
    { key: 'balance', label: 'Balance', required: false }
  ];

  optionalColumns = [
    { key: 'category', label: 'Category', required: false },
    { key: 'reference', label: 'Reference Number', required: false },
    { key: 'debit', label: 'Debit Amount', required: false },
    { key: 'credit', label: 'Credit Amount', required: false }
  ];

  constructor(private fb: FormBuilder) {
    this.mappingForm = this.fb.group({});
  }

  ngOnInit(): void {
    this.initializeForm();
    this.detectColumns();
  }

  private initializeForm(): void {
    const formControls: { [key: string]: any } = {};
    
    // Add form controls for required columns
    this.requiredColumns.forEach(col => {
      formControls[col.key] = [null, col.required ? Validators.required : null];
    });

    // Add form controls for optional columns
    this.optionalColumns.forEach(col => {
      formControls[col.key] = [null];
    });

    this.mappingForm = this.fb.group(formControls);
  }

  private detectColumns(): void {
    // Auto-detect common column patterns
    const detectedMappings: { [key: string]: string } = {};

    this.availableColumns.forEach(column => {
      const lowerColumn = column.toLowerCase();
      
      // Date column detection
      if (lowerColumn.includes('date') || lowerColumn.includes('transaction') || lowerColumn.includes('value')) {
        if (!detectedMappings['date']) {
          detectedMappings['date'] = column;
        }
      }
      
      // Description column detection
      if (lowerColumn.includes('description') || lowerColumn.includes('narration') || 
          lowerColumn.includes('particulars') || lowerColumn.includes('details')) {
        if (!detectedMappings['description']) {
          detectedMappings['description'] = column;
        }
      }
      
      // Amount column detection
      if (lowerColumn.includes('amount') && !lowerColumn.includes('balance')) {
        if (!detectedMappings['amount']) {
          detectedMappings['amount'] = column;
        }
      }
      
      // Balance column detection
      if (lowerColumn.includes('balance')) {
        if (!detectedMappings['balance']) {
          detectedMappings['balance'] = column;
        }
      }
      
      // Debit/Credit column detection
      if (lowerColumn.includes('debit') || lowerColumn.includes('withdrawal')) {
        if (!detectedMappings['debit']) {
          detectedMappings['debit'] = column;
        }
      }
      
      if (lowerColumn.includes('credit') || lowerColumn.includes('deposit')) {
        if (!detectedMappings['credit']) {
          detectedMappings['credit'] = column;
        }
      }
      
      // Category column detection
      if (lowerColumn.includes('category') || lowerColumn.includes('type')) {
        if (!detectedMappings['category']) {
          detectedMappings['category'] = column;
        }
      }
      
      // Reference column detection
      if (lowerColumn.includes('reference') || lowerColumn.includes('ref') || 
          lowerColumn.includes('number') || lowerColumn.includes('id')) {
        if (!detectedMappings['reference']) {
          detectedMappings['reference'] = column;
        }
      }
    });

    // Apply detected mappings to form
    Object.keys(detectedMappings).forEach(key => {
      if (this.mappingForm.get(key)) {
        this.mappingForm.get(key)?.setValue(detectedMappings[key]);
      }
    });
  }

  onSubmit(): void {
    if (this.mappingForm.valid) {
      const mapping: ColumnMapping = {
        fileId: this.file.id,
        mappings: this.mappingForm.value
      };
      this.mappingComplete.emit(mapping);
    }
  }

  onCancel(): void {
    this.cancel.emit();
  }

  getColumnOptions(): string[] {
    return ['', ...this.availableColumns];
  }

  isColumnMapped(column: string): boolean {
    return Object.values(this.mappingForm.value).includes(column);
  }

  getFormError(controlName: string): string | null {
    const control = this.mappingForm.get(controlName);
    if (control?.errors && control.touched) {
      if (control.errors['required']) {
        return `${this.getColumnLabel(controlName)} is required`;
      }
    }
    return null;
  }

  private getColumnLabel(key: string): string {
    const column = [...this.requiredColumns, ...this.optionalColumns]
      .find(col => col.key === key);
    return column?.label || key;
  }
}
