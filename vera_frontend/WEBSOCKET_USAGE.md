# WebSocket Real-Time Features - Frontend Implementation

## ✅ Implementation Complete

The WebSocket frontend has been fully integrated with the Vira platform. This guide shows you how to use the real-time features.

---

## 🎯 What's Implemented

### 1. ✅ WebSocket Service (`src/services/websocketService.ts`)
- Automatic connection/disconnection based on authentication
- JWT-based authentication
- Reconnection logic with exponential backoff
- Event listeners for all real-time features

### 2. ✅ Authentication Integration (`src/stores/authStore.ts`)
- Auto-connect on login/signup
- Auto-disconnect on logout
- Auto-reconnect on page refresh (if authenticated)

### 3. ✅ Custom Hook (`src/hooks/useWebSocketMessaging.ts`)
- Easy-to-use React hook for messaging features
- Automatic conversation join/leave
- Typing indicators management
- Message state management

### 4. ✅ Chat Input (`src/components/chat/ChatInput.tsx`)
- Typing indicator callbacks
- Automatic typing start/stop on user input

### 5. ✅ Real-Time Notifications (`src/components/layout/Navbar.tsx`)
- Toast notifications for real-time events
- Notification badge counter
- WebSocket event subscription

---

## 📚 Usage Examples

### Using WebSocket in Your Components

#### Example 1: Real-Time Chat with Typing Indicators

```typescript
import React, { useState, useEffect } from 'react';
import { useWebSocketMessaging } from '@/hooks/useWebSocketMessaging';
import ChatInput from '@/components/chat/ChatInput';

export function ChatComponent({ conversationId }: { conversationId: string }) {
  const {
    messages,
    typingUsers,
    isConnected,
    sendTypingIndicator,
    stopTyping,
    addMessage,
  } = useWebSocketMessaging(conversationId);

  const handleSendMessage = async (content: string) => {
    // Send message via API
    const response = await api.sendMessage(conversationId, content);

    // Message will be received via WebSocket automatically
    // No need to manually add it to state
  };

  return (
    <div>
      {/* Connection status */}
      {!isConnected && (
        <div className="bg-yellow-100 text-yellow-800 p-2">
          Connecting to real-time chat...
        </div>
      )}

      {/* Messages */}
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id}>
            {msg.content}
          </div>
        ))}
      </div>

      {/* Typing indicators */}
      {typingUsers.length > 0 && (
        <div className="typing-indicator">
          {typingUsers.map((u) => u.user_name || u.user_id).join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
        </div>
      )}

      {/* Chat input with typing indicators */}
      <ChatInput
        onSendMessage={handleSendMessage}
        onTypingStart={sendTypingIndicator}
        onTypingStop={stopTyping}
      />
    </div>
  );
}
```

#### Example 2: Direct WebSocket Service Usage

```typescript
import { websocketService } from '@/services/websocketService';
import { useEffect } from 'react';

export function DirectWebSocketExample() {
  useEffect(() => {
    // Join conversation
    const conversationId = 'some-uuid';

    websocketService.joinConversation(conversationId)
      .then(() => console.log('Joined conversation'))
      .catch((error) => console.error('Failed to join:', error));

    // Listen for new messages
    const handleNewMessage = (data) => {
      console.log('New message:', data.message);
    };

    websocketService.onNewMessage(handleNewMessage);

    // Cleanup
    return () => {
      websocketService.offNewMessage(handleNewMessage);
      websocketService.leaveConversation(conversationId);
    };
  }, []);

  return <div>WebSocket Example</div>;
}
```

#### Example 3: Presence Tracking

```typescript
import { websocketService } from '@/services/websocketService';
import { useState, useEffect } from 'react';

export function PresenceExample() {
  const [onlineUsers, setOnlineUsers] = useState<Set<string>>(new Set());

  useEffect(() => {
    const handlePresence = (data) => {
      setOnlineUsers((prev) => {
        const updated = new Set(prev);
        if (data.status === 'online') {
          updated.add(data.user_id);
        } else {
          updated.delete(data.user_id);
        }
        return updated;
      });
    };

    websocketService.onPresenceUpdate(handlePresence);

    return () => {
      websocketService.offPresenceUpdate(handlePresence);
    };
  }, []);

  return (
    <div>
      <h3>Online Users: {onlineUsers.size}</h3>
      <ul>
        {Array.from(onlineUsers).map((userId) => (
          <li key={userId}>{userId}</li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 🔌 Available WebSocket Events

### Outgoing Events (Client → Server)

| Event | Description | Parameters |
|-------|-------------|------------|
| `join_conversation` | Join a conversation room | `{ conversation_id: string }` |
| `leave_conversation` | Leave a conversation room | `{ conversation_id: string }` |
| `typing_start` | Indicate user started typing | `{ conversation_id: string }` |
| `typing_stop` | Indicate user stopped typing | `{ conversation_id: string }` |
| `mark_read` | Mark message as read | `{ conversation_id: string, message_id: string }` |
| `get_online_users` | Get list of online users | `{ conversation_id: string }` |

### Incoming Events (Server → Client)

| Event | Description | Data Structure |
|-------|-------------|----------------|
| `new_message` | New message in conversation | `{ message: { id, content, sender_id, ... } }` |
| `typing_start` | User started typing | `{ user_id, conversation_id, user_name? }` |
| `typing_stop` | User stopped typing | `{ user_id, conversation_id }` |
| `presence_update` | User online/offline status | `{ user_id, status, timestamp }` |
| `message_read` | Message read receipt | `{ message_id, conversation_id, user_id, read_at }` |
| `notification` | Real-time notification | `{ notification: { id, type, title, message, ... } }` |

---

## 🎨 Styling Typing Indicators

```tsx
// Simple typing indicator
{typingUsers.length > 0 && (
  <div className="flex items-center space-x-2 p-3 text-sm text-gray-500">
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
    </div>
    <span>
      {typingUsers.length} {typingUsers.length === 1 ? 'person is' : 'people are'} typing...
    </span>
  </div>
)}
```

---

## 🧪 Testing WebSocket Features

### Manual Testing

1. **Start Backend**:
```bash
cd vera_backend
python -m uvicorn app.main:app --reload
```

2. **Start Frontend**:
```bash
cd vera_frontend
npm run dev
```

3. **Test Real-Time Chat**:
   - Open http://localhost:5173 in two different browser windows
   - Log in as different users
   - Start a conversation
   - Type messages and observe:
     - Real-time message delivery
     - Typing indicators
     - Read receipts

4. **Test Notifications**:
   - Trigger a notification from the backend
   - Observe toast notification in navbar
   - Check notification counter badge

### Debugging

Enable WebSocket debugging in browser console:

```javascript
// In browser console
localStorage.debug = 'socket.io-client:*';

