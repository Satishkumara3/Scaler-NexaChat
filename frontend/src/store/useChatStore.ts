import { create } from "zustand";
import { Conversation, Message, Reaction } from "@/types";

interface ChatState {
  conversations: Conversation[];
  messages: Record<string, Message[]>;
  isConversationsLoading: boolean;
  isMessagesLoading: Record<string, boolean>;
  onlineUsers: Record<string, boolean>;
  typingUsers: Record<string, Set<string>>;
  replyTarget: Message | null;  // Phase 7B: message being replied to

  setConversations: (conversations: Conversation[]) => void;
  addConversation: (conversation: Conversation) => void;
  updateConversation: (id: string, updates: Partial<Conversation>) => void;
  
  setMessages: (conversationId: string, messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessageStatus: (conversationId: string, messageId: string, status: 'SENT' | 'DELIVERED' | 'READ') => void;
  updateMessageReactions: (conversationId: string, messageId: string, emoji: string, userId: string, action: 'added' | 'removed', reactionId?: string, createdAt?: string) => void;
  
  setConversationsLoading: (loading: boolean) => void;
  setMessagesLoading: (conversationId: string, loading: boolean) => void;

  setUserOnline: (userId: string, isOnline: boolean) => void;
  setUserTyping: (conversationId: string, userId: string, isTyping: boolean) => void;

  setReplyTarget: (message: Message | null) => void;
  clearReplyTarget: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  messages: {},
  isConversationsLoading: false,
  isMessagesLoading: {},
  onlineUsers: {},
  typingUsers: {},
  replyTarget: null,

  setConversations: (conversations) => set({ conversations }),
  
  addConversation: (conversation) => set((state) => ({
    conversations: [conversation, ...state.conversations.filter(c => c.id !== conversation.id)]
  })),

  updateConversation: (id, updates) => set((state) => ({
    conversations: state.conversations.map(c => 
      c.id === id ? { ...c, ...updates } : c
    )
  })),

  setMessages: (conversationId, messages) => set((state) => ({
    messages: {
      ...state.messages,
      [conversationId]: messages
    }
  })),

  addMessage: (message) => set((state) => {
    const existing = state.messages[message.conversation_id] || [];
    if (existing.some(m => m.id === message.id)) return state;
    return {
      messages: {
        ...state.messages,
        [message.conversation_id]: [...existing, message].sort((a, b) => 
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        )
      }
    };
  }),

  updateMessageStatus: (conversationId, messageId, status) => set((state) => {
      const messages = state.messages[conversationId];
      if (!messages) return state;
      return {
          messages: {
              ...state.messages,
              [conversationId]: messages.map(m => 
                  m.id === messageId ? { ...m, status } : m
              )
          }
      };
  }),

  updateMessageReactions: (conversationId, messageId, emoji, userId, action, reactionId, createdAt) => set((state) => {
    const messages = state.messages[conversationId];
    if (!messages) return state;
    return {
      messages: {
        ...state.messages,
        [conversationId]: messages.map(m => {
          if (m.id !== messageId) return m;
          const existing = m.reactions || [];
          if (action === 'removed') {
            return { ...m, reactions: existing.filter(r => !(r.user_id === userId && r.emoji === emoji)) };
          } else {
            // Avoid duplicates
            if (existing.some(r => r.user_id === userId && r.emoji === emoji)) return m;
            const newReaction: Reaction = {
              id: reactionId || `${userId}-${emoji}`,
              message_id: messageId,
              user_id: userId,
              emoji,
              created_at: createdAt || new Date().toISOString(),
            };
            return { ...m, reactions: [...existing, newReaction] };
          }
        })
      }
    };
  }),

  setConversationsLoading: (loading) => set({ isConversationsLoading: loading }),
  
  setMessagesLoading: (conversationId, loading) => set((state) => ({
    isMessagesLoading: {
      ...state.isMessagesLoading,
      [conversationId]: loading
    }
  })),

  setUserOnline: (userId, isOnline) => set((state) => ({
      onlineUsers: {
          ...state.onlineUsers,
          [userId]: isOnline
      }
  })),

  setUserTyping: (conversationId, userId, isTyping) => set((state) => {
      const currentTyping = state.typingUsers[conversationId] || new Set<string>();
      const nextTyping = new Set(currentTyping);
      if (isTyping) nextTyping.add(userId);
      else nextTyping.delete(userId);
      return {
          typingUsers: {
              ...state.typingUsers,
              [conversationId]: nextTyping
          }
      };
  }),

  setReplyTarget: (message) => set({ replyTarget: message }),
  clearReplyTarget: () => set({ replyTarget: null }),
}));
