/**
 * WebSocket Service for Real-Time Communication
 * Handles Socket.IO connections, messaging, typing indicators, and presence
 */
import { io, Socket } from 'socket.io-client';

// WebSocket event types
export interface NewMessageEvent {
  message: {
    id: string;
    conversation_id: string;
    sender_id: string;
    content: string;
    message_type: string;
    timestamp: string;
    is_read: boolean;
  };
}

export interface TypingEvent {
  user_id: string;
  conversation_id: string;
  user_name?: string;
}

export interface PresenceEvent {
  user_id: string;
  status: 'online' | 'offline';
  timestamp: string;
}

export interface MessageReadEvent {
  message_id: string;
  conversation_id: string;
  user_id: string;
  read_at: string;
}

export interface NotificationEvent {
  notification: {
    id: string;
    type: string;
    title: string;
    message: string;
    data?: any;
    timestamp: string;
  };
}

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private baseURL = 'http://localhost:8000';

  /**
   * Connect to WebSocket server with JWT authentication
   */
  connect(token: string): void {
    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    console.log('Connecting to WebSocket server...');

    this.socket = io(this.baseURL, {
      path: '/socket.io',
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.setupListeners();
  }

  /**
   * Set up core event listeners
   */
  private setupListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected:', this.socket?.id);
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ WebSocket disconnected:', reason);

      // Attempt reconnection if not intentional
      if (reason === 'io server disconnect') {
        // Server disconnected, try to reconnect
        this.socket?.connect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
      }
    });

    this.socket.on('connection_established', (data) => {
      console.log('Connection established:', data);
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      console.log('Disconnecting WebSocket...');
      this.socket.disconnect();
      this.socket = null;
      this.reconnectAttempts = 0;
    }
  }

  /**
   * Join a conversation room
   */
  joinConversation(conversationId: string): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.socket?.connected) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      console.log('Joining conversation:', conversationId);

      this.socket.emit(
        'join_conversation',
        { conversation_id: conversationId },
        (response: any) => {
          if (response?.error) {
            console.error('Failed to join conversation:', response.error);
            reject(new Error(response.error));
          } else {
            console.log('Joined conversation successfully:', response);
            resolve(response);
          }
        }
      );
    });
  }

  /**
   * Leave a conversation room
   */
  leaveConversation(conversationId: string): void {
    if (!this.socket?.connected) {
      console.warn('Cannot leave conversation: WebSocket not connected');
      return;
    }

    console.log('Leaving conversation:', conversationId);
    this.socket.emit('leave_conversation', { conversation_id: conversationId });
  }

  /**
   * Start typing indicator
   */
  startTyping(conversationId: string): void {
    if (!this.socket?.connected) return;

    this.socket.emit('typing_start', { conversation_id: conversationId });
  }

  /**
   * Stop typing indicator
   */
  stopTyping(conversationId: string): void {
    if (!this.socket?.connected) return;

    this.socket.emit('typing_stop', { conversation_id: conversationId });
  }

  /**
   * Mark message as read
   */
  markRead(conversationId: string, messageId: string): void {
    if (!this.socket?.connected) return;

    this.socket.emit('mark_read', {
      conversation_id: conversationId,
      message_id: messageId,
    });
  }

  /**
   * Get online users in a conversation
   */
  getOnlineUsers(conversationId: string): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.socket?.connected) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      this.socket.emit(
        'get_online_users',
        { conversation_id: conversationId },
        (response: any) => {
          if (response?.error) {
            reject(new Error(response.error));
          } else {
            resolve(response);
          }
        }
      );
    });
  }

  // Event Listeners

  /**
   * Listen for new messages
   */
  onNewMessage(callback: (data: NewMessageEvent) => void): void {
    this.socket?.on('new_message', callback);
  }

  /**
   * Listen for typing start events
   */
  onTypingStart(callback: (data: TypingEvent) => void): void {
    this.socket?.on('typing_start', callback);
  }

  /**
   * Listen for typing stop events
   */
  onTypingStop(callback: (data: TypingEvent) => void): void {
    this.socket?.on('typing_stop', callback);
  }

  /**
   * Listen for presence updates (online/offline)
   */
  onPresenceUpdate(callback: (data: PresenceEvent) => void): void {
    this.socket?.on('presence_update', callback);
  }

  /**
   * Listen for message read receipts
   */
  onMessageRead(callback: (data: MessageReadEvent) => void): void {
    this.socket?.on('message_read', callback);
  }

  /**
   * Listen for notifications
   */
  onNotification(callback: (data: NotificationEvent) => void): void {
    this.socket?.on('notification', callback);
  }

  // Remove Event Listeners

  /**
   * Remove new message listener
   */
  offNewMessage(callback: (data: NewMessageEvent) => void): void {
    this.socket?.off('new_message', callback);
  }

  /**
   * Remove typing start listener
   */
  offTypingStart(callback: (data: TypingEvent) => void): void {
    this.socket?.off('typing_start', callback);
  }

  /**
   * Remove typing stop listener
   */
  offTypingStop(callback: (data: TypingEvent) => void): void {
    this.socket?.off('typing_stop', callback);
  }

  /**
   * Remove presence update listener
   */
  offPresenceUpdate(callback: (data: PresenceEvent) => void): void {
    this.socket?.off('presence_update', callback);
  }

  /**
   * Remove message read listener
   */
  offMessageRead(callback: (data: MessageReadEvent) => void): void {
    this.socket?.off('message_read', callback);
  }

  /**
   * Remove notification listener
   */
  offNotification(callback: (data: NotificationEvent) => void): void {
    this.socket?.off('notification', callback);
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  /**
   * Get socket instance (for advanced usage)
   */
  getSocket(): Socket | null {
    return this.socket;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();
