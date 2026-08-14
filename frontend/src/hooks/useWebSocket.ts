/**
 * useWebSocket hook — Phase 1 scaffold.
 *
 * Manages the WSClient singleton lifecycle within React.
 * Subscribes to WS events and updates the Zustand store.
 *
 * Phase 3 will:
 * - Replace client_id with JWT token
 * - Wire new_message, typing, and message_status events into the store
 */

"use client";

import { useEffect, useCallback } from "react";
import WSClient from "@/lib/ws";
import useStore from "@/store/useStore";
import type { WSEvent } from "@/types";

interface UseWebSocketOptions {
  /** Phase 1: any string identifier. Phase 3: the authenticated user's ID */
  clientId: string;
  enabled?: boolean;
}

export function useWebSocket({ clientId, enabled = true }: UseWebSocketOptions) {
  const setWsConnected = useStore((s) => s.setWsConnected);
  const ws = WSClient.getInstance();

  useEffect(() => {
    if (!enabled || !clientId) return;

    ws.connect(clientId);

    // Track connection state
    const unsubConnect = ws.on("connected", () => setWsConnected(true));

    // Catch-all logger during development
    const unsubAll = ws.on("all", (event: WSEvent) => {
      if (process.env.NODE_ENV === "development") {
        console.log("[WS event]", event);
      }
    });

    return () => {
      unsubConnect();
      unsubAll();
      ws.disconnect();
      setWsConnected(false);
    };
  }, [clientId, enabled]); // eslint-disable-line react-hooks/exhaustive-deps

  const send = useCallback(
    (payload: object) => ws.send(payload),
    [] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return { isConnected: ws.isConnected, send };
}
