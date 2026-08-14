/**
 * Toast notification system — Phase 1 scaffold.
 *
 * Simple in-memory toast queue rendered at the app level.
 * Phase 5 will wire this into the WS event stream for real-time notifications.
 */

"use client";

import { useState, useCallback, useEffect } from "react";

export type ToastType = "success" | "error" | "info" | "warning";

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

// ── Toast hook ────────────────────────────────────────────────────────────────

let _addToast: ((toast: Omit<Toast, "id">) => void) | null = null;

/** Call this anywhere to show a toast (singleton, wired by <ToastContainer>) */
export function showToast(message: string, type: ToastType = "info") {
  _addToast?.({ message, type });
}

// ── Toast container component ──────────────────────────────────────────────────

const COLORS: Record<ToastType, string> = {
  success: "#00a884",
  error:   "#ef4444",
  info:    "#3b82f6",
  warning: "#f59e0b",
};

export default function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const add = useCallback((toast: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { ...toast, id }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  useEffect(() => {
    _addToast = add;
    return () => { _addToast = null; };
  }, [add]);

  if (toasts.length === 0) return null;

  return (
    <div
      role="region"
      aria-live="polite"
      style={{
        position: "fixed",
        bottom: 24,
        right: 24,
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="animate-fade-in"
          style={{
            padding: "12px 16px",
            borderRadius: 8,
            background: COLORS[toast.type],
            color: "#fff",
            fontSize: 14,
            fontWeight: 500,
            boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
            maxWidth: 360,
          }}
        >
          {toast.message}
        </div>
      ))}
    </div>
  );
}
