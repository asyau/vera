import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { useSession } from '@/contexts/SessionContext';
import { ScrollArea } from '@/components/ui/scroll-area';
import { api } from '@/lib/api';

// Export Message interface so it can be used in other components
export interface Message {
  id: string;
  content: string;
  type: 'user' | 'ai' | 'employee';
  name?: string;
  timestamp: string;
}

const ChatPanel: React.FC = () => {
  const { currentSession, addMessageToCurrentSession } = useSession();
  const [isAiTyping, setIsAiTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Scroll to bottom whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages]);
  
  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      type: 'user',
      timestamp: new Date().toISOString(),
    };
    addMessageToCurrentSession(userMessage);
    
    // Get AI response
    setIsAiTyping(true);
    try {
      const result = await api.getCompletion(content);
      const aiMessage: Message = {
        id: result.id,
        content: result.content,
        type: result.type,
        name: result.name,
        timestamp: result.timestamp,
      };
      addMessageToCurrentSession(aiMessage);
    } catch (error) {
      console.error('Error getting AI response:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        type: 'ai',
        timestamp: new Date().toISOString(),
      };
      addMessageToCurrentSession(errorMessage);
    } finally {
      setIsAiTyping(false);
    }
  };

  if (!currentSession) {
    return (
      <div className="flex flex-col h-full rounded-lg bg-white shadow-sm border border-gray-100 items-center justify-center">
        <p className="text-gray-500">No chat session selected</p>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col h-full rounded-lg bg-white shadow-sm border border-gray-100">
      <div className="p-4 border-b border-gray-100">
        <h2 className="text-lg font-semibold text-vira-dark">
          <span className="text-vira-primary">Vira</span> — AI Chat Assistant
        </h2>
      </div>
      
      <ScrollArea className="flex-1 bg-gray-50">
        <div className="p-4 space-y-4">
          {currentSession.messages.map((message) => (
            <ChatMessage
              key={message.id}
              content={message.content}
              type={message.type}
              name={message.name}
              timestamp={message.timestamp}
            />
          ))}
          
          {isAiTyping && (
            <div className="flex items-center space-x-2 p-4">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      
      <div className="p-3 border-t border-gray-100 bg-white sticky bottom-0">
        <ChatInput onSendMessage={handleSendMessage} />
      </div>
    </div>
  );
};

export default ChatPanel;
