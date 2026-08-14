"use client";
import React, { useState } from "react";
import { Message } from "@/types";

const ALLOWED_EMOJIS = ["❤️", "👍", "😂", "😮", "😢"] as const;

interface MessageBubbleProps {
  message: Message;
  isOwn: boolean;
  senderName?: string;
  currentUserId?: string;
  onReply?: (message: Message) => void;
  onToggleReaction?: (messageId: string, emoji: string) => void;
}

export function MessageBubble({
  message, isOwn, senderName, currentUserId, onReply, onToggleReaction,
}: MessageBubbleProps) {
  const [showReactionPicker, setShowReactionPicker] = useState(false);

  let timeStr = "";
  try {
    timeStr = new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {}

  // Group reactions by emoji: emoji → count + whether current user reacted
  const reactionMap: Record<string, { count: number; isMine: boolean }> = {};
  for (const r of message.reactions || []) {
    if (!reactionMap[r.emoji]) reactionMap[r.emoji] = { count: 0, isMine: false };
    reactionMap[r.emoji].count++;
    if (r.user_id === currentUserId) reactionMap[r.emoji].isMine = true;
  }
  const reactionEntries = Object.entries(reactionMap);

  return (
    <div
      className={`flex w-full mb-1 ${isOwn ? "justify-end" : "justify-start"} group relative`}
      onMouseLeave={() => setShowReactionPicker(false)}
    >
      <div
        className="max-w-[75%] px-3 py-1.5 rounded-[12px] relative"
        style={{
          backgroundColor: isOwn ? "var(--bg-bubble-me)" : "var(--bg-bubble-other)",
          color: "var(--text-primary)",
          borderBottomRightRadius: isOwn ? "4px" : "12px",
          borderBottomLeftRadius: isOwn ? "12px" : "4px",
        }}
      >
        {/* Reply preview strip */}
        {message.reply_preview && (
          <div
            className="flex flex-col mb-1.5 px-2 py-1.5 rounded-lg text-xs"
            style={{
              borderLeft: "3px solid var(--accent)",
              backgroundColor: "rgba(0,0,0,0.15)",
            }}
          >
            <span className="font-semibold opacity-80" style={{ color: "var(--accent)" }}>
              {message.reply_preview.sender_name}
            </span>
            <span className="opacity-70 truncate">{message.reply_preview.content}</span>
          </div>
        )}

        <div className="text-[15px] leading-relaxed break-words whitespace-pre-wrap flex flex-col">
          {senderName && (
            <span className="text-[11px] font-bold opacity-70 mb-0.5" style={{ color: "var(--bg-primary)" }}>
              {senderName}
            </span>
          )}

          {/* Image attachment */}
          {message.attachment && message.message_type === "IMAGE" && (
            <img
              src={`http://localhost:8000${message.attachment.url}`}
              alt="attachment"
              className="max-w-full rounded-lg mb-2 mt-1 object-contain max-h-[300px]"
            />
          )}

          {/* File attachment */}
          {message.attachment && message.message_type === "FILE" && (
            <div className="flex items-center gap-3 p-3 bg-black/10 rounded-lg mb-2 mt-1">
              <div className="p-2 bg-black/20 rounded">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
              </div>
              <div className="flex flex-col min-w-0">
                <span className="font-medium text-sm truncate">{message.attachment.original_filename}</span>
                <span className="text-xs opacity-70">{(message.attachment.file_size / 1024).toFixed(1)} KB</span>
              </div>
              <a
                href={`http://localhost:8000${message.attachment.url}`}
                download
                target="_blank"
                rel="noreferrer"
                className="ml-2 p-2 hover:bg-black/10 rounded-full transition-colors flex-shrink-0"
                title="Download"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
              </a>
            </div>
          )}

          {message.content}
        </div>

        {/* Timestamp + ticks */}
        <div
          className="flex items-center justify-end gap-1 mt-1 -mr-1"
          style={{ fontSize: "11px", color: "var(--text-secondary)" }}
        >
          <span>{timeStr}</span>
          {isOwn && (
            <span className="ml-0.5 text-xs">
              {message.status === "SENT" && <span className="opacity-70">✓</span>}
              {message.status === "DELIVERED" && <span className="opacity-70">✓✓</span>}
              {message.status === "READ" && <span style={{ color: "var(--tick-blue)" }}>✓✓</span>}
            </span>
          )}
        </div>

        {/* Reaction chips */}
        {reactionEntries.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {reactionEntries.map(([emoji, { count, isMine }]) => (
              <button
                key={emoji}
                onClick={() => onToggleReaction?.(message.id, emoji)}
                className="flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-xs font-medium transition-all hover:scale-110"
                style={{
                  backgroundColor: isMine ? "var(--accent)" : "rgba(255,255,255,0.15)",
                  color: isMine ? "white" : "inherit",
                  border: isMine ? "1.5px solid var(--accent)" : "1.5px solid rgba(255,255,255,0.2)",
                }}
              >
                <span>{emoji}</span>
                <span>{count}</span>
              </button>
            ))}
          </div>
        )}

        {/* Hover actions: react + reply */}
        <div
          className="absolute opacity-0 group-hover:opacity-100 transition-opacity flex gap-1"
          style={{ top: "4px", [isOwn ? "left" : "right"]: "calc(100% + 4px)" }}
        >
          {/* Reaction picker trigger */}
          {onToggleReaction && (
            <div className="relative">
              <button
                onClick={() => setShowReactionPicker(p => !p)}
                className="p-1.5 rounded-full hover:bg-white/10 transition-colors text-sm"
                title="React"
                style={{ color: "var(--text-secondary)" }}
              >
                😊
              </button>
              {showReactionPicker && (
                <div
                  className="absolute z-50 flex gap-1 p-2 rounded-xl shadow-xl"
                  style={{
                    backgroundColor: "var(--bg-secondary)",
                    border: "1px solid var(--border-color)",
                    bottom: "calc(100% + 4px)",
                    [isOwn ? "right" : "left"]: "0",
                  }}
                >
                  {ALLOWED_EMOJIS.map(emoji => (
                    <button
                      key={emoji}
                      onClick={() => { onToggleReaction(message.id, emoji); setShowReactionPicker(false); }}
                      className="text-xl hover:scale-125 transition-transform"
                      title={emoji}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Reply button */}
          {onReply && (
            <button
              onClick={() => onReply(message)}
              className="p-1.5 rounded-full hover:bg-white/10 transition-colors"
              title="Reply"
              style={{ color: "var(--text-secondary)" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="9 17 4 12 9 7" />
                <path d="M20 18v-2a4 4 0 0 0-4-4H4" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
