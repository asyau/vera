import React, { useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  CheckSquare,
  Users,
  Plus,
  History,
  Shield
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface ChatSession {
  id: string;
  title: string;
  date: string;
  isActive?: boolean;
}

interface CollapsibleSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  viewMode: 'chat' | 'tasks' | 'messaging' | 'team-dashboard';
  onViewModeChange: (mode: 'chat' | 'tasks' | 'messaging' | 'team-dashboard') => void;
  chatSessions: ChatSession[];
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
  isSupervisor?: boolean;
}

const CollapsibleSidebar: React.FC<CollapsibleSidebarProps> = ({
  isOpen,
  onToggle,
  viewMode,
  onViewModeChange,
  chatSessions,
  onSessionSelect,
  onNewSession,
  isSupervisor = false
}) => {
  const [activeAccordion, setActiveAccordion] = useState<string>('chat');

  const handleViewModeChange = (mode: 'chat' | 'tasks' | 'messaging' | 'team-dashboard') => {
    onViewModeChange(mode);
    setActiveAccordion(mode);
  };

  return (
    <div className={`h-full flex flex-col bg-white border-r border-gray-200 transition-all duration-300 ease-in-out ${
      isOpen ? 'w-64' : 'w-12'
    }`}>
      {/* Toggle Button */}
      <div className="p-2 border-b border-gray-200">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggle}
              className="w-full h-8"
            >
              {isOpen ? (
                <ChevronLeft className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            {isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          </TooltipContent>
        </Tooltip>
      </div>

      {isOpen ? (
        <>
          {/* New Chat Button */}
          <div className="p-4 border-b border-gray-200">
            <Button
              onClick={onNewSession}
              className="w-full bg-vira-primary hover:bg-vira-primary/90"
              size="sm"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Chat
            </Button>
          </div>

          {/* Accordion Navigation */}
          <div className="flex-1 overflow-hidden">
            <Accordion
              type="single"
              collapsible
              value={activeAccordion}
              onValueChange={setActiveAccordion}
              className="h-full"
            >
              {/* Chat Section */}
              <AccordionItem value="chat" className="border-none">
                <AccordionTrigger
                  className={`px-3 py-2 hover:bg-gray-50 ${
                    viewMode === 'chat' ? 'bg-blue-50 text-blue-700' : ''
                  }`}
                  onClick={() => handleViewModeChange('chat')}
                >
                  <div className="flex items-center space-x-2">
                    <MessageSquare className="h-4 w-4" />
                    <span className="text-sm font-medium">Chat</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-0">
                  <div className="py-3">
                    <div className="px-4 pb-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-gray-700">Recent Chats</span>
                        <History className="h-4 w-4 text-gray-400" />
                      </div>
                    </div>

                    <ScrollArea className="h-64">
                      {chatSessions.length > 0 ? (
                        <div className="space-y-1 px-2">
                          {chatSessions.map((session) => (
                            <button
                              key={session.id}
                              onClick={() => onSessionSelect(session.id)}
                              className={`w-full px-4 py-3 text-left transition-all duration-200 hover:bg-gray-50 rounded-lg ${
                                session.isActive
                                  ? 'bg-blue-50 border-l-4 border-blue-500'
                                  : 'hover:border-l-4 hover:border-gray-200'
                              }`}
                            >
                              <div className="flex items-start space-x-3">
                                <div className={`flex-shrink-0 w-2 h-2 rounded-full mt-2 ${
                                  session.isActive ? 'bg-blue-500' : 'bg-gray-300'
                                }`} />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between">
                                    <p className={`text-sm font-medium truncate ${
                                      session.isActive ? 'text-blue-700' : 'text-gray-900'
                                    }`}>
                                      {session.title}
                                    </p>
                                  </div>
                                  <p className="text-xs text-gray-500 mt-1">
                                    {session.date}
                                  </p>
                                </div>
                              </div>
                            </button>
                          ))}
                        </div>
                      ) : (
                        <div className="px-4 py-6 text-center">
                          <MessageSquare className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                          <p className="text-sm text-gray-500">No recent chats</p>
                          <p className="text-xs text-gray-400 mt-1">Start a new conversation to get started</p>
                        </div>
                      )}
                    </ScrollArea>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Tasks Section */}
              <AccordionItem value="tasks" className="border-none">
                <AccordionTrigger
                  className={`px-3 py-2 hover:bg-gray-50 ${
                    viewMode === 'tasks' ? 'bg-blue-50 text-blue-700' : ''
                  }`}
                  onClick={() => handleViewModeChange('tasks')}
                >
                  <div className="flex items-center space-x-2">
                    <CheckSquare className="h-4 w-4" />
                    <span className="text-sm font-medium">Tasks</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-0">
                  <div className="px-3 py-2">
                    <div className="text-xs text-gray-500">
                      Manage your tasks and assignments
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Messaging Section */}
              <AccordionItem value="messaging" className="border-none">
                <AccordionTrigger
                  className={`px-3 py-2 hover:bg-gray-50 ${
                    viewMode === 'messaging' ? 'bg-blue-50 text-blue-700' : ''
                  }`}
                  onClick={() => handleViewModeChange('messaging')}
                >
                  <div className="flex items-center space-x-2">
                    <Users className="h-4 w-4" />
                    <span className="text-sm font-medium">Messaging</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-0">
                  <div className="px-3 py-2">
                    <div className="text-xs text-gray-500">
                      Team communication and collaboration
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Team Dashboard Section - Only for supervisors */}
              {isSupervisor && (
                <AccordionItem value="team-dashboard" className="border-none">
                  <AccordionTrigger
                    className={`px-3 py-2 hover:bg-gray-50 ${
                      viewMode === 'team-dashboard' ? 'bg-blue-50 text-blue-700' : ''
                    }`}
                    onClick={() => handleViewModeChange('team-dashboard')}
                  >
                    <div className="flex items-center space-x-2">
                      <Shield className="h-4 w-4" />
                      <span className="text-sm font-medium">Team Dashboard</span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="pb-0">
                    <div className="px-3 py-2">
                      <div className="text-xs text-gray-500">
                        Manage team members and overview
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              )}
            </Accordion>
          </div>
        </>
      ) : (
        /* Collapsed State - Icon Only */
        <div className="flex flex-col items-center py-4 space-y-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className={`h-8 w-8 ${viewMode === 'chat' ? 'bg-blue-50 text-blue-700' : ''}`}
                onClick={() => handleViewModeChange('chat')}
              >
                <MessageSquare className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">Chat</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className={`h-8 w-8 ${viewMode === 'tasks' ? 'bg-blue-50 text-blue-700' : ''}`}
                onClick={() => handleViewModeChange('tasks')}
              >
                <CheckSquare className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">Tasks</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className={`h-8 w-8 ${viewMode === 'messaging' ? 'bg-blue-50 text-blue-700' : ''}`}
                onClick={() => handleViewModeChange('messaging')}
              >
                <Users className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">Messaging</TooltipContent>
          </Tooltip>

          {/* Team Dashboard - Only for supervisors */}
          {isSupervisor && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className={`h-8 w-8 ${viewMode === 'team-dashboard' ? 'bg-blue-50 text-blue-700' : ''}`}
                  onClick={() => handleViewModeChange('team-dashboard')}
                >
                  <Shield className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">Team Dashboard</TooltipContent>
            </Tooltip>
          )}
        </div>
      )}
    </div>
  );
};

export default CollapsibleSidebar;
