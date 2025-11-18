# WebSocket Real-Time Implementation Guide

## ✅ Backend Complete (Just Implemented)

### What Was Added:

1. **WebSocket Service** (`app/services/websocket_service.py`):
   - Connection manager for user sessions
   - Presence tracking (online/offline)
   - Typing indicators
   - Room management for conversations
   - Message broadcasting

2. **WebSocket Routes** (`app/routes/websocket.py`):
   - Socket.IO endpoints for real-time communication
   - Events: `connect`, `disconnect`, `join_conversation`, `leave_conversation`, `typing_start`, `typing_stop`, `mark_read`
   - JWT authentication for WebSocket connections

3. **Integration**:
   - Mounted Socket.IO app in `main.py` at `/socket.io`
   - Updated `messaging.py` to broadcast messages via WebSocket
   - Added `get_current_user_id_from_token()` for WebSocket auth

4. **Dependencies**:
   - Added `python-socketio==5.11.0` and `python-engineio==4.9.0` to `requirements.txt`

---

## 🔨 Frontend Implementation (Next Steps)

### Step 1: Install Socket.IO Client

```bash
cd vera_frontend
npm install socket.io-client
```

### Step 2: Create WebSocket Manager

Create `vera_frontend/src/services/websocketService.ts`:

```typescript
import { io, Socket } from 'socket.io-client';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(token: string) {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io('http://localhost:8000', {
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

  private setupListeners() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected:', this.socket?.id);
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;
    });

    this.socket.on('connection_established', (data) => {
      console.log('Connection established:', data);
    });
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }

  // Join conversation
  joinConversation(conversationId: string): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.socket?.connected) {
        reject(new Error('Not connected'));
        return;
      }

      this.socket.emit(
        'join_conversation',
        { conversation_id: conversationId },
        (response: any) => {
          if (response.error) {
            reject(new Error(response.error));
          } else {
            resolve(response);
          }
        }
      );
    });
  }

  // Leave conversation
  leaveConversation(conversationId: string) {
    this.socket?.emit('leave_conversation', { conversation_id: conversationId });
  }

  // Typing indicators
  startTyping(conversationId: string) {
    this.socket?.emit('typing_start', { conversation_id: conversationId });
  }

  stopTyping(conversationId: string) {
    this.socket?.emit('typing_stop', { conversation_id: conversationId });
  }

  // Mark message as read
  markRead(conversationId: string, messageId: string) {
    this.socket?.emit('mark_read', {
      conversation_id: conversationId,
      message_id: messageId,
    });
  }

  // Event listeners
  onNewMessage(callback: (data: any) => void) {
    this.socket?.on('new_message', callback);
  }

  onTypingStart(callback: (data: any) => void) {
    this.socket?.on('typing_start', callback);
  }

  onTypingStop(callback: (data: any) => void) {
    this.socket?.on('typing_stop', callback);
  }

  onPresenceUpdate(callback: (data: any) => void) {
    this.socket?.on('presence_update', callback);
  }

  onMessageRead(callback: (data: any) => void) {
    this.socket?.on('message_read', callback);
  }

  onNotification(callback: (data: any) => void) {
    this.socket?.on('notification', callback);
  }

  // Remove listeners
  offNewMessage(callback: (data: any) => void) {
    this.socket?.off('new_message', callback);
  }

  offTypingStart(callback: (data: any) => void) {
    this.socket?.off('typing_start', callback);
  }

  offTypingStop(callback: (data: any) => void) {
    this.socket?.off('typing_stop', callback);
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const websocketService = new WebSocketService();
```

### Step 3: Update AuthContext/Store

Add WebSocket connection after successful login:

```typescript
// In your auth store or context
import { websocketService } from '@/services/websocketService';

// After successful login
const handleLogin = async (credentials) => {
  const response = await api.login(credentials);
  const token = response.access_token;

  // Store token
  localStorage.setItem('token', token);

  // Connect WebSocket
  websocketService.connect(token);
};

// On logout
const handleLogout = () => {
  websocketService.disconnect();
  localStorage.removeItem('token');
};
```

### Step 4: Update Chat Component

Update `vera_frontend/src/components/chat/ChatPanel.tsx`:

```typescript
import { useEffect, useState } from 'react';
import { websocketService } from '@/services/websocketService';

export function ChatPanel({ conversationId }) {
  const [messages, setMessages] = useState([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);

  useEffect(() => {
    // Join conversation
    websocketService.joinConversation(conversationId);

    // Listen for new messages
    const handleNewMessage = (data: any) => {
      setMessages((prev) => [...prev, data.message]);
    };

    // Listen for typing indicators
    const handleTypingStart = (data: any) => {
      setTypingUsers((prev) => [...prev, data.user_id]);
    };

    const handleTypingStop = (data: any) => {
      setTypingUsers((prev) => prev.filter((id) => id !== data.user_id));
    };

    websocketService.onNewMessage(handleNewMessage);
    websocketService.onTypingStart(handleTypingStart);
    websocketService.onTypingStop(handleTypingStop);

    return () => {
      // Cleanup
      websocketService.offNewMessage(handleNewMessage);
      websocketService.offTypingStart(handleTypingStart);
      websocketService.offTypingStop(handleTypingStop);
      websocketService.leaveConversation(conversationId);
    };
  }, [conversationId]);

  // Handle typing
  const handleTyping = () => {
    websocketService.startTyping(conversationId);

    // Auto-stop after 3 seconds
    setTimeout(() => {
      websocketService.stopTyping(conversationId);
    }, 3000);
  };

  // Render typing indicators
  const renderTypingIndicator = () => {
    if (typingUsers.length === 0) return null;

    return (
      <div className="typing-indicator">
        {typingUsers.length} {typingUsers.length === 1 ? 'person is' : 'people are'} typing...
      </div>
    );
  };

  return (
    <div>
      {/* Messages */}
      {messages.map((msg) => (
        <div key={msg.id}>{msg.content}</div>
      ))}

      {/* Typing indicator */}
      {renderTypingIndicator()}

      {/* Input */}
      <input
        type="text"
        onChange={handleTyping}
        placeholder="Type a message..."
      />
    </div>
  );
}
```

