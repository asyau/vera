/**
 * Organizational Hierarchy Graph Component
 * Visualizes company structure with React Flow
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionLineType,
  MarkerType,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Loader2, RefreshCw, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { api } from '@/services/api';
import { OrgNode } from './nodes/OrgNode';
import { NodeData, OrgGraphFilters } from '@/types/org';

const nodeTypes = {
  orgNode: OrgNode,
};

const defaultEdgeOptions = {
  type: 'smoothstep',
  markerEnd: {
    type: MarkerType.ArrowClosed,
    width: 20,
    height: 20,
  },
  style: {
    strokeWidth: 2,
  },
};

interface OrgHierarchyGraphProps {
  className?: string;
  height?: string;
  defaultFilters?: OrgGraphFilters;
}

export function OrgHierarchyGraph({
  className,
  height = '600px',
  defaultFilters,
}: OrgHierarchyGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState<OrgGraphFilters>(defaultFilters || { depth: 5, include_users: true });
  const [stats, setStats] = useState({ total_nodes: 0, total_edges: 0, depth: 0 });

  // Fetch org graph data
  const fetchOrgGraph = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.getOrgGraph(filters);

      // Transform nodes for React Flow
      const flowNodes: Node[] = response.nodes.map((node, index) => ({
        id: node.id,
        type: 'orgNode',
        data: node,
        position: { x: 0, y: 0 }, // Will be auto-laid out
      }));

      // Transform edges for React Flow
      const flowEdges: Edge[] = response.edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        type: 'smoothstep',
        animated: edge.type === 'manages',
        ...defaultEdgeOptions,
      }));

      // Apply hierarchical layout
      const layoutedNodes = applyHierarchicalLayout(flowNodes, flowEdges);

      setNodes(layoutedNodes);
      setEdges(flowEdges);
      setStats(response.stats);
      toast.success('Organization graph loaded successfully');
    } catch (error: any) {
      console.error('Failed to fetch org graph:', error);
      toast.error('Failed to load organization graph');
    } finally {
      setIsLoading(false);
    }
  }, [filters, setNodes, setEdges]);

  // Initial load
  useEffect(() => {
    fetchOrgGraph();
  }, [fetchOrgGraph]);

  // Apply hierarchical layout to nodes
  const applyHierarchicalLayout = (nodes: Node[], edges: Edge[]): Node[] => {
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const childrenMap = new Map<string, string[]>();
    const levelMap = new Map<string, number>();

    // Build parent-child relationships
    edges.forEach(edge => {
      if (!childrenMap.has(edge.source)) {
        childrenMap.set(edge.source, []);
      }
      childrenMap.get(edge.source)!.push(edge.target);
    });

    // Find root nodes (nodes with no incoming edges)
    const targetIds = new Set(edges.map(e => e.target));
    const rootNodes = nodes.filter(n => !targetIds.has(n.id));

    // Assign levels using BFS
    const queue: Array<{ id: string; level: number }> = rootNodes.map(n => ({ id: n.id, level: 0 }));
    while (queue.length > 0) {
      const { id, level } = queue.shift()!;
      levelMap.set(id, level);
      const children = childrenMap.get(id) || [];
      children.forEach(childId => {
        queue.push({ id: childId, level: level + 1 });
      });
    }

    // Position nodes by level
    const levelWidth = 350;
    const levelHeight = 250;
    const levelNodes = new Map<number, string[]>();

    levelMap.forEach((level, id) => {
      if (!levelNodes.has(level)) {
        levelNodes.set(level, []);
      }
      levelNodes.get(level)!.push(id);
    });

    // Calculate positions
    return nodes.map(node => {
      const level = levelMap.get(node.id) || 0;
      const nodesAtLevel = levelNodes.get(level) || [];
      const indexInLevel = nodesAtLevel.indexOf(node.id);
      const totalAtLevel = nodesAtLevel.length;

      return {
        ...node,
        position: {
          x: (indexInLevel - (totalAtLevel - 1) / 2) * levelWidth,
          y: level * levelHeight,
        },
      };
    });
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Organization Hierarchy</CardTitle>
            <CardDescription>
              {stats.total_nodes} entities across {stats.depth} levels
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Select
              value={filters.depth?.toString() || '5'}
              onValueChange={(value) => setFilters({ ...filters, depth: parseInt(value) })}
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="Depth" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1 level</SelectItem>
                <SelectItem value="2">2 levels</SelectItem>
                <SelectItem value="3">3 levels</SelectItem>
                <SelectItem value="4">4 levels</SelectItem>
                <SelectItem value="5">5 levels</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchOrgGraph}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div style={{ height }} className="relative">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              connectionLineType={ConnectionLineType.SmoothStep}
              defaultEdgeOptions={defaultEdgeOptions}
              fitView
              attributionPosition="bottom-left"
              minZoom={0.1}
              maxZoom={2}
            >
              <Background />
              <Controls />
              <MiniMap
                nodeStrokeWidth={3}
                zoomable
                pannable
                className="bg-white/80 backdrop-blur-sm"
              />
              <Panel position="top-right" className="bg-white/80 backdrop-blur-sm p-2 rounded-md shadow">
                <div className="text-xs space-y-1">
                  <div className="font-semibold">Legend:</div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-purple-500" />
                    <span>Company</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-blue-500" />
                    <span>Project</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-green-500" />
                    <span>Team</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-orange-500" />
                    <span>User</span>
                  </div>
                </div>
              </Panel>
            </ReactFlow>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default OrgHierarchyGraph;
