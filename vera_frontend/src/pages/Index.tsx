import React, { useState } from 'react';
import Navbar from '@/components/layout/Navbar';
import ChatPanel from '@/components/chat/ChatPanel';
import TaskTable from '@/components/tasks/TaskTable';
import TriChatPanel from '@/components/trichat/TriChatPanel';
import ChatSidebar from '@/components/layout/ChatSidebar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Clipboard, MessageSquare, KanbanSquare, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SessionProvider, useSession } from '@/contexts/SessionContext';
import { Chat } from '@/components/Chat';

// Type for view modes
type ViewMode = 'chat' | 'chat-tasks' | 'tasks' | 'trichat';

// Layout wrapper component
const AppLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="h-screen flex flex-col bg-gray-50 overflow-hidden">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        {children}
      </div>
    </div>
  );
};

// Main content component
const MainContent = () => {
  const [showBriefing, setShowBriefing] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('chat');
  const [showTaskPanel, setShowTaskPanel] = useState(false);
  const { sessions, currentSession, setCurrentSession, createNewSession } = useSession();
  
  const toggleTaskPanel = () => {
    setShowTaskPanel(prev => !prev);
  };
  
  const handleSessionSelect = (sessionId: string) => {
    setCurrentSession(sessionId);
  };
  
  const handleNewSession = () => {
    createNewSession();
  };
  
  return (
    <div className="flex w-full h-full overflow-hidden">
      {/* Only show sidebar in chat and chat-tasks modes */}
      {(viewMode === 'chat' || viewMode === 'chat-tasks') && (
        <ChatSidebar 
          sessions={sessions.map(s => ({ 
            ...s, 
            isActive: s.id === currentSession?.id 
          }))}
          onSessionSelect={handleSessionSelect}
          onNewSession={handleNewSession}
        />
      )}
      
      <div className="flex flex-col flex-1 h-full overflow-hidden">
        <div className="flex p-2 bg-white border-b border-gray-200 items-center justify-between">
          <div className="flex space-x-2">
            <Button 
              variant={viewMode === 'chat' ? "default" : "outline"}
              size="sm"
              onClick={() => setViewMode('chat')}
              className={viewMode === 'chat' ? "bg-vira-primary hover:bg-vira-primary/90" : ""}
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Chat Focus
            </Button>
            <Button 
              variant={viewMode === 'chat-tasks' ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setViewMode('chat-tasks');
                setShowTaskPanel(true);
              }}
              className={viewMode === 'chat-tasks' ? "bg-vira-primary hover:bg-vira-primary/90" : ""}
            >
              <Clipboard className="h-4 w-4 mr-2" />
              Chat + Tasks
            </Button>
            <Button 
              variant={viewMode === 'tasks' ? "default" : "outline"}
              size="sm"
              onClick={() => setViewMode('tasks')}
              className={viewMode === 'tasks' ? "bg-vira-primary hover:bg-vira-primary/90" : ""}
            >
              <KanbanSquare className="h-4 w-4 mr-2" />
              Tasks Only
            </Button>
            <Button 
              variant={viewMode === 'trichat' ? "default" : "outline"}
              size="sm"
              onClick={() => setViewMode('trichat')}
              className={viewMode === 'trichat' ? "bg-vira-primary hover:bg-vira-primary/90" : ""}
            >
              <Users className="h-4 w-4 mr-2" />
              TriChat
            </Button>
          </div>
          
          {/* Only show toggle button in chat-tasks mode */}
          {viewMode === 'chat-tasks' && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={toggleTaskPanel}
              className={`${showTaskPanel ? 'bg-gray-100' : ''}`}
            >
              <Clipboard className="h-4 w-4 mr-2" />
              Toggle Tasks
            </Button>
          )}
        </div>
        
        <div className="flex flex-1 overflow-hidden">
          {/* Chat area - shown in chat and chat-tasks modes */}
          {(viewMode === 'chat' || (viewMode === 'chat-tasks' && showTaskPanel)) && (
            <div className={`${viewMode === 'chat-tasks' && showTaskPanel ? 'w-1/2' : 'w-full'} h-full overflow-hidden`}>
              <div className="h-full">
                <ChatPanel />
              </div>
            </div>
          )}
          
          {/* Task panel - shown in chat-tasks mode when toggled */}
          {viewMode === 'chat-tasks' && showTaskPanel && (
            <div className="w-1/2 h-full border-l border-gray-200 overflow-hidden">
              <TaskTable />
            </div>
          )}
          
          {/* Full-screen task view - shown in tasks mode */}
          {viewMode === 'tasks' && (
            <div className="w-full h-full overflow-hidden">
              <TaskTable fullScreen={true} />
            </div>
          )}
          
          {/* TriChat view - shown in trichat mode */}
          {viewMode === 'trichat' && (
            <div className="w-full h-full overflow-hidden">
              <TriChatPanel />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const Index = () => {
  return (
    <SessionProvider>
      <AppLayout>
        <MainContent />
      </AppLayout>
    </SessionProvider>
  );
};

export default Index;
