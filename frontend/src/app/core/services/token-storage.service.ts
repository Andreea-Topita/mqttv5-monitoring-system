import { Injectable } from '@angular/core';

const TOKEN_KEY = 'mqtt_monitor_access_token';

@Injectable({
  providedIn: 'root'
})
export class TokenStorageService {
  saveToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  clearToken(): void {
    localStorage.removeItem(TOKEN_KEY);
  }

  hasToken(): boolean {
    return this.getToken() !== null;
  }
}