export interface UserResponse {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  success: boolean;
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  identifier: string;
  password: string;
}