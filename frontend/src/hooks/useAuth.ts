/**
 * useAuth hook — Phase 2 real implementation.
 *
 * Provides:
 * - currentUser, isAuthLoading, isAuthenticated
 * - requestOtp, register, login, logout
 * - restoreSession (called on app mount to check /me)
 */

"use client";

import { useCallback } from "react";
import useStore from "@/store/useStore";
import { post, get } from "@/lib/api";
import type { User } from "@/types";

interface OtpRequestResponse {
  message: string;
}

interface AuthResponse {
  user: User;
  message: string;
}

interface MeResponse {
  user: User;
}

export function useAuth() {
  const currentUser = useStore((s) => s.currentUser);
  const isAuthLoading = useStore((s) => s.isAuthLoading);
  const setCurrentUser = useStore((s) => s.setCurrentUser);
  const setAuthLoading = useStore((s) => s.setAuthLoading);

  /** Call once on app mount to hydrate session from HttpOnly cookie. */
  const restoreSession = useCallback(async () => {
    setAuthLoading(true);
    try {
      const data = await get<MeResponse>("/api/auth/me");
      setCurrentUser(data.user);
    } catch {
      setCurrentUser(null);
    } finally {
      setAuthLoading(false);
    }
  }, [setCurrentUser, setAuthLoading]);

  /** Request OTP for registration */
  const requestRegisterOtp = useCallback(async (phone: string) => {
    await post<OtpRequestResponse>("/api/auth/register/request-otp", { phone });
  }, []);

  /** Verify OTP and complete registration */
  const register = useCallback(
    async (phone: string, otpCode: string, displayName: string): Promise<User> => {
      const data = await post<AuthResponse>("/api/auth/register/verify", {
        phone,
        otp_code: otpCode,
        display_name: displayName,
      });
      setCurrentUser(data.user);
      return data.user;
    },
    [setCurrentUser]
  );

  /** Request OTP for login */
  const requestLoginOtp = useCallback(async (phone: string) => {
    await post<OtpRequestResponse>("/api/auth/login/request-otp", { phone });
  }, []);

  /** Verify OTP and complete login */
  const login = useCallback(
    async (phone: string, otpCode: string): Promise<User> => {
      const data = await post<AuthResponse>("/api/auth/login/verify", {
        phone,
        otp_code: otpCode,
      });
      setCurrentUser(data.user);
      return data.user;
    },
    [setCurrentUser]
  );

  /** Logout — clears cookie server-side and resets store */
  const logout = useCallback(async () => {
    try {
      await post("/api/auth/logout");
    } finally {
      setCurrentUser(null);
    }
  }, [setCurrentUser]);

  /** Update display name / about */
  const updateProfile = useCallback(
    async (updates: { display_name?: string; about?: string }): Promise<User> => {
      const { put } = await import("@/lib/api");
      const data = await put<{ user: User }>("/api/auth/me", updates);
      setCurrentUser(data.user);
      return data.user;
    },
    [setCurrentUser]
  );

  return {
    currentUser,
    isAuthLoading,
    isAuthenticated: !!currentUser,
    restoreSession,
    requestRegisterOtp,
    register,
    requestLoginOtp,
    login,
    logout,
    updateProfile,
    setCurrentUser,
    setAuthLoading,
  };
}
