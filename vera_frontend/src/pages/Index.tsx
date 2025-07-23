import React, { useState } from 'react';
import Navbar from '@/components/layout/Navbar';
import ChatPanel from '@/components/chat/ChatPanel';
import TaskTable from '@/components/tasks/TaskTable';
import TriChatPanel from '@/components/trichat/TriChatPanel';
import ChatSidebar from '@/components/layout/ChatSidebar';
import ViewNavigation from '@/components/layout/ViewNavigation';
import { SessionProvider, useSession } from '@/contexts/SessionContext';

// Type for view modes
type ViewMode = 'chat' | 'tasks' | 'trichat';

// Layout wrapper component
const AppLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-50 via-blue-50/30 to-indigo-50/30 overflow-hidden">
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
      {/* Only show sidebar in chat mode */}
      {viewMode === 'chat' && (
        <ChatSidebar 
          sessions={sessions.map(s => ({ 
            ...s, 
            isActive: s.id === currentSession?.id 
          }))}
          onSessionSelect={handleSessionSelect}
          onNewSession={handleNewSession}
        />
      )}
      
      <div className="flex flex-col flex-1 h-full overflow-hidden animate-in fade-in-0 slide-in-from-right-2 duration-300">
        <ViewNavigation
          viewMode={viewMode}
          onViewModeChange={(mode) => {
            setViewMode(mode);
            if (mode === 'chat') {
              setShowTaskPanel(false);
            }
          }}
          showTaskPanel={showTaskPanel}
          onToggleTaskPanel={toggleTaskPanel}
        />
        
        <div className="flex flex-1 overflow-hidden">
          {/* Chat area - always shown in chat mode */}
          {viewMode === 'chat' && (
            <div className={`${showTaskPanel ? 'w-1/2' : 'w-full'} h-full overflow-hidden`}>
              <div className="h-full">
                <ChatPanel />
              </div>
            </div>
          )}
          
          {/* Task panel - shown in chat mode when toggled */}
          {viewMode === 'chat' && showTaskPanel && (
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
