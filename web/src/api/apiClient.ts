import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

const apiClient = axios.create({
  baseURL: `${API_URL}${API_PREFIX}`,
  headers: {
    "Content-Type": "application/json",
    "Accept": "application/json",
  },
  timeout: 30000,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const errorResponse = {
      message: "An unexpected error occurred",
    };

    if (error.response) {
      // Server responded with error
      errorResponse.status = error.response.status;
      errorResponse.message = error.response.data?.message || `Error: ${error.response.status}`;
    } else if (error.request) {
      // No response received
      errorResponse.message = "No response received from server. Please check your connection.";
    }

    console.error("API Error:", errorResponse);
    return Promise.reject(errorResponse);
  }
);

// Helper methods
export const api = {
  get: async (url, config) => {
    try {
      const response = await apiClient.get(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  post: async (url, data, config) => {
    try {
      const response = await apiClient.post(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  put: async (url, data, config) => {
    try {
      const response = await apiClient.put(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  delete: async (url, config) => {
    try {
      const response = await apiClient.delete(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
};

export default apiClient;
