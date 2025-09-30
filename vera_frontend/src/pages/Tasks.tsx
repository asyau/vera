import React from 'react';
import { useAuthStore } from '@/stores/authStore';
import EmployeeTaskView from '@/components/tasks/EmployeeTaskView';
import SupervisorTaskView from '@/components/tasks/SupervisorTaskView';

const Tasks: React.FC = () => {
  const { hasRole } = useAuthStore();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
        <p className="mt-1 text-sm text-gray-500">
          {hasRole('supervisor')
            ? 'Manage and track your team\'s tasks'
            : 'View and manage your assigned tasks'
          }
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        {hasRole('supervisor') ? <SupervisorTaskView /> : <EmployeeTaskView />}
      </div>
    </div>
  );
};

export default Tasks;
