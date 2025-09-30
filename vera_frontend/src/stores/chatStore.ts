/**
 * Chat Store using Zustand
 * Implements MVP pattern - Model layer for chat/conversation state
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Message, Conversation, ChatSession } from '@/types/chat';
import { api } from '@/services/api';

export interface ChatState {
  // State
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  isLoading: boolean;
  isTyping: boolean;
  error: string | null;

  // WebSocket/Real-time state
  isConnected: boolean;
  connectionError: string | null;

  // Actions - Conversations
  fetchConversations: () => Promise<void>;
  createConversation: (title: string, type: 'direct' | 'group' | 'trichat', participants?: string[]) => Promise<Conversation>;
  setCurrentConversation: (conversation: Conversation | null) => void;

  // Actions - Messages
  fetchMessages: (conversationId: string) => Promise<void>;
  sendMessage: (content: string, type?: 'text' | 'audio') => Promise<Message>;
  markMessagesAsRead: (conversationId: string, messageIds?: string[]) => Promise<void>;

  // Actions - Sessions (for AI chat)
  createSession: (title?: string) => ChatSession;
  setCurrentSession: (session: ChatSession | null) => void;
  updateSession: (sessionId: string, updates: Partial<ChatSession>) => void;
  deleteSession: (sessionId: string) => void;

  // Actions - AI interactions
  sendAIMessage: (message: string) => Promise<void>;
  sendVoiceMessage: (audioBlob: Blob) => Promise<void>;

  // Actions - Real-time
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  setTyping: (isTyping: boolean) => void;

  // Actions - UI
  clearError: () => void;

  // Selectors
  getUnreadCount: () => number;
  getConversationMessages: (conversationId: string) => Message[];
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set, get) => ({
      // Initial state
      conversations: [],
      currentConversation: null,
      messages: [],
      sessions: [],
      currentSession: null,
      isLoading: false,
      isTyping: false,
      error: null,

      // WebSocket state
      isConnected: false,
      connectionError: null,

      // Conversation actions
      fetchConversations: async () => {
        set({ isLoading: true, error: null });

        try {
          const conversations = await api.getConversations();
          set({ conversations, isLoading: false });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to fetch conversations',
            isLoading: false
          });
        }
      },

      createConversation: async (title: string, type: 'direct' | 'group' | 'trichat', participants = []) => {
        set({ isLoading: true, error: null });

        try {
          const conversation = await api.createConversation({
            title,
            type,
            participants
          });

          set(state => ({
            conversations: [conversation, ...state.conversations],
            isLoading: false
          }));

          return conversation;
        } catch (error: any) {
          set({
            error: error.message || 'Failed to create conversation',
            isLoading: false
          });
          throw error;
        }
      },

      setCurrentConversation: (conversation: Conversation | null) => {
        set({ currentConversation: conversation });

        // Fetch messages when conversation changes
        if (conversation) {
          get().fetchMessages(conversation.id);
        } else {
          set({ messages: [] });
        }
      },

      // Message actions
      fetchMessages: async (conversationId: string) => {
        set({ isLoading: true, error: null });

        try {
          const messages = await api.getMessages(conversationId);
          set({ messages, isLoading: false });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to fetch messages',
            isLoading: false
          });
        }
      },

      sendMessage: async (content: string, type = 'text') => {
        const { currentConversation } = get();

        if (!currentConversation) {
          throw new Error('No active conversation');
        }

        try {
          const message = await api.sendMessage(currentConversation.id, {
            content,
            type
          });

          set(state => ({
            messages: [...state.messages, message]
          }));

          return message;
        } catch (error: any) {
          set({ error: error.message || 'Failed to send message' });
          throw error;
        }
      },

      markMessagesAsRead: async (conversationId: string, messageIds?: string[]) => {
        try {
          await api.markMessagesAsRead(conversationId, messageIds);

          // Update local state
          set(state => ({
            messages: state.messages.map(msg =>
              (!messageIds || messageIds.includes(msg.id)) && msg.conversation_id === conversationId
                ? { ...msg, is_read: true }
                : msg
            )
          }));
        } catch (error: any) {
          set({ error: error.message || 'Failed to mark messages as read' });
        }
      },

      // Session actions (for AI chat)
      createSession: (title = 'New Chat') => {
        const newSession: ChatSession = {
          id: `session-${Date.now()}`,
          title,
          messages: [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };

        set(state => ({
          sessions: [newSession, ...state.sessions],
          currentSession: newSession
        }));

        return newSession;
      },

      setCurrentSession: (session: ChatSession | null) => {
        set({ currentSession: session });
      },

      updateSession: (sessionId: string, updates: Partial<ChatSession>) => {
        set(state => ({
          sessions: state.sessions.map(session =>
            session.id === sessionId
              ? { ...session, ...updates, updated_at: new Date().toISOString() }
              : session
          ),
          currentSession: state.currentSession?.id === sessionId
            ? { ...state.currentSession, ...updates, updated_at: new Date().toISOString() }
            : state.currentSession
        }));
      },

      deleteSession: (sessionId: string) => {
        set(state => ({
          sessions: state.sessions.filter(session => session.id !== sessionId),
          currentSession: state.currentSession?.id === sessionId ? null : state.currentSession
        }));
      },

      // AI interaction actions
      sendAIMessage: async (message: string) => {
        const { currentSession } = get();

        if (!currentSession) {
          throw new Error('No active session');
        }

        // Add user message to session
        const userMessage: Message = {
          id: `msg-${Date.now()}`,
          conversation_id: currentSession.id,
          sender_id: 'user',
          content: message,
          type: 'text',
          timestamp: new Date().toISOString(),
          is_read: true
        };

        get().updateSession(currentSession.id, {
          messages: [...currentSession.messages, userMessage]
        });

        set({ isTyping: true });

        try {
          // Send to AI service
          const aiResponse = await api.sendAIMessage(message);

          const aiMessage: Message = {
            id: `msg-${Date.now()}-ai`,
            conversation_id: currentSession.id,
            sender_id: 'vira',
            content: aiResponse.content,
            type: 'text',
            timestamp: new Date().toISOString(),
            is_read: true
          };

          get().updateSession(currentSession.id, {
            messages: [...get().currentSession!.messages, aiMessage]
          });
        } catch (error: any) {
          set({ error: error.message || 'Failed to get AI response' });
        } finally {
          set({ isTyping: false });
        }
      },

      sendVoiceMessage: async (audioBlob: Blob) => {
        set({ isLoading: true, error: null });

        try {
          // Convert speech to text
          const transcription = await api.transcribeAudio(audioBlob);

          // Send as regular message
          await get().sendAIMessage(transcription);
        } catch (error: any) {
          set({
            error: error.message || 'Failed to process voice message',
            isLoading: false
          });
        } finally {
          set({ isLoading: false });
        }
      },

      // Real-time actions
      connectWebSocket: () => {
        // TODO: Implement WebSocket connection
        set({ isConnected: true, connectionError: null });
      },

      disconnectWebSocket: () => {
        // TODO: Implement WebSocket disconnection
        set({ isConnected: false });
      },

      setTyping: (isTyping: boolean) => {
        set({ isTyping });
      },

      // UI actions
      clearError: () => {
        set({ error: null, connectionError: null });
      },

      // Selectors
      getUnreadCount: () => {
        const { messages } = get();
        return messages.filter(msg => !msg.is_read && msg.sender_id !== 'user').length;
      },

      getConversationMessages: (conversationId: string) => {
        const { messages } = get();
        return messages.filter(msg => msg.conversation_id === conversationId);
      }
    }),
    {
      name: 'chat-store'
    }
  )
);
