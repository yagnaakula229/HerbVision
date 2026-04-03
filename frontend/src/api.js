import axios from "axios";

// Dynamically determine backend URL based on how frontend is accessed
const getBackendURL = () => {
  const hostname = window.location.hostname;
  // If accessed on localhost, use localhost; otherwise use the same hostname for backend
  return `http://${hostname}:5000`;
};

const BASE_URL = getBackendURL();

console.log("Backend URL:", BASE_URL);

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000, // 15 second timeout
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  console.log("API Request:", config.method.toUpperCase(), config.url);
  return config;
});

api.interceptors.response.use(
  (response) => {
    console.log("API Response:", response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error("API Error:", error.message, error.config?.url);
    return Promise.reject(error);
  }
);

export default api;
export { BASE_URL };
