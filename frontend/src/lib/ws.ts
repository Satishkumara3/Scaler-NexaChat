/**
 * WebSocket client abstraction.
 *
 * Design:
 * - Singleton pattern — one connection per browser session
 * - Automatic reconnect with exponential back-off
 * - Event listener map so multiple hooks can subscribe without conflicts
 * - In Phase 1 the server authenticates with ?client_id=; Phase 3 upgrades to ?token=<jwt>
 *
 * Usage:
 *   const ws = WSClient.getInstance();
 *   ws.connect("test-user");
 *   ws.on("new_message", (event) => { ... });
 *   ws.send({ type: "ping" });
 */

import type { WSEvent, WSEventType } from "@/types";

type EventHandler = (event: WSEvent) => void;

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

const MAX_RECONNECT_DELAY_MS = 30_000;
const INITIAL_RECONNECT_DELAY_MS = 1_000;

class WSClient {
  private static instance: WSClient | null = null;

  private socket: WebSocket | null = null;
  private clientId: string | null = null;
  private listeners: Map<WSEventType | "all", Set<EventHandler>> = new Map();
  private reconnectDelay = INITIAL_RECONNECT_DELAY_MS;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = false;

  private constructor() {}

  static getInstance(): WSClient {
    if (!WSClient.instance) {
      WSClient.instance = new WSClient();
    }
    return WSClient.instance;
  }

  // ── Connection lifecycle ────────────────────────────────────────────────────

  connect(clientId: string): void {
    this.clientId = clientId;
    this.shouldReconnect = true;
    this.openSocket();
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    this.socket?.close(1000, "Client disconnected");
    this.socket = null;
  }

  get isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  // ── Sending ─────────────────────────────────────────────────────────────────

  send(payload: object): void {
    if (!this.isConnected) {
      console.warn("[WS] Cannot send — socket not open");
      return;
    }
    this.socket!.send(JSON.stringify(payload));
  }

  // ── Event subscription ──────────────────────────────────────────────────────

  on(eventType: WSEventType | "all", handler: EventHandler): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(handler);

    // Return an unsubscribe function for easy cleanup in useEffect
    return () => this.off(eventType, handler);
  }

  off(eventType: WSEventType | "all", handler: EventHandler): void {
    this.listeners.get(eventType)?.delete(handler);
  }

  // ── Internals ───────────────────────────────────────────────────────────────

  private openSocket(): void {
    if (!this.clientId) return;

    // Phase 1: identify by client_id query param
    // Phase 3: upgrade to ?token=<jwt>
    const url = `${WS_BASE_URL}/ws?client_id=${encodeURIComponent(this.clientId)}`;

    console.log(`[WS] Connecting to ${url}`);
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log("[WS] Connected ✅");
      this.reconnectDelay = INITIAL_RECONNECT_DELAY_MS;
      this.dispatch({ type: "connected", message: "Connected" } as WSEvent);
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSEvent;
        this.dispatch(data);
      } catch {
        console.error("[WS] Failed to parse message:", event.data);
      }
    };

    this.socket.onerror = (err) => {
      console.error("[WS] Error:", err);
    };

    this.socket.onclose = (event) => {
      console.log(`[WS] Closed (code=${event.code})`);
      if (this.shouldReconnect && event.code !== 1000) {
        this.scheduleReconnect();
      }
    };
  }

  private scheduleReconnect(): void {
    console.log(`[WS] Reconnecting in ${this.reconnectDelay}ms …`);
    this.reconnectTimer = setTimeout(() => {
      this.openSocket();
    }, this.reconnectDelay);

    // Exponential back-off, capped at MAX_RECONNECT_DELAY_MS
    this.reconnectDelay = Math.min(
      this.reconnectDelay * 2,
      MAX_RECONNECT_DELAY_MS
    );
  }

  private dispatch(event: WSEvent): void {
    // Fire type-specific listeners
    this.listeners.get(event.type)?.forEach((h) => h(event));
    // Fire catch-all listeners
    this.listeners.get("all")?.forEach((h) => h(event));
  }
}

export default WSClient;
