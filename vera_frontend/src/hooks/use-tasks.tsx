import { useState, useEffect } from 'react';
import { api } from '@/services/api';
import { Task } from '@/types/task';

export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch tasks on mount
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const fetchedTasks = await api.getTasks();
        setTasks(fetchedTasks);
        setError(null);
      } catch (err) {
        console.error('Tasks fetch error:', err);

        // More specific error handling
        if (err instanceof Error) {
          if (err.message.includes('403') || err.message.includes('Not authenticated')) {
            setError('Authentication required. Please log in again.');
          } else if (err.message.includes('401')) {
            setError('Session expired. Please log in again.');
          } else {
            setError(err.message);
          }
        } else {
          setError('Failed to fetch tasks');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, []);

  // Add a new task
  const addTask = async (task: Omit<Task, 'id' | 'timeline'>) => {
    try {
      const newTask = await api.createTask(task);
      setTasks((prevTasks) => [...prevTasks, newTask]);
      return newTask;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task');
      throw err;
    }
  };

  // Update an existing task
  const updateTask = async (id: string, updates: Partial<Task>) => {
    try {
      const updatedTask = await api.updateTask(id, updates);
      setTasks((prevTasks) =>
        prevTasks.map((task) =>
          task.id === id ? updatedTask : task
        )
      );
      return updatedTask;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task');
      throw err;
    }
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
    return tasks.filter((task) => task.due_date === today);
  };

  // Get tasks due this week
  const getTasksDueThisWeek = () => {
    const today = new Date();
    const weekLater = new Date();
    weekLater.setDate(today.getDate() + 7);

    return tasks.filter((task) => {
      const taskDate = new Date(task.due_date || '');
      return taskDate >= today && taskDate <= weekLater;
    });
  };

  // Get tasks by assignee ID
  const getTasksByAssignee = (assigneeId: string) => {
    return tasks.filter((task) => task.assigned_to === assigneeId);
  };

  // Refetch tasks
  const refetch = async () => {
    setLoading(true);
    try {
      const fetchedTasks = await api.getTasks();
      setTasks(fetchedTasks);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  };

  return {
    tasks,
    loading,
    error,
    addTask,
    updateTask,
    deleteTask,
    getTasksByStatus,
    getTasksDueToday,
    getTasksDueThisWeek,
    getTasksByAssignee,
    refetch,
  };
}
