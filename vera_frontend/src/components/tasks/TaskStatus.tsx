
import React from 'react';
import { cn } from '@/lib/utils';

type TaskStatusType = 'pending' | 'in-progress' | 'completed' | 'cancelled';

interface TaskStatusProps {
  status: TaskStatusType;
}

const TaskStatus: React.FC<TaskStatusProps> = ({ status }) => {
  const statusConfig = {
    'pending': {
      label: 'Pending',
      className: 'bg-amber-100 text-amber-800'
    },
    'in-progress': {
      label: 'In Progress',
      className: 'bg-blue-100 text-blue-800'
    },
    'completed': {
      label: 'Completed',
      className: 'bg-green-100 text-green-800'
    },
    'cancelled': {
      label: 'Cancelled',
      className: 'bg-red-100 text-red-800'
    }
  };
  
  const config = statusConfig[status];
  
  return (
    <span className={cn("status-pill", config.className)}>
      {config.label}
    </span>
  );
};

export default TaskStatus;