### Step 5: Add Real-Time Notifications

Update `vera_frontend/src/components/layout/Navbar.tsx`:

```typescript
useEffect(() => {
  const handleNotification = (data: any) => {
    // Show toast notification
    toast({
      title: data.notification.type,
      description: data.notification.message,
    });

    // Update notification count
    setNotificationCount((prev) => prev + 1);
  };

  websocketService.onNotification(handleNotification);

  return () => {
    websocketService.onNotification(() => {});
  };
}, []);
```

---

## 🧪 Testing the WebSocket Connection

### Backend Test

```bash
cd vera_backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Check logs for: `Socket.IO server started`

### Frontend Test

```bash
cd vera_frontend
npm install socket.io-client
npm run dev
```

Open browser console and check for: `WebSocket connected: <socket-id>`

### Manual Test with Socket.IO Client

```javascript
// In browser console
const socket = io('http://localhost:8000', {
  path: '/socket.io',
  auth: { token: 'your-jwt-token-here' },
});

socket.on('connect', () => console.log('Connected!'));
socket.emit('join_conversation', { conversation_id: 'some-uuid' }, (response) => {
  console.log('Joined:', response);
});
```

---

## 🎯 Features Enabled

### ✅ Real-Time Chat
- Instant message delivery
- No polling required
- Typing indicators
- Read receipts

### ✅ Presence System
- Online/offline status
- Last seen timestamps
- User activity tracking

### ✅ Notifications
- Real-time task assignments
- Message mentions
- System alerts

### ✅ Collaborative Features
- Multiple users in conversation
- Typing awareness
- Simultaneous updates

---

## 🔒 Security Considerations

1. **JWT Authentication**: All WebSocket connections require valid JWT
2. **Room Isolation**: Users can only join conversations they're part of
3. **CORS**: Configure `cors_allowed_origins` properly in production
4. **Rate Limiting**: Consider adding rate limits for typing events
5. **SSL/TLS**: Use `wss://` in production with proper certificates

---

## 📊 Monitoring

### Backend Logs

```python
# Enable Socket.IO logging
sio = socketio.AsyncServer(
    logger=True,
    engineio_logger=True,
)
```

### Frontend Debugging

```javascript
// Enable Socket.IO debugging
localStorage.debug = 'socket.io-client:*';
```

### Connection Status Endpoint

```bash
# Check active connections
curl http://localhost:8000/api/websocket/status
```

---

## 🚀 Next Steps

1. **Install Socket.IO client** in frontend
2. **Create WebSocket service** as shown above
3. **Update AuthContext** to connect on login
4. **Update ChatPanel** for real-time messages
5. **Add typing indicators** to ChatInput
6. **Test** with multiple browser tabs

### Quick Start Commands

```bash
# Backend (in vera_backend/)
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend (in vera_frontend/)
npm install socket.io-client
npm run dev

# Test
# Open http://localhost:3000 in two browser tabs
# Login as different users
# Start chatting!
```

---

## 📝 Files Created/Modified

### Backend:
- ✅ `app/services/websocket_service.py` - WebSocket service
- ✅ `app/routes/websocket.py` - Socket.IO routes
- ✅ `app/core/dependencies.py` - WebSocket auth helper
- ✅ `app/main.py` - Mounted Socket.IO app
- ✅ `app/routes/messaging.py` - Real-time message broadcasting
- ✅ `requirements.txt` - Added Socket.IO dependencies

### Frontend (To Create):
- `src/services/websocketService.ts` - WebSocket client
- Update `src/components/chat/ChatPanel.tsx` - Real-time messages
- Update `src/components/chat/ChatInput.tsx` - Typing indicators
- Update `src/contexts/AuthContext.tsx` or `src/stores/authStore.ts` - Connect/disconnect
- Update `src/components/layout/Navbar.tsx` - Real-time notifications

---

## 🐛 Troubleshooting

### Connection Refused
- Check backend is running: `curl http://localhost:8000/`
- Check Socket.IO endpoint: `curl http://localhost:8000/socket.io/`
- Verify CORS settings

### Authentication Failed
- Check JWT token format in browser localStorage
- Verify token expiration
- Check `jwt_secret_key` in backend `.env`

### Messages Not Appearing
- Check browser console for errors
- Verify conversation_id is correct UUID
- Check backend logs for Socket.IO events
- Ensure user joined conversation room

### Performance Issues
- Limit typing event frequency (debounce)
- Implement message pagination
- Consider WebSocket connection pooling for high traffic
