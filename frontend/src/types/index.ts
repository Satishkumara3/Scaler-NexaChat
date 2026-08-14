/**
 * Shared TypeScript interfaces for the entire frontend.
 * This is the single source of truth for data shapes.
 * Updated each phase as new models are introduced.
 */

// ─────────────────────────────────────────────────────────────
// Auth
// ─────────────────────────────────────────────────────────────
export interface User {
  id: string;
  phone: string;
  display_name: string;
  avatar_url?: string;
  about: string;
  created_at: string;
  last_seen: string | null;
}

export interface Session {
  id: string;
  user_id: string;
  expires_at: string;
  created_at: string;
  last_used_at: string | null;
}

export interface Contact {
  id?: string;
  user_id?: string;
  contact_user_id: string;
  nickname?: string;
  created_at: string;
  user?: User; // Joined related info
}

// ─────────────────────────────────────────────────────────────
// Conversations
// ─────────────────────────────────────────────────────────────
export interface Conversation {
  id: string;
  type: "DIRECT" | "GROUP";
  created_at: string;
  updated_at: string;
  other_user?: Partial<User>;
  last_message?: Message | null;
  unread_count?: number;
  members?: GroupMember[];
  name?: string;
  avatar_url?: string;
  created_by?: string;
}

export interface ConversationMember {
  user_id: string;
  conversation_id: string;
  role: "admin" | "member";
  joined_at: string;
  user?: User;
}

export type GroupMember = User & ConversationMember;

// ─────────────────────────────────────────────────────────────
// Messages
// ─────────────────────────────────────────────────────────────
export type MessageType = "TEXT" | "IMAGE" | "VIDEO" | "FILE";
export type MessageStatus = "SENT" | "DELIVERED" | "READ";

export interface Attachment {
  id: string;
  message_id: string;
  original_filename: string;
  stored_filename: string;
  mime_type: string;
  file_size: number;
  url: string;
}

export interface Reaction {
  id: string;
  message_id: string;
  user_id: string;
  emoji: string;
  created_at: string;
}

export interface ReplyPreview {
  id: string;
  sender_id: string;
  sender_name: string;
  content: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  message_type: MessageType;
  status: MessageStatus;
  created_at: string;
  updated_at: string;
  sender?: User;
  attachment?: Attachment;
  reply_to_message_id?: string | null;
  reply_preview?: ReplyPreview | null;
  reactions?: Reaction[];
}

export interface MessageStatusUpdate {
  message_id: string;
  user_id: string;
  status: Omit<MessageStatus, "sending">;
  updated_at: string;
}

// ─────────────────────────────────────────────────────────────
// WebSocket events
// ─────────────────────────────────────────────────────────────
export type WSEventType =
  | "connected"
  | "echo"
  | "new_message"
  | "message_status"
  | "typing"
  | "member_added"
  | "member_removed"
  | "group_updated"
  | "user_online"
  | "user_offline"
  | "pong"
  | "error";

export interface WSEvent {
  type: WSEventType;
  [key: string]: unknown;
}

export interface TypingEvent extends WSEvent {
  type: "typing";
  conversation_id: string;
  user_id: string;
  is_typing: boolean;
}

export interface NewMessageEvent extends WSEvent {
  type: "new_message";
  message: Message;
}

export interface MessageStatusEvent extends WSEvent {
  type: "message_status";
  message_id: string;
  user_id: string;
  status: MessageStatus;
}

// ─────────────────────────────────────────────────────────────
// API response wrappers
// ─────────────────────────────────────────────────────────────
export interface ApiError {
  error: true;
  status_code: number;
  message: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
}
