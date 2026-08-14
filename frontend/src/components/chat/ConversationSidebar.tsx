import React from "react";
import Avatar from "@/components/common/Avatar";
import { Conversation } from "@/types";
import { ConversationItem } from "./ConversationItem";
import { useAuth } from "@/hooks/useAuth";

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  isLoading: boolean;
  onNewChat?: () => void;
  onNewGroup?: () => void;
  onSettings?: () => void;
}

export function ConversationSidebar({ 
  conversations, 
  activeId, 
  onSelect,
  isLoading,
  onNewChat,
  onNewGroup,
  onSettings
}: ConversationSidebarProps) {
  const { currentUser } = useAuth();
  const [searchQuery, setSearchQuery] = React.useState("");
  
  if (!currentUser) return null;

  const filteredConversations = conversations.filter(c => {
     if (!searchQuery) return true;
     const query = searchQuery.toLowerCase();
     const isGroup = c.type === "GROUP";
     const matchName = isGroup ? (c.name || "Group") : (c.other_user?.display_name || "Unknown User");
     return matchName.toLowerCase().includes(query);
  });

  return (
    <aside 
      className="h-full flex flex-col"
      style={{ 
        width: "var(--sidebar-width)",
        backgroundColor: "var(--bg-secondary)",
        borderRight: "1px solid var(--border-color)"
      }}
    >
      <header 
        className="p-3 flex items-center justify-between"
        style={{
          borderBottom: "1px solid var(--border-color)",
          height: "64px"
        }}
      >
        <div className="flex items-center gap-3">
          <Avatar 
            name={currentUser.display_name} 
            src={currentUser.avatar_url!} 
            size={40} 
          />
        </div>
        
        <div className="flex items-center gap-2">
          {/* New chat button placeholder */}
          <button 
            className="p-2 rounded-full hover:bg-white/5 transition-colors"
            title="New Chat (Use contacts)"
            onClick={onNewChat}
          >
             <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
          </button>
          
          {/* New group button */}
          <button 
            className="p-2 rounded-full hover:bg-white/5 transition-colors"
            title="New Group"
            onClick={onNewGroup}
          >
             <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
          </button>
          
          {/* Settings button */}
          <button 
            className="p-2 rounded-full hover:bg-white/5 transition-colors"
            title="Settings"
            onClick={onSettings}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          </button>
        </div>
      </header>

      {/* Search Input Placeholder */}
      <div className="p-2">
         <div 
           className="px-3 py-1.5 flex items-center gap-2 rounded-lg"
           style={{ backgroundColor: "var(--bg-primary)" }}
         >
           <svg className="text-muted" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
           <input 
             type="text" 
             placeholder="Search" 
             value={searchQuery}
             onChange={(e) => setSearchQuery(e.target.value)}
             className="bg-transparent text-sm w-full outline-none text-primary"
           />
           {searchQuery && (
              <button 
                  onClick={() => setSearchQuery("")} 
                  className="text-muted hover:text-primary transition-colors focus:outline-none"
              >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
           )}
         </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto px-2">
        {isLoading ? (
          <div className="text-center p-4 text-muted text-sm">Loading chats...</div>
        ) : conversations.length === 0 ? (
          <div className="text-center p-4 text-muted text-sm mt-10">
            No conversations yet.<br/>Start a new chat!
          </div>
        ) : filteredConversations.length === 0 && searchQuery ? (
          <div className="text-center p-4 text-muted text-sm mt-10">
            No results found for &quot;{searchQuery}&quot;
          </div>
        ) : (
          filteredConversations.map(conv => (
             <ConversationItem 
               key={conv.id}
               conversation={conv}
               isActive={activeId === conv.id}
               onClick={() => onSelect(conv.id)}
             />
          ))
        )}
      </div>
    </aside>
  );
}
