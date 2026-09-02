import React, { useState } from 'react';
import { Calendar, CheckCircle, Clock, Filter, User, KanbanSquare, ListFilter } from 'lucide-react';
import TaskStatus from './TaskStatus';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTasks } from '@/hooks/use-tasks';
import { useUsers } from '@/hooks/use-users';
import { Task } from '@/types/task';

interface TaskTableProps {
  fullScreen?: boolean;
}

const TaskTable: React.FC<TaskTableProps> = ({ fullScreen = false }) => {
  const { tasks, loading, error } = useTasks();
  const { getUserName } = useUsers();
  const [activeFilter, setActiveFilter] = useState('all');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [viewType, setViewType] = useState<'table' | 'kanban'>('table');
  const [assigneeFilter, setAssigneeFilter] = useState<string | null>(null);

  // Format date to display in a user-friendly format
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Filter tasks based on active filter
  const filteredTasks = tasks.filter(task => {
    let passesTimeFilter = true;
    let passesAssigneeFilter = true;

    // Apply time filter
    if (activeFilter === 'today') {
      const today = new Date().toISOString().split('T')[0];
      passesTimeFilter = task.due_date === today;
    } else if (activeFilter === 'week') {
      const today = new Date();
      const weekLater = new Date();
      weekLater.setDate(today.getDate() + 7);
      const taskDate = new Date(task.due_date || '');
      passesTimeFilter = taskDate >= today && taskDate <= weekLater;
    }

    // Apply assignee filter
    if (assigneeFilter) {
              passesAssigneeFilter = getUserName(task.assigned_to) === assigneeFilter;
    }

    return passesTimeFilter && passesAssigneeFilter;
  });

  // Get unique assignee names for filtering
  const assignees = [...new Set(tasks.map(task => task.assigned_to).filter(Boolean).map(id => getUserName(id)))];

  const handleTaskClick = (task: Task) => {
    setSelectedTask(task);
  };

  const closeTaskDialog = () => {
    setSelectedTask(null);
  };

  // Format timestamp for timeline display
  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  // Group tasks by status for kanban view
  const tasksByStatus = {
    todo: filteredTasks.filter(task => task.status === 'todo'),
    'in_progress': filteredTasks.filter(task => task.status === 'in_progress'),
    completed: filteredTasks.filter(task => task.status === 'completed'),
    cancelled: filteredTasks.filter(task => task.status === 'cancelled')
  };

  if (loading) {
    return (
      <div className="flex flex-col h-full rounded-lg bg-white shadow-sm border border-gray-100 p-4">
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-vira-primary"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full rounded-lg bg-white shadow-sm border border-gray-100 p-4">
        <div className="flex items-center justify-center h-full text-red-500">
          <p>Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full rounded-lg bg-white shadow-sm border border-gray-100">
      <div className="p-4 border-b border-gray-100 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-vira-dark">Task Dashboard</h2>

        {fullScreen && (
          <div className="flex space-x-2">
            <Button
              variant={viewType === 'table' ? "default" : "outline"}
              size="sm"
              onClick={() => setViewType('table')}
              className={viewType === 'table' ? "bg-vira-primary hover:bg-vira-primary/90" : ""}
            >
              <ListFilter className="h-4 w-4 mr-2" />
              Table View
            </Button>
            <Button
              variant={viewType === 'kanban' ? "default" : "outline"}
              size="sm"
              onClick={() => setViewType('kanban')}
              className={viewType === 'kanban' ? "bg-vira-primary hover:bg-vira-primary/90" : ""}
            >
              <KanbanSquare className="h-4 w-4 mr-2" />
              Kanban View
            </Button>
          </div>
        )}
      </div>

      <div className="px-4 py-3 border-b border-gray-100">
        <Tabs defaultValue="all" className="w-full">
          <div className="flex items-center justify-between mb-2">
            <TabsList>
              <TabsTrigger
                value="all"
                onClick={() => setActiveFilter('all')}
                className="data-[state=active]:bg-vira-primary data-[state=active]:text-white"
              >
                All
              </TabsTrigger>
              <TabsTrigger
                value="today"
                onClick={() => setActiveFilter('today')}
                className="data-[state=active]:bg-vira-primary data-[state=active]:text-white"
              >
                Today
              </TabsTrigger>
              <TabsTrigger
                value="week"
                onClick={() => setActiveFilter('week')}
                className="data-[state=active]:bg-vira-primary data-[state=active]:text-white"
              >
                This Week
              </TabsTrigger>

              {fullScreen && (
                <div className="ml-2">
                  <select
                    className="h-9 rounded-md border border-gray-200 bg-white px-3 py-2 text-sm"
                    onChange={(e) => setAssigneeFilter(e.target.value || null)}
                    value={assigneeFilter || ''}
                  >
                    <option value="">All Assignees</option>
                    {assignees.map(assignee => (
                      <option key={assignee} value={assignee}>{assignee}</option>
                    ))}
                  </select>
                </div>
              )}
            </TabsList>

            <Button variant="outline" size="sm" className="gap-1">
              <Filter className="h-4 w-4" />
              <span className="hidden sm:inline">Filter</span>
            </Button>
          </div>
        </Tabs>
      </div>

      <div className="flex-1 overflow-y-auto">
        {viewType === 'table' ? (
          <div className="min-w-full divide-y divide-gray-200">
            <div className="bg-gray-50 px-4 py-3 text-xs font-medium text-gray-500">
              <div className="grid grid-cols-10 gap-2">
                <div className="col-span-5">Task</div>
                <div className="col-span-2">Assigned To</div>
                <div className="col-span-2">Due Date</div>
                <div className="col-span-1">Status</div>
              </div>
            </div>

            <div className="divide-y divide-gray-100 bg-white">
              {filteredTasks.length > 0 ? (
                filteredTasks.map((task) => (
                  <div
                    key={task.id}
                    className="grid grid-cols-10 gap-2 px-4 py-3 hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleTaskClick(task)}
                  >
                    <div className="col-span-5 font-medium text-gray-900 truncate">
                                              {task.name}
                    </div>
                    <div className="col-span-2 text-gray-500 flex items-center">
                      <User className="h-3 w-3 mr-1 text-gray-400" />
                      <span className="truncate">{getUserName(task.assigned_to)}</span>
                    </div>
                    <div className="col-span-2 text-gray-500 flex items-center">
                      <Calendar className="h-3 w-3 mr-1 text-gray-400" />
                      <span>{task.due_date ? formatDate(task.due_date) : 'No due date'}</span>
                    </div>
                    <div className="col-span-1">
                      <TaskStatus status={task.status as any} />
                    </div>
                  </div>
                ))
              ) : (
                <div className="px-4 py-8 text-center text-gray-500">
                  No tasks found matching your filters.
                </div>
              )}
            </div>
          </div>
        ) : (
          // Kanban board view
          <div className="p-4 grid grid-cols-4 gap-4 h-full">
            {Object.entries(tasksByStatus).map(([status, statusTasks]) => (
              <div key={status} className="flex flex-col h-full">
                <div className="mb-2 px-2 py-1 bg-gray-100 rounded flex items-center justify-between">
                  <h3 className="text-sm font-medium capitalize">{status.replace('-', ' ')}</h3>
                  <span className="text-xs bg-gray-200 px-2 py-0.5 rounded-full">{statusTasks.length}</span>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2">
                  {statusTasks.map(task => (
                    <div
                      key={task.id}
                      className="p-3 bg-white border border-gray-200 rounded-md shadow-sm hover:shadow cursor-pointer"
                      onClick={() => handleTaskClick(task)}
                    >
                      <div className="font-medium text-sm mb-2 truncate">{task.name}</div>
                      <div className="flex justify-between items-center text-xs text-gray-500">
                        <div className="flex items-center">
                          <User className="h-3 w-3 mr-1" />
                          <span className="truncate max-w-[80px]">{getUserName(task.assigned_to)}</span>
                        </div>
                        <div>{task.due_date ? formatDate(task.due_date) : 'No due date'}</div>
                      </div>
                    </div>
                  ))}
                  {statusTasks.length === 0 && (
                    <div className="p-4 text-center text-gray-400 text-sm italic">
                      No tasks
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Task Details Dialog */}
      <Dialog open={!!selectedTask} onOpenChange={closeTaskDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{selectedTask?.title}</DialogTitle>
            <DialogDescription>
              Task details and progress updates
            </DialogDescription>
          </DialogHeader>

          {selectedTask && (
            <div className="space-y-4 mt-2">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Assigned To</h4>
                  <p className="mt-1">{getUserName(selectedTask.assigned_to)}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Due Date</h4>
                  <p className="mt-1">{selectedTask.due_date ? formatDate(selectedTask.due_date) : 'No due date'}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Status</h4>
                  <div className="mt-1">
                    <TaskStatus status={selectedTask.status as any} />
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-500">Description</h4>
                <p className="mt-1 text-gray-700">{selectedTask.description}</p>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-500">Original Prompt</h4>
                <div className="mt-1 p-2 bg-gray-50 rounded-md text-gray-700 text-sm italic">
                  "{selectedTask.description || 'No description'}"
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-2">Timeline</h4>
                <div className="space-y-2">
                  <div className="flex items-start">
                    <div className="flex-shrink-0 h-5 w-5 flex items-center justify-center mt-0.5">
                      <Clock className="h-4 w-4 text-vira-primary" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium">Created</p>
                      <p className="text-xs text-gray-500">
                        {formatTimestamp(selectedTask.created_at)}
                      </p>
                    </div>
                  </div>

                  {selectedTask.updated_at && selectedTask.updated_at !== selectedTask.created_at && (
                    <div className="flex items-start">
                      <div className="flex-shrink-0 h-5 w-5 flex items-center justify-center mt-0.5">
                        <Clock className="h-4 w-4 text-vira-primary" />
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium">Updated</p>
                        <p className="text-xs text-gray-500">
                          {formatTimestamp(selectedTask.updated_at)}
                        </p>
                      </div>
                    </div>
                  )}

                  {selectedTask.completed_at && (
                    <div className="flex items-start">
                      <div className="flex-shrink-0 h-5 w-5 flex items-center justify-center mt-0.5">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium">Completed</p>
                        <p className="text-xs text-gray-500">
                          {formatTimestamp(selectedTask.completed_at)}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={closeTaskDialog}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TaskTable;
