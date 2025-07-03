import { loadEnvironmentFromStorage } from "@/src/auth";
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
    // Handle authentication
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    const environmentUuid = loadEnvironmentFromStorage()?.uuid;
    if (stored) {
      try {
        const session = JSON.parse(stored) as UserPublic;
        const token = session.access_token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch {
        localStorage.removeItem(AUTH_STORAGE_KEY);
      }
    }
    // Handle environment UUID injection for project-scoped endpoints
    if (environmentUuid && config.url?.includes("/projects/")) {
      // Parse existing URL and params
      const url = new URL(config.url, config.baseURL ?? baseURL);

      // Add environment_uuid if not already present
      if (!url.searchParams.has("environment_uuid")) {
        url.searchParams.append("environment_uuid", environmentUuid);
      }
      // Update the config URL (relative to baseURL)
      config.url = url.pathname + url.search;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error instanceof Error ? error : new Error(String(error)));
  }
);
export default api;
