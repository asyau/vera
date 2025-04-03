import React from 'react';
import TaskTable from '@/components/tasks/TaskTable';

const Tasks: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage and track your team's tasks
        </p>
      </div>
      
      <div className="bg-white rounded-lg shadow">
        <TaskTable fullScreen={true} />
      </div>
    </div>
  );
};

export default Tasks; 