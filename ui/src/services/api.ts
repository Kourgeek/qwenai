import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import { API_BASE_URL, STORAGE_KEYS } from '../utils/constants';
import type { ApiResponse, ApiError } from '../types';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Get token from localStorage
function getAccessToken(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  } catch {
    return null;
  }
}

// Refresh token logic
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

function processQueue(token: string | null): void {
  failedQueue.forEach((prom) => {
    if (token) {
      prom.resolve(token);
    } else {
      prom.reject(new AxiosError('Token refresh failed'));
    }
  });
  failedQueue = [];
}

async function refreshToken(): Promise<string | null> {
  try {
    const refreshTokenValue = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    if (!refreshTokenValue) return null;

    // BFF returns data directly (not wrapped in ApiResponse)
    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
      refresh_token: refreshTokenValue,
    });

    const data = response.data;
    if (data && data.access_token) {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
      return data.access_token;
    }
    return null;
  } catch {
    return null;
  }
}

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => response,
  async (error: AxiosError<ApiResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/login') &&
      !originalRequest.url?.includes('/auth/register')
    ) {
      if (isRefreshing) {
        try {
          const token = await new Promise<string | null>((resolve, reject) => {
            failedQueue.push({ resolve: resolve as any, reject: reject as any });
          });

          if (token) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          }
        } catch (refreshError) {
          // Clear auth on refresh failure
          localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
          localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
          localStorage.removeItem(STORAGE_KEYS.USER);
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await refreshToken();
        isRefreshing = false;
        processQueue(newToken);

        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return apiClient(originalRequest);
        }
      } catch {
        isRefreshing = false;
        processQueue(null);
        localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.USER);
        window.location.href = '/login';
      }

      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

// Generic request wrapper
// BFF returns data directly (not wrapped in ApiResponse)
async function request<T>(config: AxiosRequestConfig): Promise<T> {
  try {
    const response = await apiClient.request(config);
    // BFF returns data directly, not wrapped in ApiResponse
    return response.data as T;
  } catch (error) {
    const axiosError = error as AxiosError;

    if (axiosError.response) {
      const responseData = axiosError.response.data as Record<string, unknown> | undefined;
      const apiError: ApiError = {
        success: false,
        message: (responseData?.detail as string) || (responseData?.message as string) || 'An error occurred',
        error: (responseData?.detail as string) || axiosError.response.statusText,
        status: axiosError.response.status,
      };
      throw apiError;
    }

    if (axiosError.request) {
      throw {
        success: false,
        message: 'Network error. Please check your connection.',
        error: 'NETWORK_ERROR',
        status: 0,
      } as ApiError;
    }

    throw {
      success: false,
      message: axiosError.message || 'An unexpected error occurred',
      error: axiosError.message,
      status: 0,
    } as ApiError;
  }
}

// Helper methods
export const api = {
  get: <T = unknown>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'GET', url, params }),

  post: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'POST', url, data }),

  put: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'PUT', url, data }),

  patch: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'PATCH', url, data }),

  delete: <T = unknown>(url: string, config?: AxiosRequestConfig) =>
    request<T>({ ...config, method: 'DELETE', url }),
};

export default apiClient;
