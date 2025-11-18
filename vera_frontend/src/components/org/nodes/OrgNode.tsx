/**
 * Org Node Component
 * Custom node for organizational hierarchy visualization
 */
import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Building2, FolderKanban, Users, User, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { NodeData } from '@/types/org';
import { cn } from '@/lib/utils';

export function OrgNode({ data }: NodeProps<NodeData>) {
  // Get icon based on node type
  const getIcon = () => {
    switch (data.type) {
      case 'company':
        return <Building2 className="h-5 w-5" />;
      case 'project':
        return <FolderKanban className="h-5 w-5" />;
      case 'team':
        return <Users className="h-5 w-5" />;
      case 'user':
        return <User className="h-5 w-5" />;
    }
  };

  // Get color scheme based on node type
  const getColorScheme = () => {
    switch (data.type) {
      case 'company':
        return {
          bg: 'bg-gradient-to-br from-purple-500 to-indigo-600',
          border: 'border-purple-300',
          text: 'text-purple-700',
          bgLight: 'bg-purple-50',
        };
      case 'project':
        return {
          bg: 'bg-gradient-to-br from-blue-500 to-cyan-600',
          border: 'border-blue-300',
          text: 'text-blue-700',
          bgLight: 'bg-blue-50',
        };
      case 'team':
        return {
          bg: 'bg-gradient-to-br from-green-500 to-emerald-600',
          border: 'border-green-300',
          text: 'text-green-700',
          bgLight: 'bg-green-50',
        };
      case 'user':
        return {
          bg: 'bg-gradient-to-br from-orange-500 to-amber-600',
          border: 'border-orange-300',
          text: 'text-orange-700',
          bgLight: 'bg-orange-50',
        };
    }
  };

  const colors = getColorScheme();
  const completionRate = data.task_count > 0
    ? Math.round((data.completed_tasks / data.task_count) * 100)
    : 0;

  return (
    <>
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-gray-400" />

      <Card className={cn('min-w-[250px] shadow-lg hover:shadow-xl transition-all duration-200', colors.border)}>
        <CardContent className="p-4">
          {/* Header */}
          <div className="flex items-start gap-3 mb-3">
            <div className={cn('p-2 rounded-lg text-white', colors.bg)}>
              {getIcon()}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-sm truncate">{data.label}</h3>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className="text-xs capitalize">
                  {data.type}
                </Badge>
                {data.online && (
                  <div className="flex items-center gap-1">
                    <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-xs text-green-600">Online</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Role (for users) */}
          {data.role && (
            <div className="mb-2">
              <Badge variant="secondary" className="text-xs">
                {data.role}
              </Badge>
            </div>
          )}

          {/* Team size (for teams) */}
          {data.team_size !== undefined && data.team_size > 0 && (
            <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
              <Users className="h-3 w-3" />
              <span>{data.team_size} member{data.team_size === 1 ? '' : 's'}</span>
            </div>
          )}

          {/* Task Statistics */}
          {data.task_count > 0 && (
            <div className={cn('rounded-md p-2 mt-2', colors.bgLight)}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium">Tasks</span>
                <Badge variant="secondary" className="text-xs">
                  {data.task_count}
                </Badge>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div
                  className={cn('h-2 rounded-full transition-all duration-300', colors.bg)}
                  style={{ width: `${completionRate}%` }}
                />
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-1 text-xs">
                <div className="flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3 text-green-600" />
                  <span className="text-green-600">{data.completed_tasks}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3 text-blue-600" />
                  <span className="text-blue-600">{data.task_count - data.completed_tasks - data.overdue_tasks}</span>
                </div>
                <div className="flex items-center gap-1">
                  <AlertCircle className="h-3 w-3 text-red-600" />
                  <span className="text-red-600">{data.overdue_tasks}</span>
                </div>
              </div>

              <div className="text-xs text-center mt-2 font-medium" style={{ color: colors.text.replace('text-', '') }}>
                {completionRate}% Complete
              </div>
            </div>
          )}

          {/* Description */}
          {data.description && (
            <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
              {data.description}
            </p>
          )}
        </CardContent>
      </Card>

      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-gray-400" />
    </>
  );
}

export default OrgNode;
