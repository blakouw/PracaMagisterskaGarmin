import { provideHttpClient } from '@angular/common/http';
import { bootstrapApplication } from '@angular/platform-browser';
import { CategoryScale, Legend, LineController, LineElement, LinearScale, PointElement, Tooltip } from 'chart.js';
import { provideCharts } from 'ng2-charts';
import { AppComponent } from './app';

void bootstrapApplication(AppComponent, {
  providers: [
    provideHttpClient(),
    provideCharts({ registerables: [CategoryScale, Legend, LineController, LineElement, LinearScale, PointElement, Tooltip] })
  ]
}).catch((error: unknown) => console.error(error));
