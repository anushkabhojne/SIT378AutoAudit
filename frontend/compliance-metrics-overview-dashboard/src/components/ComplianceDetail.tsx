//components/ComplianceDetail.tsx

/**
 * ComplianceDetail.tsx
 * 
 * React component to display the detailed compliance control metrics in a table.
 * Supports sorting by severity, status, and last updated date.
 * Accessible with keyboard navigation and screen reader support.
 * 
 * @author Senior Lead, AutoAudit
 */

import React, { useState, useMemo } from 'react';
import { ComplianceControlMetric, SeverityLabel, ComplianceStatus } from '../types/dashboard.types';

interface ComplianceDetailProps {
  controls: ComplianceControlMetric[];
  isLoading: boolean;
  error: Error | null;
}

type SortKey = 'name' | 'severity' | 'status' | 'lastUpdated';
type SortDirection = 'asc' | 'desc';

const severityOrder: Record<SeverityLabel, number> = {
  Critical: 4,
  High: 3,
  Medium: 2,
  Low: 1,
};

const statusOrder: Record<ComplianceStatus, number> = {
  'Non-Compliant': 4,
  'Under Review': 3,
  Compliant: 2,
  'Not Applicable': 1,
};

/**
 * ComplianceDetail component
 * 
 * @param props ComplianceDetailProps
 * @returns JSX.Element
 */

export const ComplianceDetail: React.FC<ComplianceDetailProps> = ({ controls, isLoading, error }) => {
  
  const [sortKey, setSortKey] = useState<SortKey>('severity');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  /**
   * Handling sorting the column header click
   * @param key SortKey
   */

  const handleSort = (key: SortKey) => {
    
    if (sortKey === key) {
      //Toggle direction
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } 
    
    else {
      setSortKey(key);
      setSortDirection('asc');
    }
  };

  /**
   * Sorting the controls based on current sortKey and sortDirection
   */

  const sortedControls = useMemo(() => {
    
    const sorted = [...controls];
    sorted.sort((a, b) => {

      let compare = 0;
      
      switch (sortKey) {
        
        case 'name':
          compare = a.name.localeCompare(b.name);
          break;
        
        case 'severity':
          compare = severityOrder[a.severity] - severityOrder[b.severity];
          break;
        
        case 'status':
          compare = statusOrder[a.status] - statusOrder[b.status];
          break;
        
        case 'lastUpdated':
          compare = new Date(a.lastUpdated).getTime() - new Date(b.lastUpdated).getTime();
          break;
      }

      return sortDirection === 'asc' ? compare : -compare;

    });

    return sorted;

  }, [controls, sortKey, sortDirection]);

  if (isLoading) {
    return <div role = "status" aria-live = "polite">Loading compliance details...</div>;
  }

  if (error) {
    
    return (
      <div role = "alert" aria-live = "assertive" style = {{ color: 'red' }}>
        Error loading compliance details: {error.message}
      </div>
    );

  }

  if (controls.length === 0) {
    return <div>No compliance controls available.</div>;
  }

  return (
    <section aria-label = "Compliance Details" className = "compliance-detail">
      <h2>Compliance Details</h2>
      <table role = "grid" aria-rowcount = {controls.length + 1} aria-colcount = {5}>
        <thead>
          <tr>
            <th
              role = "columnheader"
              tabIndex = {0}
              onClick = {() => handleSort('name')}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleSort('name'); }}
              aria-sort = {sortKey === 'name' ? sortDirection : 'none'}
              scope = "col"
            >
              Control Name
            </th>
            <th
              role = "columnheader"
              tabIndex = {0}
              onClick = {() => handleSort('severity')}
              onKeyDown = {(e) => { if (e.key === 'Enter' || e.key === ' ') handleSort('severity'); }}
              aria-sort = {sortKey === 'severity' ? sortDirection : 'none'}
              scope = "col"
            >
              Severity
            </th>
            <th
              role = "columnheader"
              tabIndex = {0}
              onClick = {() => handleSort('status')}
              onKeyDown = {(e) => { if (e.key === 'Enter' || e.key === ' ') handleSort('status'); }}
              aria-sort = {sortKey === 'status' ? sortDirection : 'none'}
              scope = "col"
            >
              Status
            </th>
            <th
              role = "columnheader"
              tabIndex = {0}
              onClick = {() => handleSort('lastUpdated')}
              onKeyDown = {(e) => { if (e.key === 'Enter' || e.key === ' ') handleSort('lastUpdated'); }}
              aria-sort = {sortKey === 'lastUpdated' ? sortDirection : 'none'}
              scope = "col"
            >
              Last Updated
            </th>
            <th scope = "col">Description</th>
          </tr>
        </thead>
        <tbody>
          {sortedControls.map((control) => (
            <tr key = {control.id} role="row">
              <td role = "gridcell">{control.name}</td>
              <td role = "gridcell">{control.severity}</td>
              <td role = "gridcell">{control.status}</td>
              <td role = "gridcell">{new Date(control.lastUpdated).toLocaleString()}</td>
              <td role = "gridcell">{control.description ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
};
