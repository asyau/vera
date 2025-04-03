import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from '../chat/ChatMessage';
import { AtSign, Mic } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface TriChatMessage {
  id: string;
  content: string;
  type: 'user' | 'ai' | 'employee';
  name: string;
  timestamp: string;
}

const TriChatPanel: React.FC = () => {
  const [messages, setMessages] = useState<TriChatMessage[]>([
    {
      id: '1',
      content: "Good morning team. Let's discuss the Q2 marketing strategy. Sarah, could you share the latest campaign metrics?",
      type: 'user',
      name: 'John (Supervisor)',
      timestamp: '9:30 AM'
    },
    {
      id: '2',
      content: "Of course! Our Q1 campaign had a 24% conversion rate. For Q2, I'm suggesting we focus more on social media since those channels performed best.",
      type: 'employee',
      name: 'Sarah (Employee)',
      timestamp: '9:32 AM'
    },
    {
      id: '3',
      content: "Based on the data Sarah shared, we should indeed prioritize Instagram and TikTok. I've analyzed the engagement metrics and found that video content had 3.2x higher conversion rates than static images.",
      type: 'ai',
      name: 'Vira (AI)',
      timestamp: '9:33 AM'
    },
    {
      id: '4',
      content: "Great insight, Vira. Sarah, can you work with the creative team to shift our content strategy toward more video content?",
      type: 'user',
      name: 'John (Supervisor)',
      timestamp: '9:35 AM'
    },
    {
      id: '5',
      content: "Yes, I'll set up a meeting with them today and get back to you with a revised plan by Friday.",
      type: 'employee',
      name: 'Sarah (Employee)',
      timestamp: '9:36 AM'
    }
  ]);
  const [newMessage, setNewMessage] = useState('');
  const [activeRole, setActiveRole] = useState<'user' | 'employee'>('user');
  const [aiThinking, setAiThinking] = useState(false);
  const [summary, setSummary] = useState<string>("John asked Sarah about Q2 marketing strategy. Sarah reported Q1 had 24% conversion rate and suggested focusing on social media for Q2. Vira analyzed the data and recommended prioritizing Instagram and TikTok, noting video content had 3.2x higher conversion rates than static images. John agreed and requested Sarah to work with the creative team on more video content, which Sarah agreed to complete by Friday.");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;
    
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const messageId = Date.now().toString();
    
    // Determine the sender's name based on active role
    const name = activeRole === 'user' ? 'John (Supervisor)' : 'Sarah (Employee)';
    
    // Add user/employee message
    const userMessage: TriChatMessage = {
      id: messageId,
      content: newMessage,
      type: activeRole,
      name,
      timestamp: now
    };
    
    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    
    // Check if @AI is mentioned in the message
    if (newMessage.includes('@AI') || newMessage.includes('@ai')) {
      setAiThinking(true);
      
      try {
        // Send message to API to get AI response
        const response = await fetch('http://localhost:8000/api/ai/trichat-respond', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            conversation_id: 'trichat-1', // This would be dynamic in a real app
            messages: messages.map(msg => ({
              type: msg.type,
              name: msg.name,
              content: msg.content
            })),
            new_message: {
              type: activeRole,
              name,
              content: newMessage
            },
            is_at_ai: true
          }),
        });
        
        if (!response.ok) {
          throw new Error('Failed to get AI response');
        }
        
        const aiResponseData = await response.json();
        
        // Add AI response to messages
        const aiMessage: TriChatMessage = {
          id: Date.now().toString(),
          content: aiResponseData.content,
          type: 'ai',
          name: 'Vira (AI)',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        
        setMessages(prev => [...prev, aiMessage]);
        
        // Update the summary
        updateSummary([...messages, userMessage, aiMessage]);
      } catch (error) {
        console.error('Error getting AI response:', error);
        // Add a fallback AI response in case of error
        const aiMessage: TriChatMessage = {
          id: Date.now().toString(),
          content: "I'm having trouble connecting to my systems. Could you try again later?",
          type: 'ai',
          name: 'Vira (AI)',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        
        setMessages(prev => [...prev, aiMessage]);
      } finally {
        setAiThinking(false);
      }
    } else {
      // If no @AI, just update the summary with the new user message
      updateSummary([...messages, userMessage]);
    }
  };
  
  const updateSummary = async (currentMessages: TriChatMessage[]) => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: currentMessages.map(msg => ({
            type: msg.type,
            name: msg.name,
            content: msg.content
          })),
          max_tokens: 200
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to get summary');
      }
      
      const summaryText = await response.text();
      setSummary(summaryText);
    } catch (error) {
      console.error('Error getting summary:', error);
      // Keep existing summary in case of error
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  const toggleRole = () => {
    setActiveRole(current => current === 'user' ? 'employee' : 'user');
  };
  
  return (
    <div className="flex flex-col h-full rounded-lg bg-white shadow-sm border border-gray-100">
      <div className="p-4 border-b border-gray-100">
        <h2 className="text-lg font-semibold text-vira-dark">
          <span className="text-vira-primary">Tri</span>Chat Prototype
        </h2>
        <p className="text-sm text-gray-500">
          Three-way conversation between Supervisor, Employee, and AI
        </p>
      </div>
      
      <div className="flex gap-2 p-3 border-b border-gray-100 items-center">
        <span className="text-sm text-gray-600">Current Role:</span>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={toggleRole}
          className={activeRole === 'user' ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'}
        >
          {activeRole === 'user' ? 'John (Supervisor)' : 'Sarah (Employee)'}
        </Button>
      </div>
      
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4 bg-gray-50">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              content={message.content}
              type={message.type}
              name={message.name}
              timestamp={message.timestamp}
            />
          ))}
          
          {aiThinking && (
            <ChatMessage
              content=""
              type="ai"
              name="Vira (AI)"
              isTyping={true}
            />
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      
      <Card className="m-3 border border-vira-primary/20 bg-vira-light/30">
        <CardHeader className="py-3">
          <CardTitle className="text-sm font-medium text-vira-primary">AI Summary of Discussion</CardTitle>
        </CardHeader>
        <CardContent className="py-2 text-sm text-gray-700">
          <p>{summary}</p>
        </CardContent>
      </Card>
      
      <div className="p-3 border-t border-gray-100">
        <div className="flex items-end gap-2 bg-white p-3 rounded-lg border shadow-sm">
          <Textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="min-h-10 resize-none border-0 p-2 shadow-none focus-visible:ring-0"
            autoComplete="off"
          />
          
          <div className="flex shrink-0 gap-2">
            <Button variant="outline" size="icon" className="h-9 w-9 rounded-full">
              <Mic className="h-5 w-5 text-gray-500" />
            </Button>
            
            <Button 
              variant="outline" 
              size="icon" 
              className="h-9 w-9 rounded-full"
              onClick={() => setNewMessage(prev => prev + ' @AI ')}
              title="Mention AI"
            >
              <AtSign className="h-5 w-5 text-vira-primary" />
            </Button>
            
            <Button 
              onClick={handleSendMessage}
              disabled={!newMessage.trim() || aiThinking}
              size="icon" 
              className={`h-9 w-9 rounded-full ${
                newMessage.trim() && !aiThinking ? 'bg-vira-primary hover:bg-vira-primary/90' : 'bg-gray-200 text-gray-500'
              }`}
            >
              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TriChatPanel;
