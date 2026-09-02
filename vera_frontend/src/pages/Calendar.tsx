import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Calendar as CalendarIcon,
  RefreshCw,
  Settings,
  Plus,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import { useTasks } from '@/hooks/use-tasks';
import CalendarView from '@/components/calendar/CalendarView';
import TaskEventModal from '@/components/calendar/TaskEventModal';


interface Integration {
  id: string;
  type: string;
  name: string;
  status: string;
  healthy: boolean;
  config: any;
}

const Calendar: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'task' | 'event'>('task');
  const [syncing, setSyncing] = useState(false);
  const { toast } = useToast();

  // Use the existing tasks hook
  const { tasks, loading: tasksLoading, error: tasksError, refetch } = useTasks();

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    setLoading(true);
    try {
      const integrationsData = await api.getCompanyIntegrations();
      setIntegrations(integrationsData);
    } catch (error) {
      toast({
        title: "Error Loading Integrations",
        description: "Could not load calendar integrations",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSyncCalendars = async () => {
    setSyncing(true);
    try {
      const calendarIntegrations = integrations.filter(i =>
        ['google_calendar', 'microsoft_teams'].includes(i.type) &&
        i.status === 'connected' &&
        i.healthy
      );

      if (calendarIntegrations.length === 0) {
        toast({
          title: "No Calendar Integrations",
          description: "Connect a calendar service to sync events",
          variant: "destructive",
        });
        return;
      }

      // Sync each calendar integration
      const syncPromises = calendarIntegrations.map(integration =>
        api.syncIntegrationData(integration.id, 'incremental')
      );

      const results = await Promise.allSettled(syncPromises);

      const successful = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.length - successful;

      if (successful > 0) {
        toast({
          title: "Calendar Sync Complete",
          description: `${successful} calendar${successful > 1 ? 's' : ''} synced successfully${failed > 0 ? `, ${failed} failed` : ''}`,
        });
      } else {
        toast({
          title: "Sync Failed",
          description: "Could not sync calendar data",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Sync Failed",
        description: "Could not sync calendar integrations",
        variant: "destructive",
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleCreateTask = () => {
    setModalMode('task');
    setModalOpen(true);
  };

  const handleCreateEvent = () => {
    setModalMode('event');
    setModalOpen(true);
  };

  const handleModalSuccess = () => {
    refetch();
    loadIntegrations(); // Refresh to get updated sync times
  };

  const calendarIntegrations = integrations.filter(i =>
    ['google_calendar', 'microsoft_teams'].includes(i.type)
  );

  const connectedCalendars = calendarIntegrations.filter(i =>
    i.status === 'connected' && i.healthy
  );

  const renderIntegrationStatus = () => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-base">Calendar Integrations</CardTitle>
          <CardDescription>
            Connected calendar services and sync status
          </CardDescription>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSyncCalendars}
            disabled={syncing || connectedCalendars.length === 0}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
            Sync
          </Button>
          <Button variant="outline" size="sm" onClick={loadIntegrations}>
            <Settings className="w-4 h-4 mr-2" />
            Manage
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {calendarIntegrations.length === 0 ? (
          <div className="text-center py-6">
            <CalendarIcon className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground mb-3">
              No calendar integrations found. Connect Google Calendar or Microsoft Outlook to see external events.
            </p>
            <Button size="sm" onClick={() => window.open('/integrations', '_blank')}>
              <Plus className="w-4 h-4 mr-2" />
              Add Calendar Integration
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            {calendarIntegrations.map(integration => (
              <div key={integration.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="text-lg">
                    {integration.type === 'google_calendar' ? '📅' : '💼'}
                  </div>
                  <div>
                    <div className="font-medium text-sm">{integration.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {integration.type.replace('_', ' ').toUpperCase()}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Badge
                    variant={integration.healthy && integration.status === 'connected' ? 'default' : 'destructive'}
                    className="text-xs"
                  >
                    {integration.healthy && integration.status === 'connected' ? (
                      <>
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Connected
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-3 h-3 mr-1" />
                        {integration.status}
                      </>
                    )}
                  </Badge>

                  {integration.config?.last_sync && (
                    <div className="text-xs text-muted-foreground">
                      Last sync: {new Date(integration.config.last_sync).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderStatsCards = () => {
    const totalTasks = tasks?.length || 0;
    const pendingTasks = tasks?.filter(t => t.status === 'pending')?.length || 0;
    const inProgressTasks = tasks?.filter(t => t.status === 'in-progress')?.length || 0;
    const completedTasks = tasks?.filter(t => t.status === 'complete')?.length || 0;

    const tasksWithDueDates = tasks?.filter(t => t.due_date)?.length || 0;
    const overdueTasks = tasks?.filter(t => {
      if (!t.due_date) return false;
      return new Date(t.due_date) < new Date() && t.status !== 'complete';
    })?.length || 0;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
            <CalendarIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTasks}</div>
            <p className="text-xs text-muted-foreground">
              {tasksWithDueDates} with due dates
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <div className="h-4 w-4 bg-blue-500 rounded-full" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{inProgressTasks}</div>
            <p className="text-xs text-muted-foreground">
              {pendingTasks} pending
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedTasks}</div>
            <p className="text-xs text-muted-foreground">
              {totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0}% completion rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertCircle className={`h-4 w-4 ${overdueTasks > 0 ? 'text-red-500' : 'text-muted-foreground'}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${overdueTasks > 0 ? 'text-red-600' : ''}`}>
              {overdueTasks}
            </div>
            <p className="text-xs text-muted-foreground">
              {connectedCalendars.length} calendar{connectedCalendars.length !== 1 ? 's' : ''} connected
            </p>
          </CardContent>
        </Card>
      </div>
    );
  };

  if (loading || tasksLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (tasksError) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Error Loading Calendar</h3>
            <p className="text-muted-foreground text-center mb-4">
              {tasksError.includes('Authentication') || tasksError.includes('Session expired')
                ? tasksError
                : 'Could not load calendar data. Please try refreshing the page.'}
            </p>
            <div className="flex space-x-2">
              <Button onClick={() => window.location.reload()}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Page
              </Button>
              {(tasksError.includes('Authentication') || tasksError.includes('Session expired')) && (
                <Button onClick={() => window.location.href = '/login'} variant="outline">
                  Go to Login
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Calendar</h1>
          <p className="text-muted-foreground mt-2">
            Manage your tasks and view calendar events from connected services.
          </p>
        </div>

        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => { refetch(); loadIntegrations(); }}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={handleCreateTask}>
            <Plus className="w-4 h-4 mr-2" />
            Add Task
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {renderStatsCards()}

      {/* Integration Status */}
      {renderIntegrationStatus()}

      {/* Calendar View */}
      <CalendarView
        tasks={tasks || []}
        integrations={integrations}
        onTaskCreate={handleCreateTask}
        onEventCreate={handleCreateEvent}
      />

      {/* Task/Event Creation Modal */}
      <TaskEventModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={handleModalSuccess}
        integrations={integrations}
        mode={modalMode}
      />
    </div>
  );
};

export default Calendar;
