import axios from "axios";

const api = axios.create({
  // baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api", // ALL APIs start with /api
  baseURL: import.meta.env.VITE_API_BASE_URL || "https://obe-assess-fyp.onrender.com/api", // ALL APIs start with /api
});

// Automatically attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
