/**
 * Axios API client — configured with the backend base URL.
 *
 * All frontend code should import from here instead of using axios directly:
 *   import api from "@/lib/api";
 *
 * Features:
 * - withCredentials: true  → sends HttpOnly session cookie automatically
 * - Request interceptor   → attaches content-type
 * - Response interceptor  → normalises error shape to ApiError
 */

import axios, { AxiosError } from "axios";
import type { ApiError } from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,          // send session cookies cross-origin
  headers: { "Content-Type": "application/json" },
  timeout: 10_000,
});

// ── Response interceptor ─────────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Normalise to a consistent error object
    const message =
      error.response?.data?.message ??
      error.message ??
      "An unexpected error occurred";

    const status = error.response?.status ?? 0;

    // Attach a clean error so callers can pattern-match
    return Promise.reject({ status, message, raw: error });
  }
);

export default api;

// ── Typed helper wrappers ────────────────────────────────────────────────────
// Using these keeps route code clean and avoids repeated .data extraction.

export async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const res = await api.get<T>(url, { params });
  return res.data;
}

export async function post<T>(url: string, data?: unknown): Promise<T> {
  const res = await api.post<T>(url, data);
  return res.data;
}

export async function put<T>(url: string, data?: unknown): Promise<T> {
  const res = await api.put<T>(url, data);
  return res.data;
}

export async function del<T>(url: string): Promise<T> {
  const res = await api.delete<T>(url);
  return res.data;
}
