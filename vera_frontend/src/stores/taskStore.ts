/**
 * Task Store using Zustand
 * Implements MVP pattern - Model layer for task management state
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Task, TaskCreateRequest, TaskUpdateRequest, TaskAnalytics } from '@/types/task';
import { api } from '@/services/api';

export interface TaskState {
  // State
  tasks: Task[];
  currentTask: Task | null;
  overdueTasks: Task[];
  upcomingTasks: Task[];
  analytics: TaskAnalytics | null;
  isLoading: boolean;
  error: string | null;

  // Filters and UI state
  statusFilter: string | null;
  priorityFilter: string | null;
  searchQuery: string;

  // Actions - Task CRUD
  fetchTasks: (filters?: { status?: string; includeCreated?: boolean; includeAssigned?: boolean }) => Promise<void>;
  createTask: (task: TaskCreateRequest) => Promise<Task>;
  updateTask: (taskId: string, updates: TaskUpdateRequest) => Promise<Task>;
  deleteTask: (taskId: string) => Promise<void>;
  assignTask: (taskId: string, assigneeId: string) => Promise<Task>;
  completeTask: (taskId: string) => Promise<Task>;

  // Actions - Task queries
  fetchOverdueTasks: () => Promise<void>;
  fetchUpcomingTasks: (days?: number) => Promise<void>;
  searchTasks: (query: string) => Promise<void>;
  fetchTaskAnalytics: () => Promise<void>;

  // Actions - UI state
  setStatusFilter: (status: string | null) => void;
  setPriorityFilter: (priority: string | null) => void;
  setSearchQuery: (query: string) => void;
  setCurrentTask: (task: Task | null) => void;
  clearError: () => void;

  // Selectors
  getTasksByStatus: (status: string) => Task[];
  getTasksByPriority: (priority: string) => Task[];
  getFilteredTasks: () => Task[];
}

export const useTaskStore = create<TaskState>()(
  devtools(
    (set, get) => ({
      // Initial state
      tasks: [],
      currentTask: null,
      overdueTasks: [],
      upcomingTasks: [],
      analytics: null,
      isLoading: false,
      error: null,

      // Filter state
      statusFilter: null,
      priorityFilter: null,
      searchQuery: '',

      // Task CRUD actions
      fetchTasks: async (filters = {}) => {
        set({ isLoading: true, error: null });

        try {
          const tasks = await api.getTasks(filters);
          set({ tasks, isLoading: false });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to fetch tasks',
            isLoading: false
          });
        }
      },

      createTask: async (taskData: TaskCreateRequest) => {
        set({ isLoading: true, error: null });

        try {
          const newTask = await api.createTask(taskData);

          set(state => ({
            tasks: [newTask, ...state.tasks],
            isLoading: false
          }));

          return newTask;
        } catch (error: any) {
          set({
            error: error.message || 'Failed to create task',
            isLoading: false
          });
          throw error;
        }
      },

      updateTask: async (taskId: string, updates: TaskUpdateRequest) => {
        set({ isLoading: true, error: null });

        try {
          const updatedTask = await api.updateTask(taskId, updates);

          set(state => ({
            tasks: state.tasks.map(task =>
              task.id === taskId ? updatedTask : task
            ),
            currentTask: state.currentTask?.id === taskId ? updatedTask : state.currentTask,
            isLoading: false
          }));

          return updatedTask;
        } catch (error: any) {
          set({
            error: error.message || 'Failed to update task',
            isLoading: false
          });
          throw error;
        }
      },

      deleteTask: async (taskId: string) => {
        set({ isLoading: true, error: null });

        try {
          await api.deleteTask(taskId);

          set(state => ({
            tasks: state.tasks.filter(task => task.id !== taskId),
            currentTask: state.currentTask?.id === taskId ? null : state.currentTask,
            isLoading: false
          }));
        } catch (error: any) {
          set({
            error: error.message || 'Failed to delete task',
            isLoading: false
          });
          throw error;
        }
      },

      assignTask: async (taskId: string, assigneeId: string) => {
        try {
          const updatedTask = await api.assignTask(taskId, assigneeId);

          set(state => ({
            tasks: state.tasks.map(task =>
              task.id === taskId ? updatedTask : task
            )
          }));

          return updatedTask;
        } catch (error: any) {
          set({ error: error.message || 'Failed to assign task' });
          throw error;
        }
      },

      completeTask: async (taskId: string) => {
        try {
          const completedTask = await api.completeTask(taskId);

          set(state => ({
            tasks: state.tasks.map(task =>
              task.id === taskId ? completedTask : task
            )
          }));

          return completedTask;
        } catch (error: any) {
          set({ error: error.message || 'Failed to complete task' });
          throw error;
        }
      },

      // Task query actions
      fetchOverdueTasks: async () => {
        try {
          const overdueTasks = await api.getOverdueTasks();
          set({ overdueTasks });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch overdue tasks' });
        }
      },

      fetchUpcomingTasks: async (days = 7) => {
        try {
          const upcomingTasks = await api.getUpcomingTasks(days);
          set({ upcomingTasks });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch upcoming tasks' });
        }
      },

      searchTasks: async (query: string) => {
        set({ isLoading: true, error: null, searchQuery: query });

        try {
          const tasks = await api.searchTasks(query);
          set({ tasks, isLoading: false });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to search tasks',
            isLoading: false
          });
        }
      },

      fetchTaskAnalytics: async () => {
        try {
          const analytics = await api.getTaskAnalytics();
          set({ analytics });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch task analytics' });
        }
      },

      // UI state actions
      setStatusFilter: (status: string | null) => {
        set({ statusFilter: status });
      },

      setPriorityFilter: (priority: string | null) => {
        set({ priorityFilter: priority });
      },

      setSearchQuery: (query: string) => {
        set({ searchQuery: query });
      },

      setCurrentTask: (task: Task | null) => {
        set({ currentTask: task });
      },

      clearError: () => {
        set({ error: null });
      },

      // Selectors
      getTasksByStatus: (status: string) => {
        const { tasks } = get();
        return tasks.filter(task => task.status === status);
      },

      getTasksByPriority: (priority: string) => {
        const { tasks } = get();
        return tasks.filter(task => task.priority === priority);
      },

      getFilteredTasks: () => {
        const { tasks, statusFilter, priorityFilter, searchQuery } = get();

        return tasks.filter(task => {
          // Status filter
          if (statusFilter && task.status !== statusFilter) {
            return false;
          }

          // Priority filter
          if (priorityFilter && task.priority !== priorityFilter) {
            return false;
          }

          // Search query
          if (searchQuery) {
            const query = searchQuery.toLowerCase();
            return (
              task.title.toLowerCase().includes(query) ||
              task.description.toLowerCase().includes(query)
            );
          }

          return true;
        });
      }
    }),
    {
      name: 'task-store'
    }
  )
);
