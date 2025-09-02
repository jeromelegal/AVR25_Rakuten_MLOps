// frontend/src/services/axiosInstance.js
import axios from 'axios';
import { getAuthToken } from './authService';

const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_GATEWAY_BASE_URL,
});

axiosInstance.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default axiosInstance;
