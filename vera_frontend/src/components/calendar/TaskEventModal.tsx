import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { CalendarIcon, Clock, MapPin, Users, Plus, X } from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface TaskEventModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  integrations: any[];
  mode: 'task' | 'event';
}

interface TaskFormData {
  name: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'in-progress' | 'complete';
  due_date: string;
  assigned_to?: string;
}

interface EventFormData {
  summary: string;
  description: string;
  start_time: string;
  end_time: string;
  timezone: string;
  location: string;
  attendees: string[];
  calendar_id: string;
  integration_id: string;
}

const TaskEventModal: React.FC<TaskEventModalProps> = ({
  open,
  onClose,
  onSuccess,
  integrations,
  mode
}) => {
  const [loading, setLoading] = useState(false);
  const [taskForm, setTaskForm] = useState<TaskFormData>({
    name: '',
    description: '',
    priority: 'medium',
    status: 'pending',
    due_date: '',
  });

  const [eventForm, setEventForm] = useState<EventFormData>({
    summary: '',
    description: '',
    start_time: '',
    end_time: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    location: '',
    attendees: [],
    calendar_id: 'primary',
    integration_id: ''
  });

  const [newAttendee, setNewAttendee] = useState('');
  const [availableCalendars, setAvailableCalendars] = useState<any[]>([]);
  const { toast } = useToast();

  const calendarIntegrations = integrations.filter(i =>
    ['google_calendar', 'microsoft_teams'].includes(i.type) &&
    i.status === 'connected' &&
    i.healthy
  );

  useEffect(() => {
    if (!open) {
      // Reset forms when modal closes
      setTaskForm({
        name: '',
        description: '',
        priority: 'medium',
        status: 'pending',
        due_date: '',
      });
      setEventForm({
        summary: '',
        description: '',
        start_time: '',
        end_time: '',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        location: '',
        attendees: [],
        calendar_id: 'primary',
        integration_id: ''
      });
      setAvailableCalendars([]);
    } else if (mode === 'event' && calendarIntegrations.length > 0) {
      // Set default integration and load calendars
      const defaultIntegration = calendarIntegrations[0];
      setEventForm(prev => ({ ...prev, integration_id: defaultIntegration.id }));
      loadCalendars(defaultIntegration.id);
    }
  }, [open, mode, calendarIntegrations]);

  const loadCalendars = async (integrationId: string) => {
    try {
      const integration = integrations.find(i => i.id === integrationId);
      if (!integration) return;

      let calendars = [];
      if (integration.type === 'google_calendar') {
        const result = await api.getGoogleCalendars(integrationId);
        if (result.success && result.data) {
          calendars = result.data;
        }
      } else if (integration.type === 'microsoft_teams') {
        const result = await api.getMicrosoftTeams(integrationId);
        if (result.success && result.data) {
          calendars = result.data.map((cal: any) => ({
            id: cal.id || 'primary',
            name: cal.name || 'Default Calendar'
          }));
        }
      }

      setAvailableCalendars(calendars);
    } catch (error) {
      console.warn('Failed to load calendars:', error);
    }
  };

  const handleTaskSubmit = async () => {
    if (!taskForm.name.trim()) {
      toast({
        title: "Missing Information",
        description: "Please provide a task name",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const taskData = {
        ...taskForm,
        due_date: taskForm.due_date || undefined,
      };

      const result = await api.createTask(taskData);

      if (result.success || result.id) {
        toast({
          title: "Task Created",
          description: "Your task has been successfully created",
        });
        onSuccess();
        onClose();
      } else {
        toast({
          title: "Creation Failed",
          description: result.error || "Could not create task",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Creation Failed",
        description: "Could not create task",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEventSubmit = async () => {
    if (!eventForm.summary.trim()) {
      toast({
        title: "Missing Information",
        description: "Please provide an event title",
        variant: "destructive",
      });
      return;
    }

    if (!eventForm.start_time || !eventForm.end_time) {
      toast({
        title: "Missing Information",
        description: "Please provide start and end times",
        variant: "destructive",
      });
      return;
    }

    if (!eventForm.integration_id) {
      toast({
        title: "No Calendar Selected",
        description: "Please select a calendar integration",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const eventData = {
        summary: eventForm.summary,
        description: eventForm.description || undefined,
        start_time: eventForm.start_time,
        end_time: eventForm.end_time,
        timezone: eventForm.timezone,
        location: eventForm.location || undefined,
        attendees: eventForm.attendees.length > 0 ? eventForm.attendees : undefined,
        calendar_id: eventForm.calendar_id || 'primary',
      };

      const result = await api.createCalendarEvent(eventForm.integration_id, eventData);

      if (result.success) {
        toast({
          title: "Event Created",
          description: "Your calendar event has been successfully created",
        });
        onSuccess();
        onClose();
      } else {
        toast({
          title: "Creation Failed",
          description: result.error || "Could not create event",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Creation Failed",
        description: "Could not create calendar event",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const addAttendee = () => {
    if (newAttendee.trim() && !eventForm.attendees.includes(newAttendee.trim())) {
      setEventForm(prev => ({
        ...prev,
        attendees: [...prev.attendees, newAttendee.trim()]
      }));
      setNewAttendee('');
    }
  };

  const removeAttendee = (attendee: string) => {
    setEventForm(prev => ({
      ...prev,
      attendees: prev.attendees.filter(a => a !== attendee)
    }));
  };

  const formatDateTimeLocal = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const getDefaultDateTime = (offsetHours: number = 0): string => {
    const now = new Date();
    now.setHours(now.getHours() + offsetHours);
    now.setMinutes(0, 0, 0); // Round to nearest hour
    return formatDateTimeLocal(now);
  };

  const renderTaskForm = () => (
    <div className="space-y-4">
      <div>
        <Label htmlFor="taskName">Task Name *</Label>
        <Input
          id="taskName"
          value={taskForm.name}
          onChange={(e) => setTaskForm({ ...taskForm, name: e.target.value })}
          placeholder="Enter task name"
        />
      </div>

      <div>
        <Label htmlFor="taskDescription">Description</Label>
        <Textarea
          id="taskDescription"
          value={taskForm.description}
          onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
          placeholder="Enter task description (optional)"
          rows={3}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="taskPriority">Priority</Label>
          <Select
            value={taskForm.priority}
            onValueChange={(value: 'low' | 'medium' | 'high') =>
              setTaskForm({ ...taskForm, priority: value })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="taskStatus">Status</Label>
          <Select
            value={taskForm.status}
            onValueChange={(value: 'pending' | 'in-progress' | 'complete') =>
              setTaskForm({ ...taskForm, status: value })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="in-progress">In Progress</SelectItem>
              <SelectItem value="complete">Complete</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor="taskDueDate">Due Date (Optional)</Label>
        <Input
          id="taskDueDate"
          type="datetime-local"
          value={taskForm.due_date}
          onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })}
        />
      </div>

      <div className="flex justify-end space-x-2 pt-4">
        <Button variant="outline" onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button onClick={handleTaskSubmit} disabled={loading}>
          {loading ? 'Creating...' : 'Create Task'}
        </Button>
      </div>
    </div>
  );

  const renderEventForm = () => {
    if (calendarIntegrations.length === 0) {
      return (
        <div className="text-center py-8">
          <CalendarIcon className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Calendar Integration</h3>
          <p className="text-muted-foreground mb-4">
            To create calendar events, you need to connect a calendar service like Google Calendar or Microsoft Outlook.
          </p>
          <Button onClick={onClose}>
            Go to Integrations
          </Button>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div>
          <Label htmlFor="eventSummary">Event Title *</Label>
          <Input
            id="eventSummary"
            value={eventForm.summary}
            onChange={(e) => setEventForm({ ...eventForm, summary: e.target.value })}
            placeholder="Enter event title"
          />
        </div>

        <div>
          <Label htmlFor="eventDescription">Description</Label>
          <Textarea
            id="eventDescription"
            value={eventForm.description}
            onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })}
            placeholder="Enter event description (optional)"
            rows={3}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="startTime">Start Time *</Label>
            <Input
              id="startTime"
              type="datetime-local"
              value={eventForm.start_time || getDefaultDateTime(1)}
              onChange={(e) => setEventForm({ ...eventForm, start_time: e.target.value })}
            />
          </div>

          <div>
            <Label htmlFor="endTime">End Time *</Label>
            <Input
              id="endTime"
              type="datetime-local"
              value={eventForm.end_time || getDefaultDateTime(2)}
              onChange={(e) => setEventForm({ ...eventForm, end_time: e.target.value })}
            />
          </div>
        </div>

        <div>
          <Label htmlFor="location">Location</Label>
          <Input
            id="location"
            value={eventForm.location}
            onChange={(e) => setEventForm({ ...eventForm, location: e.target.value })}
            placeholder="Enter location (optional)"
          />
        </div>

        <div>
          <Label htmlFor="integration">Calendar</Label>
          <Select
            value={eventForm.integration_id}
            onValueChange={(value) => {
              setEventForm({ ...eventForm, integration_id: value });
              loadCalendars(value);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select calendar integration" />
            </SelectTrigger>
            <SelectContent>
              {calendarIntegrations.map(integration => (
                <SelectItem key={integration.id} value={integration.id}>
                  {integration.name} ({integration.type.replace('_', ' ')})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {availableCalendars.length > 0 && (
          <div>
            <Label htmlFor="calendar">Specific Calendar</Label>
            <Select
              value={eventForm.calendar_id}
              onValueChange={(value) => setEventForm({ ...eventForm, calendar_id: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {availableCalendars.map(calendar => (
                  <SelectItem key={calendar.id} value={calendar.id}>
                    {calendar.name || calendar.summary || 'Default Calendar'}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <div>
          <Label>Attendees</Label>
          <div className="flex space-x-2 mb-2">
            <Input
              value={newAttendee}
              onChange={(e) => setNewAttendee(e.target.value)}
              placeholder="Enter email address"
              onKeyPress={(e) => e.key === 'Enter' && addAttendee()}
            />
            <Button type="button" onClick={addAttendee} size="sm">
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          {eventForm.attendees.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {eventForm.attendees.map(attendee => (
                <Badge key={attendee} variant="secondary" className="flex items-center space-x-1">
                  <span>{attendee}</span>
                  <button
                    type="button"
                    onClick={() => removeAttendee(attendee)}
                    className="ml-1 hover:text-red-500"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-2 pt-4">
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleEventSubmit} disabled={loading}>
            {loading ? 'Creating...' : 'Create Event'}
          </Button>
        </div>
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {mode === 'task' ? 'Create New Task' : 'Create Calendar Event'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'task'
              ? 'Add a new task to your Vira workspace'
              : 'Create a new event in your connected calendar'
            }
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {mode === 'task' ? renderTaskForm() : renderEventForm()}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TaskEventModal;
