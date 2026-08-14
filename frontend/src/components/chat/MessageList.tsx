import React, { useEffect, useRef } from "react";
import { Message, GroupMember, Conversation } from "@/types";
import { MessageBubble } from "./MessageBubble";

interface MessageListProps {
  messages: Message[];
  currentUserId: string;
  conversation?: Conversation;
  onReply?: (message: Message) => void;
  onToggleReaction?: (messageId: string, emoji: string) => void;
}

export function MessageList({ messages, currentUserId, conversation, onReply, onToggleReaction }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div 
      className="flex-1 overflow-y-auto p-4 md:px-8 lg:px-12 xl:px-24 bg-chat-pattern"
      ref={scrollRef}
    >
      {messages.length === 0 ? (
        <div className="h-full flex items-center justify-center text-muted italic text-sm">
          No messages here yet... Start the conversation!
        </div>
      ) : (
        <div className="flex flex-col mt-auto pt-4">
          {messages.map((message) => {
            const isOwn = message.sender_id === currentUserId;
            let senderName: string | undefined;
            if (!isOwn && conversation?.type === "GROUP") {
              const member = conversation.members?.find(
                (m: GroupMember) => m.id === message.sender_id || m.user_id === message.sender_id
              );
              senderName = member?.display_name || "Unknown";
            }
            return (
              <MessageBubble 
                key={message.id} 
                message={message} 
                isOwn={isOwn} 
                senderName={senderName}
                currentUserId={currentUserId}
                onReply={onReply}
                onToggleReaction={onToggleReaction}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
