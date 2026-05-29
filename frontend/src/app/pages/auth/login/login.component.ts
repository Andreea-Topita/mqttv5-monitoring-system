import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  identifier = '';
  password = '';

  loading = false;
  errorMessage = '';

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  login(): void {
    this.errorMessage = '';

    if (!this.identifier.trim() || !this.password) {
      this.errorMessage = 'Please enter your username/email and password.';
      return;
    }

    this.loading = true;

    this.authService.login({
      identifier: this.identifier.trim(),
      password: this.password
    }).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/connect']);
      },
      error: (err) => {
        this.loading = false;

        if (err?.status === 0) {
          this.errorMessage = 'The backend is not responding. Check if the API is running on port 8000.';
          return;
        }

        this.errorMessage =
          err?.error?.error?.message ||
          err?.error?.detail ||
          'Login failed. Please check your credentials.';
      }
    });
  }
}