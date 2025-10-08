//components/PerformanceMetrics.tsx

/**
 * PerformanceMetrics.tsx
 * 
 * React component to display performance metrics such as page load time,
 * API response times and resource usage.
 * Supports real-time updates and accessibility features.
 * 
 * @author Senior Lead, AutoAudit
 */

import React, { useEffect, useState } from 'react';

interface PerformanceMetricsData {
  pageLoadTimeMs: number;
  apiResponseTimeMs: number;
  memoryUsageMb: number;
}

interface PerformanceMetricsProps {
  refreshIntervalMs?: number;
}

/**
 * PerformanceMetrics component
 * 
 * @param props PerformanceMetricsProps
 * @returns JSX.Element
 */

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
  refreshIntervalMs = 5000,
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetricsData>({
    pageLoadTimeMs: 0,
    apiResponseTimeMs: 0,
    memoryUsageMb: 0,
  });

  /**
   * Function to simulate fetching performance metrics.
   * Replace with real data fetching in production.
   */

  const fetchPerformanceMetrics = () => {
    
    //Simulated data for demonstration
    const simulatedMetrics: PerformanceMetricsData = {
      
      pageLoadTimeMs: window.performance.timing.loadEventEnd - window.performance.timing.navigationStart || 0,
      apiResponseTimeMs: Math.random() * 300 + 100, //Simulated 100-400ms
      
      memoryUsageMb:
        (performance as any)?.memory
          ? ((performance as any).memory.usedJSHeapSize / 1024 / 1024).toFixed(2)
          : 0,
    };
    
    setMetrics({
      pageLoadTimeMs: simulatedMetrics.pageLoadTimeMs,
      apiResponseTimeMs: simulatedMetrics.apiResponseTimeMs,
      memoryUsageMb: Number(simulatedMetrics.memoryUsageMb),
    });
  };

  useEffect(() => {
    fetchPerformanceMetrics();
    const interval = setInterval(fetchPerformanceMetrics, refreshIntervalMs);
    return () => clearInterval(interval);
  }, [refreshIntervalMs]);

  return (
    <section aria-label = "Performance Metrics" className = "performance-metrics">
      <h2>Performance Metrics</h2>
      <ul>
        <li>
          <strong>Page Load Time:</strong>{' '}
          <span aria-live = "polite" aria-atomic="true">
            {metrics.pageLoadTimeMs > 0 ? `${metrics.pageLoadTimeMs.toFixed(0)} ms` : 'N/A'}
          </span>
        </li>
        <li>
          <strong>API Response Time:</strong>{' '}
          <span aria-live="polite" aria-atomic="true">
            {metrics.apiResponseTimeMs.toFixed(0)} ms
          </span>
        </li>
        <li>
          <strong>Memory Usage:</strong>{' '}
          <span aria-live="polite" aria-atomic="true">
            {metrics.memoryUsageMb > 0 ? `${metrics.memoryUsageMb.toFixed(2)} MB` : 'N/A'}
          </span>
        </li>
      </ul>
    </section>
  );
};
