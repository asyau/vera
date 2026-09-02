/**
 * Custom hook for WebSocket messaging
 * Handles real-time message updates, typing indicators, and presence
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { websocketService, NewMessageEvent, TypingEvent } from '@/services/websocketService';

export interface WebSocketMessage {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  message_type: string;
  timestamp: string;
  is_read: boolean;
}

export interface TypingUser {
  user_id: string;
  conversation_id: string;
  user_name?: string;
}

export function useWebSocketMessaging(conversationId: string | null) {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Join conversation when conversationId changes
  useEffect(() => {
    if (!conversationId || !websocketService.isConnected()) {
      return;
    }

    console.log('Joining conversation:', conversationId);

    websocketService
      .joinConversation(conversationId)
      .then(() => {
        console.log('Successfully joined conversation');
        setIsConnected(true);
      })
      .catch((error) => {
        console.error('Failed to join conversation:', error);
        setIsConnected(false);
      });

    return () => {
      console.log('Leaving conversation:', conversationId);
      websocketService.leaveConversation(conversationId);
      setIsConnected(false);
    };
  }, [conversationId]);

  // Listen for new messages
  useEffect(() => {
    const handleNewMessage = (data: NewMessageEvent) => {
      console.log('Received new message:', data);

      // Only add message if it's for the current conversation
      if (data.message.conversation_id === conversationId) {
        setMessages((prev) => {
          // Avoid duplicates
          if (prev.some((m) => m.id === data.message.id)) {
            return prev;
          }
          return [...prev, data.message];
        });
      }
    };

    websocketService.onNewMessage(handleNewMessage);

    return () => {
      websocketService.offNewMessage(handleNewMessage);
    };
  }, [conversationId]);

  // Listen for typing indicators
  useEffect(() => {
    const handleTypingStart = (data: TypingEvent) => {
      if (data.conversation_id === conversationId) {
        setTypingUsers((prev) => {
          // Avoid duplicates
          if (prev.some((u) => u.user_id === data.user_id)) {
            return prev;
          }
          return [...prev, data];
        });
      }
    };

    const handleTypingStop = (data: TypingEvent) => {
      if (data.conversation_id === conversationId) {
        setTypingUsers((prev) => prev.filter((u) => u.user_id !== data.user_id));
      }
    };

    websocketService.onTypingStart(handleTypingStart);
    websocketService.onTypingStop(handleTypingStop);

    return () => {
      websocketService.offTypingStart(handleTypingStart);
      websocketService.offTypingStop(handleTypingStop);
    };
  }, [conversationId]);

  // Send typing indicator (with debounce)
  const sendTypingIndicator = useCallback(() => {
    if (!conversationId || !websocketService.isConnected()) {
      return;
    }

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Send typing start
    websocketService.startTyping(conversationId);

    // Auto-stop typing after 3 seconds
    typingTimeoutRef.current = setTimeout(() => {
      websocketService.stopTyping(conversationId);
    }, 3000);
  }, [conversationId]);

  // Stop typing indicator
  const stopTyping = useCallback(() => {
    if (!conversationId || !websocketService.isConnected()) {
      return;
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }

    websocketService.stopTyping(conversationId);
  }, [conversationId]);

  // Mark message as read
  const markMessageAsRead = useCallback(
    (messageId: string) => {
      if (!conversationId || !websocketService.isConnected()) {
        return;
      }

      websocketService.markRead(conversationId, messageId);
    },
    [conversationId]
  );

  // Clear messages when conversation changes
  useEffect(() => {
    setMessages([]);
    setTypingUsers([]);
  }, [conversationId]);

  return {
    messages,
    typingUsers,
    isConnected,
    sendTypingIndicator,
    stopTyping,
    markMessageAsRead,
    addMessage: (message: WebSocketMessage) => setMessages((prev) => [...prev, message]),
    clearMessages: () => setMessages([]),
  };
}
