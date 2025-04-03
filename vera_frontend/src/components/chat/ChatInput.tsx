
import React, { useState } from 'react';
import { Mic, Send, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  placeholder?: string;
  showAttachButton?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  placeholder = "Message Vira...",
  showAttachButton = false
}) => {
  const [message, setMessage] = useState('');
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
    }
  };
  
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 bg-white p-3 rounded-lg border shadow-sm">
      {showAttachButton && (
        <Button type="button" variant="ghost" size="icon" className="h-9 w-9 shrink-0 rounded-full">
          <Plus className="h-5 w-5 text-gray-500" />
        </Button>
      )}
      
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="min-h-10 resize-none border-0 p-2 shadow-none focus-visible:ring-0"
        autoComplete="off"
      />
      
      <div className="flex shrink-0 gap-2">
        <Button type="button" variant="ghost" size="icon" className="h-9 w-9 rounded-full">
          <Mic className="h-5 w-5 text-gray-500" />
        </Button>
        
        <Button 
          type="submit" 
          size="icon" 
          className={`h-9 w-9 rounded-full ${message.trim() ? 'bg-vira-primary hover:bg-vira-primary/90' : 'bg-gray-200 text-gray-500'}`}
          disabled={!message.trim()}
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
};

export default ChatInput;