// Reload page to see detailed WebSocket logs
```

---

## 🔧 Configuration

### Environment Variables

The WebSocket service connects to `http://localhost:8000` by default. To change this:

Edit `src/services/websocketService.ts`:

```typescript
private baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

Add to `.env`:

```bash
VITE_API_URL=https://your-production-api.com
```

---

## 🐛 Troubleshooting

### WebSocket Not Connecting

1. **Check if backend is running**:
```bash
curl http://localhost:8000/socket.io/
```

2. **Check authentication**:
   - Verify JWT token is stored in localStorage
   - Check browser console for connection errors
   - Ensure token is not expired

3. **Check browser console**:
   - Look for "WebSocket connected" message
   - Check for error messages

### Messages Not Appearing

1. **Verify conversation join**:
```javascript
// In browser console
websocketService.isConnected() // Should return true
```

2. **Check event listeners**:
   - Ensure `onNewMessage` callback is registered
   - Verify conversation ID is correct
   - Check backend logs for message broadcast

### Typing Indicators Not Working

1. **Verify callbacks are provided**:
```typescript
<ChatInput
  onTypingStart={sendTypingIndicator}
  onTypingStop={stopTyping}
/>
```

2. **Check WebSocket events**:
   - Enable debug logging
   - Verify `typing_start` and `typing_stop` events are sent

---

## 📈 Performance Considerations

### Debouncing Typing Indicators

The typing indicator automatically stops after 3 seconds. To change this:

Edit `src/hooks/useWebSocketMessaging.ts`:

```typescript
// Change timeout from 3000ms to desired value
typingTimeoutRef.current = setTimeout(() => {
  websocketService.stopTyping(conversationId);
}, 3000); // ← Change this value
```

### Memory Management

- Event listeners are automatically cleaned up on component unmount
- WebSocket disconnects on logout
- Reconnection is handled automatically

---

## 🚀 Next Steps

### Recommended Enhancements

1. **Message Pagination**:
   - Load historical messages when joining conversation
   - Implement infinite scroll for message history

2. **File Attachments**:
   - Add support for file uploads in real-time
   - Show upload progress

3. **Voice/Video Calls**:
   - Integrate WebRTC for voice/video
   - Use WebSocket for signaling

4. **Advanced Presence**:
   - Show "last seen" timestamps
   - Display user activity status (active, away, busy)

5. **Push Notifications**:
   - Integrate service workers for push notifications
   - Show notifications even when tab is not active

---

## 📝 API Integration

### Sending Messages

When sending a message via the API, the WebSocket will automatically receive it:

```typescript
// 1. Send message via API
const response = await fetch('/api/messaging/conversations/${conversationId}/messages', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    content: 'Hello!',
    type: 'text',
  }),
});

// 2. WebSocket automatically receives the message
// No need to manually add to state!
```

The backend broadcasts the message to all conversation participants via WebSocket, so you'll receive it in the `onNewMessage` callback.

---

## ✅ Implementation Checklist

- [x] WebSocket service created
- [x] Auth store integration
- [x] Custom messaging hook
- [x] Chat input typing indicators
- [x] Real-time notifications
- [x] Error handling
- [x] Reconnection logic
- [x] Event cleanup
- [ ] Message pagination (future)
- [ ] Presence UI components (future)
- [ ] Push notifications (future)

---

## 🎉 Summary

The WebSocket implementation is now complete and ready to use! You have:

- ✅ Real-time message delivery
- ✅ Typing indicators
- ✅ Online/offline presence tracking
- ✅ Real-time notifications
- ✅ Automatic connection management
- ✅ Read receipts support

Simply use the `useWebSocketMessaging` hook in your chat components or interact directly with the `websocketService` for custom use cases.

**Happy coding! 🚀**
