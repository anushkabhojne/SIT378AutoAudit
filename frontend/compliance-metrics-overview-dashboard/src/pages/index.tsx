//pages/index.tsx

/**
 * index.tsx
 * 
 * Main entry page for the AutoAudit Compliance Dashboard.
 * Integrates all components: ComplianceSummary, ComplianceDetail, AlertList,
 * PerformanceMetrics, and AccessibilitySettings.
 * Handles data fetching, state management, and user interactions.
 * 
 * @author Senior Lead, AutoAudit
 */

import React, { useEffect, useState, useCallback } from 'react';
import { ComplianceMetrics, ComplianceControlMetric, ComplianceAlert, UserPermissions } from '../types/dashboard.types';
import { ComplianceSummary } from '../components/ComplianceSummary';
import { ComplianceDetail } from '../components/ComplianceDetail';
import { AlertList } from '../components/AlertList';
import { PerformanceMetrics } from '../components/PerformanceMetrics';
import { AccessibilitySettings } from '../components/AccessibilitySettings';

//PLACEHOLDER: Simulated API endpoints, to be replaced with real API calls
const API_ENDPOINTS = {
  complianceMetrics: '/api/compliance/metrics',
  complianceControls: '/api/compliance/controls',
  complianceAlerts: '/api/compliance/alerts',
};

/**
 * Fetching the JSON helper with error handling
 * @param url string
 * @param authToken optional string
 */

async function fetchJson<T>(url: string, authToken?: string): Promise<T> {
  
  const headers: HeadersInit = authToken ? { Authorization: `Bearer ${authToken}` } : {};
  const response = await fetch(url, { headers });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Main Dashboard Page component
 * 
 * @returns JSX.Element
 */

const DashboardPage: React.FC = () => {
  
  //State for compliance metrics summary
  const [complianceMetrics, setComplianceMetrics] = useState<ComplianceMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState<boolean>(true);
  const [metricsError, setMetricsError] = useState<Error | null>(null);

  //State for compliance controls detail
  const [complianceControls, setComplianceControls] = useState<ComplianceControlMetric[]>([]);
  const [controlsLoading, setControlsLoading] = useState<boolean>(true);
  const [controlsError, setControlsError] = useState<Error | null>(null);

  //State for compliance alerts
  const [alerts, setAlerts] = useState<ComplianceAlert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState<boolean>(true);
  const [alertsError, setAlertsError] = useState<Error | null>(null);

  //User permissions to simulate fetching or from auth context
  const [userPermissions] = useState<UserPermissions>({
    canAcknowledgeAlerts: true,
    canResolveAlerts: true,
    canViewDetailedMetrics: true,
  });

  //Fetching the  compliance metrics summary
  const fetchComplianceMetrics = useCallback(async () => {
    
    setMetricsLoading(true);
    setMetricsError(null);
    
    try {
      const data = await fetchJson<ComplianceMetrics>(API_ENDPOINTS.complianceMetrics);
      setComplianceMetrics(data);
    } 
    
    catch (error) {
      setMetricsError(error as Error);
    } 
    
    finally {
      setMetricsLoading(false);
    }
  }, []);

  //Fetching the compliance controls detail
  const fetchComplianceControls = useCallback(async () => {
    
    setControlsLoading(true);
    setControlsError(null);
    
    try {
      const data = await fetchJson<ComplianceControlMetric[]>(API_ENDPOINTS.complianceControls);
      setComplianceControls(data);
    } 
    
    catch (error) {
      setControlsError(error as Error);
    } 
    
    finally {
      setControlsLoading(false);
    }
  }, []);

  //Fetching the compliance alerts
  const fetchComplianceAlerts = useCallback(async () => {
    
    setAlertsLoading(true);
    setAlertsError(null);
    
    try {
      const data = await fetchJson<ComplianceAlert[]>(API_ENDPOINTS.complianceAlerts);
      setAlerts(data);
    } 
    
    catch (error) {
      setAlertsError(error as Error);
    } 
    
    finally {
      setAlertsLoading(false);
    }
  }, []);

  //Initial data fetch on mount
  useEffect(() => {
    fetchComplianceMetrics();
    fetchComplianceControls();
    fetchComplianceAlerts();
  }, [fetchComplianceMetrics, fetchComplianceControls, fetchComplianceAlerts]);

  //Handlers for acknowledging and resolving alerts
  const handleAcknowledge = async (alertId: string) => {
    
    //Simulating the API call to acknowledge the alert
    try {
      
      //PLACEHOLDER: To be replaced with the real API call
      await new Promise((resolve) => setTimeout(resolve, 500));
      
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        )
      );
    } 
    
    catch {
      //Handle the error (e.g., show notification)
    }
  };

  const handleResolve = async (alertId: string) => {
    //Simulating the API call to resolve the alert
    
    try {
      //PLACEHOLDER: To be replaced with the real API call
      
      await new Promise((resolve) => setTimeout(resolve, 500));
      
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId ? { ...alert, resolved: true } : alert
        )
      );
    } 
    
    catch {
      //Handle the error (e.g., show notification)
    }
  };

  return (
    <main className = "dashboard-page" role = "main">
      <h1>AutoAudit Compliance Dashboard</h1>

      <AccessibilitySettings />

      <ComplianceSummary
        complianceMetrics = {complianceMetrics}
        isLoading = {metricsLoading}
        error = {metricsError}
      />

      {userPermissions.canViewDetailedMetrics && (
        <ComplianceDetail
          controls = {complianceControls}
          isLoading = {controlsLoading}
          error = {controlsError}
        />
      )}

      <AlertList
        alerts={alerts}
        userPermissions = {userPermissions}
        isLoading = {alertsLoading}
        error = {alertsError}
        onAcknowledge = {handleAcknowledge}
        onResolve = {handleResolve}
      />

      <PerformanceMetrics />
    </main>
  );
};

export default DashboardPage;
