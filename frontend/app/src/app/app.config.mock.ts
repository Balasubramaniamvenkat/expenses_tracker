import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';
import { UploadService as MockUploadService } from './modules/upload/services/upload.service.mock'; // Import the mock service
import { UploadService } from './modules/upload/services/upload.service'; // Import the real service interface

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: false }),
    provideRouter(routes),
    provideAnimations(),
    provideHttpClient(withInterceptorsFromDi()),
    { provide: UploadService, useClass: MockUploadService } // Using the mock service
  ]
};
