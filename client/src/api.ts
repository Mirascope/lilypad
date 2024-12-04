import { UserPublic } from "@/types/types";
import { AUTH_STORAGE_KEY } from "@/utils/constants";
import axios from "axios";
let baseURL = "/api/v0";
if (import.meta.env.MODE === "development") {
  baseURL = `${import.meta.env.VITE_API_SERVER}/api/v0`;
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
    return Promise.reject(error);
  }
);
export default api;
