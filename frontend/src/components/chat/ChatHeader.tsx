import React from "react";
import Avatar from "@/components/common/Avatar";
import { Conversation } from "@/types";

interface ChatHeaderProps {
  conversation: Conversation | null;
  isOnline: boolean;
  isTyping: boolean;
  onClick?: () => void;
}

export function ChatHeader({ conversation, isOnline, isTyping, onClick }: ChatHeaderProps) {
  if (!conversation) return null;

  const isGroup = conversation.type === "GROUP";
  const display_name = isGroup ? (conversation.name || "Group") : (conversation.other_user?.display_name || "Unknown User");
  const avatar_url = isGroup ? conversation.avatar_url : conversation.other_user?.avatar_url;
  
  let status_text = "";
  if (isGroup) {
      const activeMembersCount = conversation.members?.length || 0;
      status_text = `${activeMembersCount} members`;
  } else {
      const last_seen_raw = conversation.other_user?.last_seen;
      status_text = "Offline";
      if (isTyping) {
          status_text = "Typing...";
      } else if (isOnline) {
          status_text = "Online";
      } else if (last_seen_raw) {
          const last_seen_date = new Date(last_seen_raw);
          status_text = `Last seen ${last_seen_date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }
  }

  return (
    <header 
      className="p-3 flex items-center justify-between"
      style={{
        backgroundColor: "var(--bg-secondary)",
        borderBottom: "1px solid var(--border-color)",
        height: "64px"
      }}
    >
      <div 
        className="flex items-center gap-4 pl-2 cursor-pointer hover:bg-white/5 p-1 rounded transition-colors"
        onClick={onClick}
      >
        <Avatar name={display_name} src={avatar_url} size={40} />
        
        <div className="flex flex-col">
          <span className="font-semibold text-lg text-primary leading-tight">
            {display_name}
          </span>
          <div className="flex flex-row items-center gap-1">
             <span className={`text-[13px] ${isTyping || isOnline ? 'text-[var(--accent)] font-medium' : 'text-muted'}`}>
               {status_text}
             </span>
             {isTyping && !isGroup && (
               <div className="flex items-center gap-1 ml-1 translate-y-[2px]">
                 <div className="typing-dot"></div>
                 <div className="typing-dot"></div>
                 <div className="typing-dot"></div>
               </div>
             )}
          </div>
        </div>
      </div>
      
      {/* Right side actions placeholder */}
      <div className="flex items-center gap-3 pr-2 text-muted">
         <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="1"></circle><circle cx="19" cy="12" r="1"></circle><circle cx="5" cy="12" r="1"></circle></svg>
      </div>
    </header>
  );
}
