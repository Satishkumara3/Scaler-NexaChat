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
      <div className="flex items-center gap-4 pr-3 text-muted">
         <button 
           onClick={() => alert("Voice and video calling are placeholders.")}
           className="hover:text-primary transition-colors hover:bg-white/5 p-2 rounded-full cursor-pointer"
           title="Voice Call"
         >
           <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
             <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
           </svg>
         </button>
         <button 
           onClick={() => alert("Voice and video calling are placeholders.")}
           className="hover:text-primary transition-colors hover:bg-white/5 p-2 rounded-full cursor-pointer"
           title="Video Call"
         >
           <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
             <polygon points="23 7 16 12 23 17 23 7"></polygon>
             <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
           </svg>
         </button>
         <button className="hover:text-primary transition-colors hover:bg-white/5 p-2 rounded-full cursor-pointer ml-1">
           <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
             <circle cx="12" cy="12" r="1"></circle>
             <circle cx="19" cy="12" r="1"></circle>
             <circle cx="5" cy="12" r="1"></circle>
           </svg>
         </button>
      </div>
    </header>
  );
}
