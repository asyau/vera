import React from 'react';
import { MessageSquare, Clipboard, KanbanSquare, Users, Sparkles, Bot, Target, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ViewNavigationProps {
  viewMode: 'chat' | 'tasks' | 'trichat';
  onViewModeChange: (mode: 'chat' | 'tasks' | 'trichat') => void;
  showTaskPanel?: boolean;
  onToggleTaskPanel?: () => void;
}

const ViewNavigation: React.FC<ViewNavigationProps> = ({
  viewMode,
  onViewModeChange,
  showTaskPanel,
  onToggleTaskPanel
}) => {
  const navigationItems = [
    {
      id: 'chat' as const,
      label: 'Chat',
      description: 'Conversation with optional task management',
      icon: MessageSquare,
      color: 'from-blue-500 to-indigo-600',
      bgColor: 'bg-gradient-to-r from-blue-50 to-indigo-50',
      borderColor: 'border-blue-200'
    },
    {
      id: 'tasks' as const,
      label: 'Tasks',
      description: 'Dedicated task workspace',
      icon: KanbanSquare,
      color: 'from-purple-500 to-violet-600',
      bgColor: 'bg-gradient-to-r from-purple-50 to-violet-50',
      borderColor: 'border-purple-200'
    },
    {
      id: 'trichat' as const,
      label: 'TriChat',
      description: 'Multi-agent collaboration',
      icon: Users,
      color: 'from-orange-500 to-red-600',
      bgColor: 'bg-gradient-to-r from-orange-50 to-red-50',
      borderColor: 'border-orange-200'
    }
  ];

  return (
    <div className="bg-white/80 backdrop-blur-sm border-b border-gray-100 px-4 py-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = viewMode === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => onViewModeChange(item.id)}
                className={cn(
                  "relative group flex items-center space-x-2 px-3 py-1.5 rounded-lg transition-all duration-200 ease-in-out",
                  "hover:scale-102 hover:shadow-sm",
                  isActive 
                    ? `${item.bgColor} ${item.borderColor} border shadow-md` 
                    : "hover:bg-gray-50 border border-transparent"
                )}
              >
                <div className={cn(
                  "flex items-center justify-center w-6 h-6 rounded-md transition-all duration-200",
                  isActive 
                    ? `bg-gradient-to-r ${item.color} text-white shadow-sm` 
                    : "bg-gray-100 text-gray-600 group-hover:bg-gray-200"
                )}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                
                <span className={cn(
                  "text-sm font-medium transition-colors duration-200",
                  isActive 
                    ? `bg-gradient-to-r ${item.color} bg-clip-text text-transparent` 
                    : "text-gray-700 group-hover:text-gray-900"
                )}>
                  {item.label}
                </span>
                
                {isActive && (
                  <div className={cn(
                    "absolute -bottom-0.5 left-1/2 transform -translate-x-1/2 w-1.5 h-1.5 rounded-full",
                    `bg-gradient-to-r ${item.color}`
                  )} />
                )}
              </button>
            );
          })}
        </div>
        
        {/* Right side controls */}
        <div className="flex items-center space-x-2">
          {viewMode === 'chat' && onToggleTaskPanel && (
            <button
              onClick={onToggleTaskPanel}
              className={cn(
                "flex items-center space-x-1.5 px-2.5 py-1.5 rounded-md transition-all duration-200 text-xs font-medium",
                "hover:bg-gray-50 hover:scale-102",
                showTaskPanel 
                  ? "bg-blue-50 text-blue-700 border border-blue-200" 
                  : "bg-gray-50 text-gray-600 border border-gray-200"
              )}
            >
              <Clipboard className="w-3.5 h-3.5" />
              {showTaskPanel ? 'Hide Tasks' : 'Show Tasks'}
            </button>
          )}
          
          {/* AI Status indicator */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1.5 bg-gradient-to-r from-green-50 to-emerald-50 rounded-md border border-green-200">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
            <span className="text-xs font-medium text-green-700">AI Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ViewNavigation; 