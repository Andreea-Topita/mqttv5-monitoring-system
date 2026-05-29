import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs';

import {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  UserResponse
} from '../models/auth.models';

import { TokenStorageService } from './token-storage.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private baseUrl = 'http://127.0.0.1:8000/api/auth';

  constructor(
    private http: HttpClient,
    private tokenStorage: TokenStorageService
  ) {}

  register(payload: RegisterRequest) {
    return this.http.post<AuthResponse>(`${this.baseUrl}/register`, payload)
      .pipe(
        tap((res) => {
          this.tokenStorage.saveToken(res.access_token);
        })
      );
  }

  login(payload: LoginRequest) {
    return this.http.post<AuthResponse>(`${this.baseUrl}/login`, payload)
      .pipe(
        tap((res) => {
          this.tokenStorage.saveToken(res.access_token);
        })
      );
  }

  me() {
    return this.http.get<UserResponse>(`${this.baseUrl}/me`);
  }

  logout(): void {
    this.tokenStorage.clearToken();
  }

  isLoggedIn(): boolean {
    return this.tokenStorage.hasToken();
  }
}