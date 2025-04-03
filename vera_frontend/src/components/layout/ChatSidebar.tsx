
import React from 'react';
import { Plus, Search, History, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ChatSession {
  id: string;
  title: string;
  date: string;
  isActive?: boolean;
}

interface ChatSidebarProps {
  sessions: ChatSession[];
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
  className?: string;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  onSessionSelect,
  onNewSession,
  className
}) => {
  return (
    <div className={`w-64 h-full flex flex-col bg-white border-r border-gray-200 overflow-hidden ${className}`}>
      <div className="p-4 flex-shrink-0">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button 
              onClick={onNewSession}
              className="w-full bg-vira-primary hover:bg-vira-primary/90 mb-4"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Chat
            </Button>
          </TooltipTrigger>
          <TooltipContent>Start a new conversation</TooltipContent>
        </Tooltip>
        
        <div className="relative mb-4">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
          <Input 
            placeholder="Search chats..." 
            className="pl-8 bg-gray-50 border-gray-200"
          />
        </div>
      </div>
      
      <Separator className="flex-shrink-0" />
      
      <ScrollArea className="flex-1 overflow-y-auto">
        <div className="py-2">
          <div className="px-4 py-2 flex items-center">
            <History className="h-4 w-4 mr-2 text-gray-500" />
            <span className="text-xs font-medium text-gray-500">Recent Chats</span>
          </div>
          
          {sessions.length > 0 ? (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => onSessionSelect(session.id)}
                className={`w-full px-4 py-3 text-left transition-colors hover:bg-gray-100 ${
                  session.isActive ? 'bg-gray-100' : ''
                }`}
              >
                <div className="flex items-center">
                  <MessageSquare className="h-4 w-4 mr-2 text-gray-500" />
                  <div className="flex flex-col">
                    <span className="text-sm font-medium truncate">{session.title}</span>
                    <span className="text-xs text-gray-500">{session.date}</span>
                  </div>
                </div>
              </button>
            ))
          ) : (
            <div className="px-4 py-3 text-sm text-gray-500 text-center">
              No recent chats
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

export default ChatSidebar;
