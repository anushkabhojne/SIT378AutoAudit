// types/dashboard.types.ts

/**
 * dashboard.types.ts
 * 
 * TypeScript type definitions and interfaces for the AutoAudit Compliance Dashboard.
 * Includes types for compliance metrics, alerts, user permissions, accessibility preferences, and more.
 * 
 * @author Senior Lead, AutoAudit
 */

/**
 * Severity levels for compliance controls and alerts
 */

export type SeverityLabel = 'Critical' | 'High' | 'Medium' | 'Low';

/**
 * Compliance status for controls
 */

export type ComplianceStatus = 'Compliant' | 'Non-Compliant' | 'Under Review' | 'Not Applicable';

/**
 * Interface representing a single compliance control metric
 */

export interface ComplianceControlMetric {
  id: string;
  name: string;
  severity: SeverityLabel;
  status: ComplianceStatus;

  //ISO 8601 timestamp
  lastUpdated: string; 

  description?: string;
}

/**
 * Interface representing the aggregated compliance metrics
 */

export interface ComplianceMetrics {
  totalControls: number;
  compliantControls: number;
  nonCompliantControls: number;
  controls: ComplianceControlMetric[];

  //ISO 8601 timestamp
  lastAssessmentDate: string; 
}

/**
 * Interface representing a compliance alert or finding
 */

export interface ComplianceAlert {
  id: string;
  title: string;
  description: string;
  severityLabel: SeverityLabel;

  //ISO 8601 timestamp when alert was generated
  timestamp: string; 

  acknowledged: boolean;
  resolved: boolean;
  relatedControlId?: string;
}

/**
 * User permissions relevant to the dashboard features
 */

export interface UserPermissions {
  canAcknowledgeAlerts: boolean;
  canResolveAlerts: boolean;
  canViewDetailedMetrics: boolean;

  //Optional auth token for API requests
  authToken?: string; 
}

/**
 * Accessibility preferences detected or set by the user
 */

export interface AccessibilityPreferences {
  prefersReducedMotion: boolean;
  prefersHighContrast: boolean;

  //e.g., 1.0 = normal, 1.2 = 20% larger
  fontSizeScale: number; 
}

/**
 * Interface for dashboard configuration options
 */

export interface DashboardConfig {
  refreshIntervalMs: number;
  maxAlertDisplayCount: number;
  enablePerformanceMetrics: boolean;
  enableAccessibilityFeatures: Boolean;
}
