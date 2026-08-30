import { api } from './api';
import { ENDPOINTS, STORAGE_KEYS } from '../utils/constants';
import type {
  LoginCredentials,
  RegisterCredentials,
  AuthTokens,
  User,
} from '../types';

// Storage helpers
function saveTokens(tokens: AuthTokens): void {
  try {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);
    localStorage.setItem(STORAGE_KEYS.ACCESS_EXPIRES_AT, String(tokens.access_expires_at || Date.now() + 3600000));
    localStorage.setItem(STORAGE_KEYS.REFRESH_EXPIRES_AT, String(tokens.refresh_expires_at || Date.now() + 86400000));
  } catch (e) {
    console.error('Failed to save tokens to localStorage', e);
  }
}

function clearTokens(): void {
  try {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.ACCESS_EXPIRES_AT);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_EXPIRES_AT);
  } catch (e) {
    console.error('Failed to clear tokens from localStorage', e);
  }
}

function getUser(): User | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEYS.USER);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

export function saveUser(user: User): void {
  try {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
  } catch (e) {
    console.error('Failed to save user to localStorage', e);
  }
}

export function clearUser(): void {
  try {
    localStorage.removeItem(STORAGE_KEYS.USER);
  } catch (e) {
    console.error('Failed to clear user from localStorage', e);
  }
}

// Check if user is authenticated
export function isAuthenticated(): boolean {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  const expiresAt = localStorage.getItem(STORAGE_KEYS.ACCESS_EXPIRES_AT);
  if (!token || !expiresAt) return false;
  return Date.now() < Number(expiresAt);
}

// Check if token needs refresh
export function isTokenExpired(): boolean {
  const expiresAt = localStorage.getItem(STORAGE_KEYS.ACCESS_EXPIRES_AT);
  if (!expiresAt) return true;
  return Date.now() >= Number(expiresAt) - 60000; // Buffer of 1 minute
}

// Login
export async function login(credentials: LoginCredentials): Promise<{ user: User; tokens: AuthTokens }> {
  const result = await api.post<AuthTokens & { user_id: string; email: string }>(ENDPOINTS.AUTH.LOGIN, credentials);
  const tokens: AuthTokens = {
    access_token: result.access_token,
    refresh_token: result.refresh_token,
    access_expires_at: Date.now() + 3600000,
    refresh_expires_at: Date.now() + 86400000,
  };

  if (!tokens.access_token) throw new Error('No tokens received from server');

  saveTokens(tokens);

  return { user: { id: result.user_id, email: result.email } as User, tokens };
}

// Register
export async function register(credentials: RegisterCredentials): Promise<{ user: User; tokens: AuthTokens }> {
  const result = await api.post<AuthTokens & { user_id: string; id: string; email: string }>(ENDPOINTS.AUTH.REGISTER, credentials);
  const tokens: AuthTokens = {
    access_token: result.access_token,
    refresh_token: result.refresh_token,
    access_expires_at: Date.now() + 3600000,
    refresh_expires_at: Date.now() + 86400000,
  };

  if (!tokens.access_token) throw new Error('No tokens received from server');

  saveTokens(tokens);

  return { user: { id: result.user_id || result.id, email: result.email } as User, tokens };
}

// Logout
export function logout(): void {
  try {
    api.post(ENDPOINTS.AUTH.LOGOUT, {}).catch(() => {
      // Ignore errors during logout
    });
  } finally {
    clearTokens();
    clearUser();
  }
}

// Get current user
export function getCurrentUser(): User | null {
  return getUser();
}

// Update current user profile
export async function updateProfile(profileData: Partial<User>): Promise<User> {
  const user = await api.put<User>(ENDPOINTS.AUTH.PROFILE, profileData);
  saveUser(user);
  return user;
}

// Refresh token
export async function refreshAuthToken(): Promise<boolean> {
  const refreshTokenValue = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  if (!refreshTokenValue) return false;

  try {
    const result = await api.post<AuthTokens>(ENDPOINTS.AUTH.REFRESH, {
      refresh_token: refreshTokenValue,
    });
    const tokens: AuthTokens = {
      access_token: result.access_token,
      refresh_token: result.refresh_token,
      access_expires_at: Date.now() + 3600000,
      refresh_expires_at: Date.now() + 86400000,
    };
    if (!tokens.access_token) throw new Error('No tokens received from server');
    saveTokens(tokens);
    return true;
  } catch {
    logout();
    return false;
  }
}

// Forgot password
export async function forgotPassword(email: string): Promise<void> {
  await api.post(ENDPOINTS.AUTH.FORGOT_PASSWORD || '/auth/forgot-password', { email });
}

// Change password
export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await api.put(`${ENDPOINTS.AUTH.PROFILE}/password`, {
    current_password: currentPassword,
    new_password: newPassword,
  });
}
