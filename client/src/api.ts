import axios from "axios";
let baseURL = "/api/v0";
if (import.meta.env.MODE === "development") {
  baseURL = "http://localhost:8000/api/v0";
}
const api = axios.create({
  baseURL,
});

export default api;
