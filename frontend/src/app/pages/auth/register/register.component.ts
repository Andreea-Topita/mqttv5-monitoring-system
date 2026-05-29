import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.component.html',
  styleUrl: './register.component.css'
})
export class RegisterComponent {
  username = '';
  email = '';
  password = '';
  confirmPassword = '';

  loading = false;
  errorMessage = '';

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  register(): void {
    this.errorMessage = '';

    if (!this.username.trim() || !this.email.trim() || !this.password || !this.confirmPassword) {
      this.errorMessage = 'Please complete all fields.';
      return;
    }

    if (this.username.trim().length < 3) {
      this.errorMessage = 'Username must have at least 3 characters.';
      return;
    }

    if (this.password.length < 6) {
      this.errorMessage = 'Password must have at least 6 characters.';
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.errorMessage = 'Passwords do not match.';
      return;
    }

    this.loading = true;

    this.authService.register({
      username: this.username.trim(),
      email: this.email.trim(),
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
          'Account creation failed.';
      }
    });
  }
}