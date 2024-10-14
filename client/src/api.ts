import axios from "axios";
let baseURL = "/api";
if (import.meta.env.MODE === "development") {
  baseURL = "http://localhost:8000/api";
}
const api = axios.create({
  baseURL,
});

export default api;
