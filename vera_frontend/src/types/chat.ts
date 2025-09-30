/**
 * Chat and messaging type definitions
 */

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  type: 'text' | 'audio' | 'file' | 'system';
  timestamp: string;
  is_read: boolean;
  metadata?: Record<string, any>;
}

export interface Conversation {
  id: string;
  title: string;
  type: 'direct' | 'group' | 'trichat';
  creator_id: string;
  participants: string[];
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface CreateConversationRequest {
  title: string;
  type: 'direct' | 'group' | 'trichat';
  participants?: string[];
}

export interface SendMessageRequest {
  content: string;
  type?: 'text' | 'audio' | 'file';
  metadata?: Record<string, any>;
}
