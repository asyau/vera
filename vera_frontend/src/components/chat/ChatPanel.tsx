
import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { useSession } from '@/contexts/SessionContext';
import { ScrollArea } from '@/components/ui/scroll-area';

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
  
  // Mock AI response
  const simulateAiResponse = (userMessage: string) => {
    setIsAiTyping(true);
    
    // Sample responses based on user input
    const responses = [
      "I'll handle that for you right away.",
      "I've made a note of that request. Would you like me to schedule it?",
      "I've added that to your task list. When would you like it completed by?",
      "Let me look into that for you. I'll get back to you shortly with more information.",
      "I can help with that. Would you like me to assign this to someone on your team?"
    ];
    
    // Generate a simple response based on message content
    let responseText = '';
    if (userMessage.toLowerCase().includes('meeting')) {
      responseText = "I'll schedule that meeting for you. What time works best?";
    } else if (userMessage.toLowerCase().includes('email')) {
      responseText = "I can draft that email. Who would you like it sent to?";
    } else if (userMessage.toLowerCase().includes('task')) {
      responseText = "I've created that task. Would you like me to assign it to someone specific?";
    } else {
      // Random response if no keywords match
      responseText = responses[Math.floor(Math.random() * responses.length)];
    }
    
    // Simulate typing delay
    setTimeout(() => {
      setIsAiTyping(false);
      const aiMessage: Message = {
        id: Date.now().toString(),
        content: responseText,
        type: 'ai',
        name: 'Vira',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      addMessageToCurrentSession(aiMessage);
    }, 1500);
  };
  
  const handleSendMessage = (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      type: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    
    addMessageToCurrentSession(userMessage);
    
    // Simulate AI response
    simulateAiResponse(content);
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
            <ChatMessage
              content=""
              type="ai"
              name="Vira"
              isTyping={true}
            />
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
