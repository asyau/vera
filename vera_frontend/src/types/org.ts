/**
 * Organizational Hierarchy Types
 * Type definitions for org hierarchy graph visualization
 */

export type NodeType = 'company' | 'project' | 'team' | 'user';
export type EdgeType = 'manages' | 'belongs_to' | 'supervises' | 'works_on';

export interface NodeData {
  id: string;
  label: string;
  type: NodeType;
  role?: string;
  email?: string;
  task_count: number;
  completed_tasks: number;
  overdue_tasks: number;
  team_size?: number;
  online: boolean;
  avatar_url?: string;
  description?: string;
}

export interface EdgeData {
  id: string;
  source: string;
  target: string;
  label?: string;
  type: EdgeType;
}

export interface OrgGraphResponse {
  nodes: NodeData[];
  edges: EdgeData[];
  stats: {
    total_nodes: number;
    total_edges: number;
    depth: number;
  };
}

export interface UserWorkload {
  user_id: string;
  user_name: string;
  total_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  completion_rate: number;
}

export interface TeamWorkload {
  team_id: string;
  team_name: string;
  total_tasks: number;
  total_members: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  avg_completion_rate: number;
  members: UserWorkload[];
}

export interface OrgGraphFilters {
  company_id?: string;
  project_id?: string;
  team_id?: string;
  depth?: number;
  include_users?: boolean;
}
