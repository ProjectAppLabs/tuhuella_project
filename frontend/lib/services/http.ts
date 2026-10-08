'use client';

import axios from 'axios';

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/lib/services/tokens';

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || '/api').replace(/\/$/, '');

export const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

const refreshAccessToken = async (): Promise<string | null> => {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  try {
    const response = await axios.post(`${API_BASE_URL}/token/refresh/`, { refresh });
    const access = response.data?.access;
    if (!access) return null;
    setTokens({ access, refresh });
    return access;
  } catch (error) {
    if ((error as { response?: { status?: number } })?.response?.status === 401) {
      clearTokens();
      return null;
    }
    throw error;
  }
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error?.config as (typeof error.config & { _retry?: boolean }) | undefined;
    const status = error?.response?.status;

    if (status !== 401 || !originalRequest || originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    refreshPromise = refreshPromise ?? refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
    const newAccess = await refreshPromise;

    if (!newAccess) {
      return Promise.reject(error);
    }

    originalRequest.headers = originalRequest.headers ?? {};
    originalRequest.headers.Authorization = `Bearer ${newAccess}`;
    return api(originalRequest);
  }
);
