import { Routes } from '@angular/router';

import { authGuard } from './core/guards/auth.guard';
import { ConnectComponent } from './pages/connect/connect.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';

import { LoginComponent } from './pages/auth/login/login.component';
import { RegisterComponent } from './pages/auth/register/register.component';
import { ChartsComponent } from './pages/charts/charts.component';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },

  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },

  { path: 'connect', component: ConnectComponent, canActivate: [authGuard] },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'charts', component: ChartsComponent, canActivate: [authGuard] },

  { path: '**', redirectTo: 'login' }
];