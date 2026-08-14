/**
 * Auth provider — mounts at the app level.
 * Calls restoreSession on mount so the authenticated state
 * is hydrated from the HttpOnly cookie after a page refresh.
 */

"use client";

import { useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { restoreSession } = useAuth();

  useEffect(() => {
    restoreSession();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return <>{children}</>;
}
