// frontend/utils/Client.js
import axios from "axios";

// Use env var if provided, otherwise default to the nginx proxy prefix
const API_BASE = import.meta.env?.VITE_API_BASE || "/api";

const client = axios.create({
  baseURL: API_BASE,
  withCredentials: false,
});

export default client;
