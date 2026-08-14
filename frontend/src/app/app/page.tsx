"use client";

import { useAuth } from "@/hooks/useAuth";
import { useChat } from "@/hooks/useChat";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

// Components
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { EmptyChatState } from "@/components/chat/EmptyChatState";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { MessageList } from "@/components/chat/MessageList";
import { MessageComposer } from "@/components/chat/MessageComposer";
import { NewGroupModal } from "@/components/chat/NewGroupModal";
import { GroupDetailsModal } from "@/components/chat/GroupDetailsModal";
import { SettingsModal } from "@/components/chat/SettingsModal";
import { UsersModal } from "@/components/chat/UsersModal";
import { Contact, User } from "@/types";
import api from "@/lib/api";

export default function AppPage() {
  const { currentUser, isAuthLoading, logout } = useAuth();
  const router = useRouter();
  const [showContacts, setShowContacts] = useState(false);
  const [isGroupModalOpen, setIsGroupModalOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [usersList, setUsersList] = useState<User[]>([]);

  const { 
    conversations, 
    activeConversationId, 
    activeConversation, 
    messages, 
    selectConversation, 
    sendMessage,
    sendAttachment,
    onlineUsers,
    typingUsers,
    sendTypingEvent,
    toggleReaction,
    replyTarget,
    setReplyTarget,
    clearReplyTarget,
    startDirectChat,
  } = useChat();

  const isOnline = activeConversation?.other_user?.id 
    ? onlineUsers[activeConversation.other_user.id] 
    : false;
    
  const isTyping = activeConversationId && activeConversation?.other_user?.id
    ? typingUsers[activeConversationId]?.has(activeConversation.other_user.id)
    : false;

  // Protect route
  useEffect(() => {
    if (!isAuthLoading && !currentUser) {
      router.replace("/login");
    }
  }, [isAuthLoading, currentUser, router]);

  if (isAuthLoading || !currentUser) {
    return null; // or a spinner
  }

  const handleSendMessage = async (content: string) => {
    if (!activeConversationId) return;
    await sendMessage(activeConversationId, content, replyTarget?.id);
    clearReplyTarget();
    sendTypingEvent(false);
  };

  const handleSendAttachment = async (file: File) => {
    if (!activeConversationId) return;
    // from useChat
    await sendAttachment(activeConversationId, file);
  };

  const handleTyping = (isTypingEvent: boolean) => {
      sendTypingEvent(isTypingEvent);
  };

  const handleOpenGroupModal = async () => {
      setIsGroupModalOpen(true);
      try {
          const res = await api.get("/api/users");
          setUsersList(res.data.users.filter((u: User) => u.id !== currentUser?.id));
      } catch (e) {
          console.error("Failed to load users", e);
      }
  };

  const handleCreateGroup = async (name: string, memberIds: string[]) => {
      try {
          // Add current user implicitly
          const res = await api.post("/api/groups", { name, member_ids: [...memberIds] });
          setIsGroupModalOpen(false);
          // addConversation will be pulled when WS or sync hits, but we can do it manually or fetch list again
          window.location.reload(); // Quick phase 5 refresh implementation
      } catch (err) {
          console.error(err);
          alert("Failed to create group");
      }
  };

  return (
    <main
      className="flex h-full w-full overflow-hidden"
      style={{ backgroundColor: "var(--bg-primary)" }}
    >
      <ConversationSidebar 
         conversations={conversations}
         activeId={activeConversationId}
         onSelect={selectConversation}
         isLoading={false}
         onNewChat={() => setShowContacts(true)}
         onNewGroup={handleOpenGroupModal}
         onSettings={() => setIsSettingsOpen(true)}
      />

      <div className="flex-1 flex flex-col h-full relative">
         {!activeConversationId ? (
            <EmptyChatState />
         ) : (
            <>
               <ChatHeader 
                  conversation={activeConversation} 
                  isOnline={!!isOnline}
                  isTyping={!!isTyping}
                  onClick={() => setIsDetailsOpen(true)}
               />
               <MessageList 
                 messages={messages} 
                 currentUserId={currentUser.id} 
                 conversation={activeConversation || undefined}
                 onReply={setReplyTarget}
                 onToggleReaction={toggleReaction}
               />
               <MessageComposer 
                  onSendMessage={handleSendMessage} 
                  onSendAttachment={handleSendAttachment}
                  onTyping={handleTyping}
                  replyTarget={replyTarget}
                  onCancelReply={clearReplyTarget}
               />
            </>
         )}

         {showContacts && (
             <UsersModal 
                 currentUserId={currentUser.id}
                 onClose={() => setShowContacts(false)}
                 onSelectUser={(userId) => {
                     startDirectChat(userId);
                     setShowContacts(false);
                 }}
             />
         )}

         {isGroupModalOpen && (
             <NewGroupModal 
                 users={usersList} 
                 onClose={() => setIsGroupModalOpen(false)} 
                 onCreate={handleCreateGroup} 
             />
         )}

         {isDetailsOpen && activeConversation?.type === "GROUP" && (
             <GroupDetailsModal 
                 conversation={activeConversation} 
                 currentUserId={currentUser.id}
                 onClose={() => setIsDetailsOpen(false)} 
             />
         )}

         {isSettingsOpen && (
             <SettingsModal 
                 currentUser={currentUser} 
                 onClose={() => setIsSettingsOpen(false)}
                 onLogout={logout || (() => router.replace("/login"))}
             />
         )}
      </div>
    </main>
  );
}
