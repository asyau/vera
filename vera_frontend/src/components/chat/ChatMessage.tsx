
import React from 'react';
import { cn } from '@/lib/utils';

type MessageType = 'user' | 'ai' | 'employee';

interface ChatMessageProps {
  content: string;
  type: MessageType;
  name?: string;
  timestamp?: string;
  isTyping?: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  content,
  type,
  name,
  timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  isTyping = false
}) => {
  const bubbleClass = {
    'user': 'user-bubble',
    'ai': 'ai-bubble',
    'employee': 'employee-bubble'
  }[type];

  const showName = type !== 'user' && name;

  return (
    <div className={cn("flex flex-col", type === 'user' ? 'items-end' : 'items-start')}>
      {showName && (
        <div className="text-xs text-gray-500 mb-1 ml-3">{name}</div>
      )}
      <div className={bubbleClass}>
        {isTyping ? (
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-current rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-current rounded-full animate-pulse delay-75"></div>
            <div className="w-2 h-2 bg-current rounded-full animate-pulse delay-150"></div>
          </div>
        ) : (
          <div className="whitespace-pre-wrap">{content}</div>
        )}
      </div>
      <div className="text-xs text-gray-400 mt-1 mx-2">{timestamp}</div>
    </div>
  );
};

export default ChatMessage;
