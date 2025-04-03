
import React, { useState } from 'react';
import { CheckCircle, Calendar, Clock, AlertCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

interface BriefingTask {
  id: string;
  name: string;
  assignedTo: string;
  dueDate?: string;
  status: 'completed' | 'delayed' | 'upcoming';
}

const DailyBriefing: React.FC<{ open: boolean; onClose: () => void }> = ({ open, onClose }) => {
  const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  
  const [briefingData] = useState({
    date: today,
    completedTasks: [
      {
        id: '1',
        name: 'Follow up with client leads',
        assignedTo: 'Alex Chen',
        status: 'completed' as const
      },
      {
        id: '2',
        name: 'Finalize vendor contract',
        assignedTo: 'Jamie Wilson',
        status: 'completed' as const
      }
    ],
    delayedTasks: [
      {
        id: '3',
        name: 'Review marketing campaign proposal',
        assignedTo: 'Jamie Wilson',
        dueDate: '2025-04-03',
        status: 'delayed' as const
      }
    ],
    upcomingTasks: [
      {
        id: '4',
        name: 'Schedule meeting with investors',
        assignedTo: 'Tom Yang',
        dueDate: '2025-04-04',
        status: 'upcoming' as const
      },
      {
        id: '5',
        name: 'Finalize product roadmap',
        assignedTo: 'Raj Patel',
        dueDate: '2025-04-08',
        status: 'upcoming' as const
      }
    ],
    tomorrowTasks: [
      {
        id: '6',
        name: 'Present quarterly report to leadership',
        assignedTo: 'Sarah Johnson',
        dueDate: '2025-04-04',
        status: 'upcoming' as const
      },
      {
        id: '7',
        name: 'Review new UI designs',
        assignedTo: 'Alex Chen',
        dueDate: '2025-04-04',
        status: 'upcoming' as const
      }
    ]
  });
  
  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };
  
  const TaskItem: React.FC<{ task: BriefingTask }> = ({ task }) => {
    const getStatusIcon = () => {
      switch (task.status) {
        case 'completed':
          return <CheckCircle className="h-4 w-4 text-green-500" />;
        case 'delayed':
          return <AlertCircle className="h-4 w-4 text-amber-500" />;
        case 'upcoming':
          return <Clock className="h-4 w-4 text-blue-500" />;
        default:
          return null;
      }
    };
    
    return (
      <div className="flex items-center space-x-3 py-2">
        <div className="flex-shrink-0">
          {getStatusIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {task.name}
          </p>
          <p className="text-xs text-gray-500 truncate">
            Assigned to {task.assignedTo}
            {task.dueDate && ` · Due ${formatDate(task.dueDate)}`}
          </p>
        </div>
      </div>
    );
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-vira-primary" />
            <DialogTitle>Daily Briefing</DialogTitle>
          </div>
          <DialogDescription>
            Your summary for {briefingData.date}
          </DialogDescription>
        </DialogHeader>
        
        <ScrollArea className="flex-1 mt-2">
          <div className="space-y-4 pr-4">
            {briefingData.completedTasks.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  Completed Today ({briefingData.completedTasks.length})
                </h3>
                <div className="space-y-1 pl-1">
                  {briefingData.completedTasks.map(task => (
                    <TaskItem key={task.id} task={task} />
                  ))}
                </div>
              </div>
            )}
            
            {briefingData.delayedTasks.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Still Pending ({briefingData.delayedTasks.length})
                  </h3>
                  <div className="space-y-1 pl-1">
                    {briefingData.delayedTasks.map(task => (
                      <TaskItem key={task.id} task={task} />
                    ))}
                  </div>
                </div>
              </>
            )}
            
            {briefingData.tomorrowTasks.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Due Tomorrow ({briefingData.tomorrowTasks.length})
                  </h3>
                  <div className="space-y-1 pl-1">
                    {briefingData.tomorrowTasks.map(task => (
                      <TaskItem key={task.id} task={task} />
                    ))}
                  </div>
                </div>
              </>
            )}
            
            {briefingData.upcomingTasks.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Upcoming Tasks ({briefingData.upcomingTasks.length})
                  </h3>
                  <div className="space-y-1 pl-1">
                    {briefingData.upcomingTasks.map(task => (
                      <TaskItem key={task.id} task={task} />
                    ))}
                  </div>
                </div>
              </>
            )}
            
            <Separator />
            
            <div className="bg-vira-light p-3 rounded-md border border-vira-primary/20">
              <h3 className="text-sm font-semibold text-vira-primary mb-1">
                AI Summary
              </h3>
              <p className="text-sm text-gray-700">
                You've completed 2 tasks today. There's 1 task that's currently delayed, 
                and 2 tasks due tomorrow. Your focus today should be on finalizing the marketing 
                proposal review which is currently delayed.
              </p>
            </div>
          </div>
        </ScrollArea>
        
        <DialogFooter className="flex-shrink-0 mt-4">
          <Button variant="outline" onClick={onClose}>Close</Button>
          <Button onClick={onClose}>View All Tasks</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default DailyBriefing;
