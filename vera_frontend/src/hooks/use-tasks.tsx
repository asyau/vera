
import { useState } from 'react';
import { Task } from '@/components/tasks/TaskTable';

// Sample data for initial state
const initialTasks: Task[] = [
  {
    id: '1',
    name: 'Schedule meeting with investors',
    assignedTo: 'Tom Yang',
    dueDate: '2025-04-04',
    status: 'in-progress',
    description: 'Coordinate a meeting with the investment team to discuss Q2 funding.',
    originalPrompt: 'Vira, please schedule a meeting with our investors for sometime next week.',
    timeline: {
      createdAt: '2025-04-03T09:30:00',
      sentAt: '2025-04-03T09:35:00'
    }
  },
  {
    id: '2',
    name: 'Prepare quarterly report',
    assignedTo: 'Sarah Johnson',
    dueDate: '2025-04-10',
    status: 'pending',
    description: 'Compile Q1 performance metrics and prepare executive summary.',
    originalPrompt: 'I need a quarterly report prepared by next week.',
    timeline: {
      createdAt: '2025-04-02T14:15:00',
      sentAt: '2025-04-02T14:20:00'
    }
  },
  {
    id: '3',
    name: 'Follow up with client leads',
    assignedTo: 'Alex Chen',
    dueDate: '2025-04-03',
    status: 'completed',
    description: 'Contact potential clients from the conference and schedule demos.',
    originalPrompt: 'Please have Alex follow up with the leads we got from last week\'s conference.',
    timeline: {
      createdAt: '2025-04-01T10:45:00',
      sentAt: '2025-04-01T10:50:00',
      completedAt: '2025-04-03T09:15:00'
    }
  },
  {
    id: '4',
    name: 'Review marketing campaign proposal',
    assignedTo: 'Jamie Wilson',
    dueDate: '2025-04-05',
    status: 'pending',
    description: 'Review and approve the Q2 marketing campaign strategy.',
    originalPrompt: 'Ask Jamie to send me the marketing proposal for review by Friday.',
    timeline: {
      createdAt: '2025-04-02T16:20:00',
      sentAt: '2025-04-02T16:25:00'
    }
  },
  {
    id: '5',
    name: 'Finalize product roadmap',
    assignedTo: 'Raj Patel',
    dueDate: '2025-04-08',
    status: 'in-progress',
    description: 'Complete the product roadmap for Q2-Q3 with key milestones.',
    originalPrompt: 'Vira, tell Raj I need the product roadmap finalized by next Tuesday.',
    timeline: {
      createdAt: '2025-04-03T11:10:00',
      sentAt: '2025-04-03T11:15:00'
    }
  }
];

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  
  // Add a new task
  const addTask = (task: Omit<Task, 'id'>) => {
    const newTask: Task = {
      ...task,
      id: Math.random().toString(36).substring(2, 9), // Generate a random ID
    };
    setTasks((prevTasks) => [...prevTasks, newTask]);
    return newTask;
  };
  
  // Update an existing task
  const updateTask = (id: string, updates: Partial<Task>) => {
    setTasks((prevTasks) =>
      prevTasks.map((task) =>
        task.id === id ? { ...task, ...updates } : task
      )
    );
  };
  
  // Delete a task
  const deleteTask = (id: string) => {
    setTasks((prevTasks) => prevTasks.filter((task) => task.id !== id));
  };
  
  // Get tasks by status
  const getTasksByStatus = (status: Task['status']) => {
    return tasks.filter((task) => task.status === status);
  };
  
  // Get tasks due today
  const getTasksDueToday = () => {
    const today = new Date().toISOString().split('T')[0];
    return tasks.filter((task) => task.dueDate === today);
  };
  
  // Get tasks due this week
  const getTasksDueThisWeek = () => {
    const today = new Date();
    const weekLater = new Date();
    weekLater.setDate(today.getDate() + 7);
    
    return tasks.filter((task) => {
      const taskDate = new Date(task.dueDate);
      return taskDate >= today && taskDate <= weekLater;
    });
  };
  
  // Get tasks by assignee
  const getTasksByAssignee = (assignee: string) => {
    return tasks.filter((task) => task.assignedTo === assignee);
  };
  
  return {
    tasks,
    addTask,
    updateTask,
    deleteTask,
    getTasksByStatus,
    getTasksDueToday,
    getTasksDueThisWeek,
    getTasksByAssignee,
  };
}
