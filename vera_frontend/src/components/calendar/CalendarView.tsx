import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Calendar as CalendarIcon,
  Clock,
  MapPin,
  Users,
  ExternalLink
} from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface Task {
  id: string;
  name: string;
  description?: string;
  status: string;
  priority: string;
  assigned_to?: string;
  due_date?: string;
  created_at: string;
}

interface CalendarEvent {
  id: string;
  summary: string;
  description?: string;
  start: {
    dateTime?: string;
    date?: string;
    timeZone?: string;
  };
  end: {
    dateTime?: string;
    date?: string;
    timeZone?: string;
  };
  location?: string;
  attendees?: Array<{
    email: string;
    displayName?: string;
  }>;
  htmlLink?: string;
  source: 'google' | 'microsoft' | 'vira';
}

interface CalendarItem {
  id: string;
  title: string;
  description?: string;
  start: Date;
  end: Date;
  type: 'task' | 'event';
  priority?: string;
  status?: string;
  location?: string;
  attendees?: string[];
  source: string;
  link?: string;
}

interface CalendarViewProps {
  tasks: Task[];
  integrations: any[];
  onTaskCreate: () => void;
  onEventCreate: () => void;
}

const CalendarView: React.FC<CalendarViewProps> = ({
  tasks,
  integrations,
  onTaskCreate,
  onEventCreate
}) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<'month' | 'week' | 'day'>('month');
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadCalendarEvents();
  }, [currentDate, integrations]);

  const loadCalendarEvents = async () => {
    setLoading(true);
    try {
      const events: CalendarEvent[] = [];

      // Load Google Calendar events from integrations
      const googleIntegrations = integrations.filter(i =>
        i.type === 'google_calendar' && i.status === 'connected' && i.healthy
      );

      for (const integration of googleIntegrations) {
        try {
          const startDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
          const endDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

          const googleEvents = await api.getCalendarEvents(
            integration.id,
            startDate.toISOString(),
            endDate.toISOString()
          );

          if (googleEvents.success && googleEvents.data) {
            const formattedEvents = googleEvents.data.map((event: any) => ({
              ...event,
              source: 'google'
            }));
            events.push(...formattedEvents);
          }
        } catch (error) {
          console.warn(`Failed to load events from integration ${integration.id}:`, error);
        }
      }

      setCalendarEvents(events);
    } catch (error) {
      toast({
        title: "Error Loading Calendar Events",
        description: "Could not load calendar events from integrations",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const combineTasksAndEvents = (): CalendarItem[] => {
    const items: CalendarItem[] = [];

    // Add tasks with due dates
    tasks.forEach(task => {
      if (task.due_date) {
        const dueDate = new Date(task.due_date);
        items.push({
          id: task.id,
          title: task.name,
          description: task.description,
          start: dueDate,
          end: dueDate,
          type: 'task',
          priority: task.priority,
          status: task.status,
          source: 'vira'
        });
      }
    });

    // Add calendar events
    calendarEvents.forEach(event => {
      const start = event.start.dateTime
        ? new Date(event.start.dateTime)
        : new Date(event.start.date + 'T00:00:00');

      const end = event.end.dateTime
        ? new Date(event.end.dateTime)
        : new Date(event.end.date + 'T23:59:59');

      items.push({
        id: event.id,
        title: event.summary,
        description: event.description,
        start,
        end,
        type: 'event',
        location: event.location,
        attendees: event.attendees?.map(a => a.displayName || a.email),
        source: event.source,
        link: event.htmlLink
      });
    });

    return items.sort((a, b) => a.start.getTime() - b.start.getTime());
  };

  const getMonthDays = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());

    const days = [];
    const current = new Date(startDate);

    for (let i = 0; i < 42; i++) {
      days.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }

    return days;
  };

  const getItemsForDate = (date: Date): CalendarItem[] => {
    const items = combineTasksAndEvents();
    return items.filter(item => {
      const itemDate = new Date(item.start.getFullYear(), item.start.getMonth(), item.start.getDate());
      const checkDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      return itemDate.getTime() === checkDate.getTime();
    });
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'complete':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'in-progress':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'pending':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    if (direction === 'prev') {
      newDate.setMonth(newDate.getMonth() - 1);
    } else {
      newDate.setMonth(newDate.getMonth() + 1);
    }
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const renderMonthView = () => {
    const days = getMonthDays();
    const today = new Date();
    const currentMonth = currentDate.getMonth();

    return (
      <div className="grid grid-cols-7 gap-1">
        {/* Day headers */}
        {dayNames.map(day => (
          <div key={day} className="p-2 text-center font-medium text-sm text-muted-foreground">
            {day}
          </div>
        ))}

        {/* Calendar days */}
        {days.map((day, index) => {
          const isCurrentMonth = day.getMonth() === currentMonth;
          const isToday = day.toDateString() === today.toDateString();
          const items = getItemsForDate(day);

          return (
            <div
              key={index}
              className={`min-h-24 p-1 border border-gray-200 ${
                isCurrentMonth ? 'bg-white' : 'bg-gray-50'
              } ${isToday ? 'ring-2 ring-primary' : ''}`}
            >
              <div className={`text-sm font-medium mb-1 ${
                isCurrentMonth ? 'text-gray-900' : 'text-gray-400'
              } ${isToday ? 'text-primary' : ''}`}>
                {day.getDate()}
              </div>

              <div className="space-y-1">
                {items.slice(0, 3).map(item => (
                  <div
                    key={item.id}
                    className={`text-xs p-1 rounded truncate cursor-pointer ${
                      item.type === 'task'
                        ? getPriorityColor(item.priority)
                        : 'bg-blue-100 text-blue-800 border-blue-200'
                    }`}
                    title={`${item.title} ${item.description ? '- ' + item.description : ''}`}
                  >
                    <div className="flex items-center space-x-1">
                      {item.type === 'task' ? (
                        <CalendarIcon className="w-3 h-3" />
                      ) : (
                        <Clock className="w-3 h-3" />
                      )}
                      <span className="truncate">{item.title}</span>
                    </div>
                  </div>
                ))}

                {items.length > 3 && (
                  <div className="text-xs text-muted-foreground">
                    +{items.length - 3} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderTodayView = () => {
    const today = new Date();
    const todayItems = getItemsForDate(today);

    return (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold">
            {today.toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </h3>
        </div>

        {todayItems.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <CalendarIcon className="w-12 h-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No items for today</h3>
              <p className="text-muted-foreground text-center mb-4">
                You have a clear schedule for today. Why not add a task or create an event?
              </p>
              <div className="flex space-x-2">
                <Button onClick={onTaskCreate} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Task
                </Button>
                <Button onClick={onEventCreate} variant="outline" size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Event
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {todayItems.map(item => (
              <Card key={item.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        {item.type === 'task' ? (
                          <CalendarIcon className="w-4 h-4 text-primary" />
                        ) : (
                          <Clock className="w-4 h-4 text-blue-500" />
                        )}
                        <h4 className="font-medium">{item.title}</h4>

                        {item.type === 'task' && item.priority && (
                          <Badge className={getPriorityColor(item.priority)}>
                            {item.priority}
                          </Badge>
                        )}

                        {item.type === 'task' && item.status && (
                          <Badge className={getStatusColor(item.status)}>
                            {item.status}
                          </Badge>
                        )}
                      </div>

                      {item.description && (
                        <p className="text-sm text-muted-foreground mb-2">
                          {item.description}
                        </p>
                      )}

                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <div className="flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>
                            {item.start.getTime() === item.end.getTime()
                              ? formatTime(item.start)
                              : `${formatTime(item.start)} - ${formatTime(item.end)}`
                            }
                          </span>
                        </div>

                        {item.location && (
                          <div className="flex items-center space-x-1">
                            <MapPin className="w-3 h-3" />
                            <span>{item.location}</span>
                          </div>
                        )}

                        {item.attendees && item.attendees.length > 0 && (
                          <div className="flex items-center space-x-1">
                            <Users className="w-3 h-3" />
                            <span>{item.attendees.length} attendees</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className="text-xs">
                        {item.source}
                      </Badge>

                      {item.link && (
                        <Button variant="ghost" size="sm" asChild>
                          <a href={item.link} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </Button>
                      )}
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

  return (
    <div className="space-y-4">
      {/* Calendar Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateMonth('prev')}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>

            <h2 className="text-xl font-semibold">
              {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
            </h2>

            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateMonth('next')}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>

          <Button variant="outline" size="sm" onClick={goToToday}>
            Today
          </Button>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            <Button
              variant={view === 'month' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setView('month')}
            >
              Month
            </Button>
            <Button
              variant={view === 'day' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setView('day')}
            >
              Today
            </Button>
          </div>

          <Button onClick={onTaskCreate} size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Add Task
          </Button>

          <Button onClick={onEventCreate} variant="outline" size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Create Event
          </Button>
        </div>
      </div>

      {/* Calendar Content */}
      <Card>
        <CardContent className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              {view === 'month' && renderMonthView()}
              {view === 'day' && renderTodayView()}
            </>
          )}
        </CardContent>
      </Card>

      {/* Integration Status */}
      {integrations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Connected Calendars</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex flex-wrap gap-2">
              {integrations
                .filter(i => ['google_calendar', 'microsoft_teams'].includes(i.type))
                .map(integration => (
                  <Badge
                    key={integration.id}
                    variant={integration.healthy && integration.status === 'connected' ? 'default' : 'destructive'}
                  >
                    {integration.name}
                  </Badge>
                ))
              }

              {integrations.filter(i => ['google_calendar', 'microsoft_teams'].includes(i.type)).length === 0 && (
                <div className="text-sm text-muted-foreground">
                  No calendar integrations connected.
                  <Button variant="link" className="p-0 h-auto text-sm" onClick={onEventCreate}>
                    Connect a calendar service
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CalendarView;
