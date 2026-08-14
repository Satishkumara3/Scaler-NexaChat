/**
 * Miscellaneous utility functions.
 */

// ── Date / time ─────────────────────────────────────────────────────────────

/**
 * Format a timestamp for display in the conversation list.
 * Today → "HH:MM", Earlier this week → "Mon", Older → "DD/MM/YYYY"
 */
export function formatConversationTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();

  const isToday =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();

  if (isToday) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  const diffMs = now.getTime() - date.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);

  if (diffDays < 7) {
    return date.toLocaleDateString([], { weekday: "short" }); // "Mon"
  }

  return date.toLocaleDateString([], {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/**
 * Format a message timestamp: "HH:MM"
 */
export function formatMessageTime(isoString: string): string {
  return new Date(isoString).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ── Avatar helpers ───────────────────────────────────────────────────────────

/**
 * Return stable initials from a display name (up to 2 chars).
 */
export function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * Derive a deterministic HSL background colour from a string (user ID or name).
 * This gives each user a unique, consistent avatar colour.
 */
export function getAvatarColor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 50%, 35%)`;
}

// ── String helpers ───────────────────────────────────────────────────────────

/**
 * Truncate a string to maxLength, appending "…" if truncated.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 1) + "…";
}

/**
 * Generate a UUID v4 (used for optimistic message IDs client-side).
 */
export function uuid(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
