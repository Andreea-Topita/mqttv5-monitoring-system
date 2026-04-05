import { Routes } from '@angular/router';
import { ConnectComponent } from './pages/connect/connect.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';

export const routes: Routes = [
  { path: '', redirectTo: 'connect', pathMatch: 'full' },
  { path: 'connect', component: ConnectComponent },
  { path: 'dashboard', component: DashboardComponent }
];