import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Calendar, Clock, User, CheckCircle, Circle, AlertCircle } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { useTasks } from '@/hooks/use-tasks';

const EmployeeTaskView: React.FC = () => {
  const { user } = useAuthStore();
  const { tasks, loading, error } = useTasks();

  // Filter tasks assigned to the current user
  const myTasks = tasks?.filter(task => task.assigned_to === user?.id) || [];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'in_progress':
        return <Circle className="h-4 w-4 text-blue-500" />;
      case 'todo':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'cancelled':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'todo':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProgressValue = (status: string) => {
    switch (status) {
      case 'completed':
        return 100;
      case 'in_progress':
        return 50;
      case 'todo':
        return 0;
      case 'cancelled':
        return 0;
      default:
        return 0;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading your tasks...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Error loading tasks</h3>
        <p className="text-gray-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">My Tasks</h2>
          <p className="text-sm text-gray-500">
            You have {myTasks.length} task{myTasks.length !== 1 ? 's' : ''} assigned
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          Employee View
        </Badge>
      </div>

      {myTasks.length === 0 ? (
        <Card>
          <CardContent className="text-center py-8">
            <Circle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No tasks assigned</h3>
            <p className="text-gray-600">You don't have any tasks assigned to you yet.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {myTasks.map((task) => (
            <Card key={task.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{task.name}</CardTitle>
                    <CardDescription className="mt-1">
                      {task.description}
                    </CardDescription>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(task.status)}
                    <Badge className={getStatusColor(task.status)}>
                      {task.status}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>Progress</span>
                    <span>{getProgressValue(task.status)}%</span>
                  </div>
                  <Progress value={getProgressValue(task.status)} className="h-2" />

                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-4 text-gray-600">
                      {task.due_date && (
                        <div className="flex items-center space-x-1">
                          <Calendar className="h-4 w-4" />
                          <span>Due: {new Date(task.due_date).toLocaleDateString()}</span>
                        </div>
                      )}
                      <div className="flex items-center space-x-1">
                        <Clock className="h-4 w-4" />
                        <span>Created: {new Date(task.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm">
                        View Details
                      </Button>
                      {task.status === 'todo' && (
                        <Button size="sm">
                          Start Task
                        </Button>
                      )}
                      {task.status === 'in_progress' && (
                        <Button size="sm">
                          Mark Complete
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default EmployeeTaskView;
