import { UserPublic } from "@/src/types/types";
import { AUTH_STORAGE_KEY } from "@/src/utils/constants";
import axios from "axios";
export let baseURL = "/v0";
if (import.meta.env.MODE === "development") {
  baseURL = "http://localhost:8000/v0";
}
if (import.meta.env.MODE === "production") {
  baseURL = import.meta.env.VITE_REMOTE_API_URL as string;
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
      const session = JSON.parse(stored) as UserPublic;
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
    return Promise.reject(error instanceof Error ? error : new Error(String(error)));
  }
);
export default api;
