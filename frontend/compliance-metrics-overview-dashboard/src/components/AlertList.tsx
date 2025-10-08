//components/AlertList.tsx

/**
 * AlertList.tsx
 * 
 * React component to display a list of compliance alerts.
 * Supporting filtering by severity and acknowledgment status.
 * Allowing users with permissions to acknowledge and resolve alerts.
 * Accessible with keyboard navigation and screen reader support.
 * 
 * @author Senior Lead, AutoAudit
 */

import React, { useState, useMemo } from 'react';
import { ComplianceAlert, SeverityLabel, UserPermissions } from '../types/dashboard.types';

interface AlertListProps {
  alerts: ComplianceAlert[];
  userPermissions: UserPermissions;
  isLoading: boolean;
  error: Error | null;
  onAcknowledge: (alertId: string) => void;
  onResolve: (alertId: string) => void;
}

const severityLevels: SeverityLabel[] = ['Critical', 'High', 'Medium', 'Low'];

/**
 * AlertList component
 * 
 * @param props AlertListProps
 * @returns JSX.Element
 */

export const AlertList: React.FC<AlertListProps> = ({
  alerts,
  userPermissions,
  isLoading,
  error,
  onAcknowledge,
  onResolve,
}) => {
  
  const [filterSeverity, setFilterSeverity] = useState<SeverityLabel | 'All'>('All');
  const [showAcknowledged, setShowAcknowledged] = useState<boolean>(true);

  /**
   * Filtering the alerts based on severity and acknowledgment status
   */

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const severityMatch = filterSeverity === 'All' || alert.severityLabel === filterSeverity;
      const acknowledgedMatch = showAcknowledged || !alert.acknowledged;
      return severityMatch && acknowledgedMatch;
    });

  }, [alerts, filterSeverity, showAcknowledged]);

  if (isLoading) {
    return <div role = "status" aria-live = "polite">Loading alerts...</div>;
  }

  if (error) {
    
    return (
      
      <div role = "alert" aria-live = "assertive" style = {{ color: 'red' }}>
        Error loading alerts: {error.message}
      </div>

    );
  }

  if (alerts.length === 0) {
    return <div>No alerts available.</div>;
  }

  return (
    <section aria-label = "Compliance Alerts" className = "alert-list">
      <h2>Compliance Alerts</h2>

      <form aria-label = "Filter alerts" className = "alert-filters" onSubmit = {(e) => e.preventDefault()}>
        <label htmlFor = "severityFilter">Filter by Severity:</label>
        <select
          id = "severityFilter"
          value = {filterSeverity}
          onChange = {(e) => setFilterSeverity(e.target.value as SeverityLabel | 'All')}
        >
          <option value = "All">All</option>
          {severityLevels.map((level) => (
            <option key = {level} value = {level}>
              {level}
            </option>
          ))}
        </select>

        <label htmlFor = "acknowledgedFilter" style = {{ marginLeft: '1rem' }}>
          Show Acknowledged:
        </label>
        <input
          id = "acknowledgedFilter"
          type = "checkbox"
          checked = {showAcknowledged}
          onChange = {(e) => setShowAcknowledged(e.target.checked)}
        />
      </form>

      <ul role = "list" className = "alert-items" aria-live = "polite" aria-relevant = "additions removals">
        {filteredAlerts.length === 0 ? (
          <li>No alerts match the selected filters.</li>
        ) : (
          filteredAlerts.map((alert) => (
            <li key = {alert.id} className={`alert-item alert-${alert.severityLabel.toLowerCase()}`}>
              <article aria-label = {`Alert: ${alert.title}`}>
                <h3>{alert.title}</h3>
                <p>{alert.description}</p>
                <p>
                  <strong>Severity:</strong> {alert.severityLabel}
                </p>
                <p>
                  <strong>Timestamp:</strong> {new Date(alert.timestamp).toLocaleString()}
                </p>
                <p>
                  <strong>Status:</strong>{' '}
                  {alert.resolved
                    ? 'Resolved'
                    : alert.acknowledged
                    ? 'Acknowledged'
                    : 'Unacknowledged'}
                </p>
                <div className = "alert-actions">
                  {userPermissions.canAcknowledgeAlerts && !alert.acknowledged && !alert.resolved && (
                    <button
                      type = "button"
                      onClick = {() => onAcknowledge(alert.id)}
                      aria-label = {`Acknowledge alert: ${alert.title}`}
                    >
                      Acknowledge
                    </button>
                  )}
                  {userPermissions.canResolveAlerts && !alert.resolved && (
                    <button
                      type = "button"
                      onClick = {() => onResolve(alert.id)}
                      aria-label = {`Resolve alert: ${alert.title}`}
                    >
                      Resolve
                    </button>
                  )}
                </div>
              </article>
            </li>
          ))
        )}
      </ul>
    </section>
  );
};
