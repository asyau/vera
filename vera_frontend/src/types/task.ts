/**
 * Task-related type definitions
 */

export interface Task {
  id: string;
  name: string; // Changed from title to match backend
  description: string;
  created_by: string; // Changed from creator_id to match backend
  assigned_to: string | null; // Changed from assignee_id to match backend
  project_id: string | null;
  status: 'pending' | 'in-progress' | 'complete' | 'cancelled'; // Updated to match backend statuses
  priority: 'low' | 'medium' | 'high';
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreateRequest {
  name: string; // Changed from title to match backend
  description: string;
  assigned_to?: string; // Changed from assignee_id to match backend
  project_id?: string;
  due_date?: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface TaskUpdateRequest {
  name?: string; // Changed from title to match backend
  description?: string;
  assigned_to?: string; // Changed from assignee_id to match backend
  project_id?: string;
  due_date?: string;
  priority?: 'low' | 'medium' | 'high';
  status?: 'pending' | 'in-progress' | 'complete' | 'cancelled'; // Updated to match backend
}

export interface TaskAnalytics {
  total_tasks: number;
  completed_tasks: number;
  completion_rate: number;
  overdue_tasks: number;
  upcoming_tasks: number;
  status_breakdown: Record<string, number>;
}
