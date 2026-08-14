/**
 * Zustand global store — Phase 2 expanded.
 *
 * Slices:
 * - Auth (currentUser, isAuthLoading)
 * - WebSocket status
 * - UI (activeConversationId)
 *
 * Phase 3 will add conversations, messages, and typing slices.
 */

import { create } from "zustand";
import type { User } from "@/types";

interface AppState {
  // ── Auth ──────────────────────────────────────────────────
  currentUser: User | null;
  isAuthLoading: boolean;
  setCurrentUser: (user: User | null) => void;
  setAuthLoading: (loading: boolean) => void;

  // ── WebSocket status ──────────────────────────────────────
  wsConnected: boolean;
  setWsConnected: (connected: boolean) => void;

  // ── Global UI ─────────────────────────────────────────────
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;
}

const useStore = create<AppState>((set) => ({
  // Auth
  currentUser: null,
  isAuthLoading: true,
  setCurrentUser: (user) => set({ currentUser: user }),
  setAuthLoading: (loading) => set({ isAuthLoading: loading }),

  // WebSocket
  wsConnected: false,
  setWsConnected: (connected) => set({ wsConnected: connected }),

  // UI
  activeConversationId: null,
  setActiveConversationId: (id) => set({ activeConversationId: id }),
}));

export default useStore;
