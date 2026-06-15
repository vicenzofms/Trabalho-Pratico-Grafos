import { ApplicationConfig, importProvidersFrom, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { routes } from './app.routes';
import { LucideAngularModule, Sun, Moon, Download, RefreshCw, AlertCircle, Info, X, Loader2, ArrowUp, Trash2, Network } from 'lucide-angular';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withFetch()),
    importProvidersFrom(LucideAngularModule.pick({ Sun, Moon, Download, RefreshCw, AlertCircle, Info, X, Loader2, ArrowUp, Trash2, Network })),
  ],
};
