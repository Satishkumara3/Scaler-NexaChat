import { useEffect, useCallback, useRef } from 'react';
import { useChatStore } from '@/store/useChatStore';
import useStore from '@/store/useStore';
import api from '@/lib/api';
import { Message, Conversation } from '@/types';

export function useChat() {
  const { 
    conversations, 
    messages, 
    setConversations, 
    setMessages, 
    addMessage, 
    updateMessageStatus,
    updateMessageReactions,
    setConversationsLoading, 
    setMessagesLoading,
    setUserOnline,
    setUserTyping,
    onlineUsers,
    typingUsers,
    replyTarget,
    setReplyTarget,
    clearReplyTarget,
  } = useChatStore();
  
  const { activeConversationId, setActiveConversationId, setWsConnected } = useStore();
  const currentUser = useStore(state => state.currentUser);
  const wsRef = useRef<WebSocket | null>(null);

  // Load conversations
  const loadConversations = useCallback(async () => {
    try {
      setConversationsLoading(true);
      const res = await api.get('/api/conversations');
      setConversations(res.data.conversations as Conversation[]);
    } catch (e) {
      console.error("Failed to load conversations", e);
    } finally {
      setConversationsLoading(false);
    }
  }, [setConversations, setConversationsLoading]);

  // Load messages for a conversation
  const loadMessages = useCallback(async (conversationId: string) => {
    try {
      setMessagesLoading(conversationId, true);
      const res = await api.get(`/api/messages/${conversationId}`);
      setMessages(conversationId, res.data.messages as Message[]);
    } catch (e) {
      console.error("Failed to load messages", e);
    } finally {
      setMessagesLoading(conversationId, false);
    }
  }, [setMessages, setMessagesLoading]);

  // Initialize WS
  useEffect(() => {
    // During dev, frontend might be on 3000 but backend on 8000
    // Best way is to connect to the backend URL used by axios
    // Assuming backend is relative usually, but for local dev:
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = backendUrl.replace(/^http/, 'ws') + '/ws';
    
    console.log("Connecting to WS:", wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WS Connected');
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'message.new') {
          addMessage(data.payload as Message);
          loadConversations();
          const msg = data.payload as Message;
          api.put(`/api/messages/${msg.id}/status`, { status: "DELIVERED" }).catch(e => console.error(e));

        } else if (data.type === 'message.delivered' || data.type === 'message.read') {
          const { message_id, conversation_id, status } = data.payload;
          updateMessageStatus(conversation_id, message_id, status);
          loadConversations();
          
        } else if (data.type === 'presence.online') {
          setUserOnline(data.payload.user_id, true);
        } else if (data.type === 'presence.offline') {
          setUserOnline(data.payload.user_id, false);
        } else if (data.type === 'typing.start') {
          setUserTyping(data.payload.conversation_id, data.payload.user_id, true);
        } else if (data.type === 'typing.stop') {
          setUserTyping(data.payload.conversation_id, data.payload.user_id, false);
        } else if (data.type === 'reaction.added') {
          const { message_id, conversation_id, user_id, emoji, reaction_id, created_at } = data.payload;
          updateMessageReactions(conversation_id, message_id, emoji, user_id, 'added', reaction_id, created_at);
        } else if (data.type === 'reaction.removed') {
          const { message_id, conversation_id, user_id, emoji } = data.payload;
          updateMessageReactions(conversation_id, message_id, emoji, user_id, 'removed');
        }
      } catch (e) {
        console.error("Error parsing WS message", e);
      }
    };

    ws.onclose = () => {
      console.log('WS Disconnected');
      setWsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [addMessage, loadConversations, setWsConnected]);

  // Send message REST — supports optional reply
  const sendMessage = useCallback(async (conversationId: string, content: string, replyToMessageId?: string) => {
    try {
      const res = await api.post('/api/messages', {
        conversation_id: conversationId,
        content: content,
        message_type: 'TEXT',
        ...(replyToMessageId ? { reply_to_message_id: replyToMessageId } : {}),
      });
      addMessage(res.data.message as Message);
      loadConversations();
    } catch (e) {
      console.error("Failed to send message", e);
      throw e;
    }
  }, [addMessage, loadConversations]);

  const sendAttachment = useCallback(async (conversationId: string, file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post(`/api/messages/${conversationId}/attachments`, formData, {
         headers: { 'Content-Type': 'multipart/form-data' }
      });
      addMessage(res.data.message as Message);
      loadConversations();
    } catch (e) {
      console.error("Failed to upload attachment", e);
      throw e;
    }
  }, [addMessage, loadConversations]);

  // Handle switching conversations
  const selectConversation = useCallback((id: string) => {
    setActiveConversationId(id);
    if (!messages[id]) {
        loadMessages(id);
    }
    // Phase 4: Mark unread messages as read
    const activeMessages = messages[id] || [];
    activeMessages.forEach((m) => {
        if (m.sender_id !== currentUser?.id && m.status !== "READ") {
            api.put(`/api/messages/${m.id}/status`, { status: "READ" }).catch(() => {});
        }
    });
  }, [setActiveConversationId, messages, loadMessages, currentUser?.id]);
  
  // Send typing event
  const sendTypingEvent = useCallback((isTyping: boolean) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && activeConversationId) {
       wsRef.current.send(JSON.stringify({
           type: isTyping ? 'client.typing.start' : 'client.typing.stop',
           payload: { conversation_id: activeConversationId }
       }));
    }
  }, [activeConversationId]);
  
  // Creates direct chat (or gets existing) given a user_id
  const startDirectChat = useCallback(async (userId: string) => {
      try {
          const res = await api.post('/api/conversations', { user_id: userId });
          const newConv = res.data.conversation;
          await loadConversations(); // refresh list
          selectConversation(newConv.id);
      } catch (e) {
          console.error("Error starting chat", e);
      }
  }, [loadConversations, selectConversation]);

  // Toggle emoji reaction
  const toggleReaction = useCallback(async (messageId: string, emoji: string) => {
    try {
      await api.post(`/api/messages/${messageId}/reactions`, { emoji });
      // Real-time update arrives via WS; optimistic update is optional
    } catch (e) {
      console.error("Failed to toggle reaction", e);
      throw e;
    }
  }, []);

  // Initial load
  useEffect(() => {
     loadConversations();
  }, [loadConversations]);

  return {
    conversations,
    activeConversationId,
    activeConversation: conversations.find(c => c.id === activeConversationId) || null,
    messages: activeConversationId ? messages[activeConversationId] || [] : [],
    sendMessage,
    sendAttachment,
    selectConversation,
    startDirectChat,
    loadConversations,
    onlineUsers,
    typingUsers,
    sendTypingEvent,
    toggleReaction,
    replyTarget,
    setReplyTarget,
    clearReplyTarget,
  };
}
