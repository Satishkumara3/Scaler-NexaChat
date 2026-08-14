import React from "react";
import Avatar from "@/components/common/Avatar";
import { Conversation } from "@/types";

interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onClick: () => void;
}

export function ConversationItem({ conversation, isActive, onClick }: ConversationItemProps) {
  const isGroup = conversation.type === "GROUP";
  const display_name = isGroup ? (conversation.name || "Group") : (conversation.other_user?.display_name || "Unknown User");
  const avatar_url = isGroup ? conversation.avatar_url : conversation.other_user?.avatar_url;
  
  // Last message snippet
  let lastMessageText = "";
  let lastMessageTime = "";
  if (conversation.last_message) {
      lastMessageText = conversation.last_message.content;
      // Format time safely
      try {
          const date = new Date(conversation.last_message.created_at);
          // If today, show time, else show date
          if (date.toDateString() === new Date().toDateString()) {
              lastMessageTime = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          } else {
              lastMessageTime = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
          }
      } catch (e) {
          lastMessageTime = "";
      }
  } else {
      // Just fallback to conversation creation or update
      try {
          lastMessageTime = new Date(conversation.updated_at).toLocaleDateString();
      } catch(e) {}
  }

  // Max length
  if (lastMessageText.length > 30) {
      lastMessageText = lastMessageText.substring(0, 30) + "...";
  }

  return (
    <div 
      onClick={onClick}
      className={`flex items-center gap-3 p-3 cursor-pointer transition-colors ${
        isActive ? 'bg-[var(--bg-tertiary)]' : 'hover:bg-[var(--bg-tertiary)] hover:bg-opacity-50'
      }`}
      style={{
         borderRadius: '8px',
         margin: '0 4px 2px 4px'
      }}
    >
      <Avatar name={display_name} src={avatar_url} size={48} />
      
      <div className="flex-1 min-w-0 flex flex-col justify-center">
        <div className="flex justify-between items-baseline mb-1">
          <span className="font-semibold text-primary truncate text-[15px]">
            {display_name}
          </span>
          <span className={`text-[12px] whitespace-nowrap ml-2 ${conversation.unread_count ? 'text-[var(--accent)] font-semibold' : 'text-muted'}`}>
            {lastMessageTime}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-[13px] text-secondary truncate">
            {lastMessageText || <span className="italic">No messages yet</span>}
          </span>
          {!!conversation.unread_count && (
            <span 
              className="px-2 py-0.5 mt-0.5 rounded-full text-[11px] font-bold"
              style={{ backgroundColor: 'var(--accent)', color: '#fff' }}
            >
              {conversation.unread_count}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
