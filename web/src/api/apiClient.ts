import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// Types for API responses
export interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
  headers: any;
}

export interface ApiError {
  message: string;
  status?: number;
  errors?: any;
}

// Environment-based API URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

/**
 * Creates and configures an Axios instance for API calls
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: `${API_URL}${API_PREFIX}`,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    timeout: 30000, // 30 seconds
  });

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  client.interceptors.response.use(
    (response) => {
      return response;
    },
    (error: AxiosError) => {
      // Handle specific error cases
      const errorResponse: ApiError = {
        message: 'An unexpected error occurred',
      };

      if (error.response) {
        // Server responded with an error status
        errorResponse.status = error.response.status;
        errorResponse.message = error.response.data?.message || `Error: ${error.response.status}`;
        errorResponse.errors = error.response.data?.errors;

        // Handle specific status codes
        switch (error.response.status) {
          case 401:
            // Unauthorized - clear auth and redirect to login
            localStorage.removeItem('auth_token');
            // Could dispatch an auth logout action here if using Redux
            break;
          case 403:
            // Forbidden
            errorResponse.message = 'You do not have permission to access this resource';
            break;
          case 404:
            // Not found
            errorResponse.message = 'The requested resource was not found';
            break;
          case 500:
            // Server error
            errorResponse.message = 'An internal server error occurred';
            break;
        }
      } else if (error.request) {
        // Request was made but no response received
        errorResponse.message = 'No response received from server. Please check your connection.';
      }

      console.error('API Error:', errorResponse);
      return Promise.reject(errorResponse);
    }
  );

  return client;
};

// Create the API client instance
const apiClient = createApiClient();

// Helper methods
export const api = {
  /**
   * Make a GET request
   */
  get: async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response: AxiosResponse<T> = await apiClient.get(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Make a POST request
   */
  post: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response: AxiosResponse<T> = await apiClient.post(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Make a PUT request
   */
  put: async <T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response: AxiosResponse<T> = await apiClient.put(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Make a DELETE request
   */
  delete: async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response: AxiosResponse<T> = await apiClient.delete(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};

// Export the raw client for advanced use cases
export default apiClient;
