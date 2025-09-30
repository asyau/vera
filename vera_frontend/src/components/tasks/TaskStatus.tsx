
import React from 'react';
import { cn } from '@/lib/utils';

type TaskStatusType = 'todo' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';

interface TaskStatusProps {
  status: TaskStatusType;
}

const TaskStatus: React.FC<TaskStatusProps> = ({ status }) => {
  const statusConfig = {
      'todo': {
    label: 'To Do',
      className: 'bg-amber-100 text-amber-800'
    },
    'assigned': {
      label: 'Assigned',
      className: 'bg-purple-100 text-purple-800'
    },
    'in_progress': {
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
