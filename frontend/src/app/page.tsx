/**
 * Root page — redirects based on auth state.
 *
 * - If isAuthLoading → show spinner
 * - If authenticated → redirect to /app
 * - Otherwise → redirect to /login
 */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function RootPage() {
  const { isAuthLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthLoading) return;
    if (isAuthenticated) {
      router.replace("/app");
    } else {
      router.replace("/login");
    }
  }, [isAuthLoading, isAuthenticated, router]);

  return (
    <main
      className="flex h-full items-center justify-center"
      style={{ backgroundColor: "var(--bg-primary)" }}
    >
      <div className="flex flex-col items-center gap-4 animate-fade-in">
        <div
          className="rounded-full flex items-center justify-center"
          style={{ width: 64, height: 64, background: "var(--accent)" }}
        >
          <svg
            width="34"
            height="34"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </div>
        {/* Three-dot loading indicator */}
        <div className="flex gap-1.5">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    </main>
  );
}
