import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "https://obe-assess-fyp.onrender.com/api",
});

// Automatically attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (import.meta.env.DEV) {
    console.debug("[API request]", `${config.baseURL}${config.url}`, config.method?.toUpperCase());
  }
  return config;
});

if (import.meta.env.DEV) {
  api.interceptors.response.use(
    (response) => {
      console.debug("[API response]", response.status, response.config.url);
      return response;
    },
    (error) => {
      console.debug(
        "[API error]",
        error.response?.status ?? "NO_RESPONSE",
        error.config?.url
      );
      return Promise.reject(error);
    }
  );
}

export default api;
