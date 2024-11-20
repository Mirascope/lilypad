import { UserSession } from "@/types/types";
import axios from "axios";
const AUTH_STORAGE_KEY = "auth-session";
let baseURL = "/api/v0";
if (import.meta.env.MODE === "development") {
  baseURL = "http://localhost:8000/api/v0";
}
const api = axios.create({
  baseURL,
  withCredentials: true,
});

api.interceptors.request.use(
  (config) => {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!stored) return config;

    try {
      const session = JSON.parse(stored) as UserSession;
      const token = session.access_token;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    } catch {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      return config;
    }
  },
  (error) => {
    return Promise.reject(error);
  }
);
export default api;
