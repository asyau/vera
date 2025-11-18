/**
 * Organization Hierarchy Page
 * Full-screen view of the organizational structure
 */
import React from 'react';
import { OrgHierarchyGraph } from '@/components/org/OrgHierarchyGraph';

export default function OrgHierarchy() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Organization Hierarchy</h1>
        <p className="text-muted-foreground mt-2">
          Visualize your company structure, teams, and workload distribution
        </p>
      </div>

      <OrgHierarchyGraph height="calc(100vh - 240px)" />
    </div>
  );
}
