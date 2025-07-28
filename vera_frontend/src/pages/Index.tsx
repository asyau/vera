import React, { useState } from 'react';
import Navbar from '@/components/layout/Navbar';
import ChatPanel from '@/components/chat/ChatPanel';
import TaskTable from '@/components/tasks/TaskTable';
import TeamChatPanel from '@/components/messaging/TeamChatPanel';
import CollapsibleSidebar from '@/components/layout/CollapsibleSidebar';
import TeamDashboard from '@/components/dashboard/TeamDashboard';
import { SessionProvider, useSession } from '@/contexts/SessionContext';
import { useAuth } from '@/contexts/AuthContext';

// Type for view modes
type ViewMode = 'chat' | 'tasks' | 'messaging' | 'team-dashboard';

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
  const [viewMode, setViewMode] = useState<ViewMode>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    const saved = localStorage.getItem('sidebarOpen');
    return saved ? JSON.parse(saved) : true;
  });
  const { sessions, currentSession, setCurrentSession, createNewSession } = useSession();
  const { hasRole } = useAuth();
  const isSupervisor = hasRole('supervisor');
  
  const handleSessionSelect = (sessionId: string) => {
    setCurrentSession(sessionId);
  };
  
  const handleNewSession = () => {
    createNewSession();
  };
  
  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode);
  };
  
  const handleSidebarToggle = () => {
    const newState = !sidebarOpen;
    setSidebarOpen(newState);
    localStorage.setItem('sidebarOpen', JSON.stringify(newState));
  };
  
  return (
    <div className="flex w-full h-full overflow-hidden">
      {/* Collapsible Sidebar */}
      <CollapsibleSidebar
        isOpen={sidebarOpen}
        onToggle={handleSidebarToggle}
        viewMode={viewMode}
        onViewModeChange={handleViewModeChange}
        chatSessions={sessions.map(s => ({ 
          ...s, 
          isActive: s.id === currentSession?.id 
        }))}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
        isSupervisor={isSupervisor}
      />
      
      {/* Main Content Area */}
      <div className="flex-1 h-full overflow-hidden">
        {/* Chat view */}
        {viewMode === 'chat' && (
          <div className="h-full">
            <ChatPanel />
          </div>
        )}
        
        {/* Tasks view */}
        {viewMode === 'tasks' && (
          <div className="h-full">
            <TaskTable fullScreen={true} />
          </div>
        )}
        
        {/* Messaging view */}
        {viewMode === 'messaging' && (
          <div className="h-full">
            <TeamChatPanel />
          </div>
        )}

        {/* Team Dashboard view */}
        {viewMode === 'team-dashboard' && (
          <div className="h-full">
            <TeamDashboard />
          </div>
        )}
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
