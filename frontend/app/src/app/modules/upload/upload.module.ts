import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

// Angular Material modules
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDividerModule } from '@angular/material/divider';
import { MatListModule } from '@angular/material/list';
import { MatTooltipModule } from '@angular/material/tooltip';

// Third-party modules
import { NgxFileDropModule } from 'ngx-file-drop';

// Routing
import { UploadRoutingModule } from './upload-routing.module';

// Components
import { FileUploadComponent } from './components/file-upload/file-upload.component';
import { ProcessingStatusComponent } from './components/processing-status/processing-status.component';
import { AccountSummaryComponent } from './components/account-summary/account-summary.component';
// import { ColumnMappingComponent } from './components/column-mapping/column-mapping.component';

// Services
// import { UploadService } from './services/upload.service';

@NgModule({  declarations: [
    FileUploadComponent,
    ProcessingStatusComponent,
    AccountSummaryComponent
    // ColumnMappingComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    UploadRoutingModule,
    
    // Angular Material
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatExpansionModule,
    MatChipsModule,
    MatSelectModule,
    MatFormFieldModule,
    MatInputModule,
    MatSnackBarModule,
    MatDividerModule,
    MatListModule,
    MatTooltipModule,
    
    // Third-party
    NgxFileDropModule
  ],  providers: [
    // UploadService
  ]
})
export class UploadModule { }
