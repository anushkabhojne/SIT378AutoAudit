//hooks/usePerformanceMetrics.ts

/**
 * usePerformanceMetrics.ts
 * 
 * Custom React hook to collect, record, and expose performance metrics for the dashboard.
 * Metrics include load times, render counts, and user interaction latencies.
 * Designed for integration with monitoring and analytics systems.
 * 
 * @author Senior Lead, AutoAudit
 */

import { useRef, useCallback } from 'react';

interface PerformanceMetrics {
  loadTimeMs: number | null;
  renderCount: number;
  interactionLatencies: Record<string, number[]>;
}

/**
 * usePerformanceMetrics hook implementation
 * 
 * Providing methods to record metrics and retrieve the aggregated data.
 */

export function usePerformanceMetrics() {
  
  //Ref to store metrics state
  const metricsRef = useRef<PerformanceMetrics>({
    loadTimeMs: null,
    renderCount: 0,
    interactionLatencies: {},
  });

  /**
   * Recording the page load time in milliseconds
   * @param ms Loading time in milliseconds
   */

  const recordLoadTime = useCallback((ms: number) => {
    metricsRef.current.loadTimeMs = ms;
  }, []);

  /**
   * Incrementing the render count by one
   */

  const incrementRenderCount = useCallback(() => {
    metricsRef.current.renderCount += 1;
  }, []);

  /**
   * Recording the user interaction latency for a given interaction type
   * @param interactionType String identifier for interaction (e.g., 'filterChange')
   * @param latencyMs Latency in milliseconds
   */

  const recordInteractionLatency = useCallback((interactionType: string, latencyMs: number) => {
    
    if (!metricsRef.current.interactionLatencies[interactionType]) {
      metricsRef.current.interactionLatencies[interactionType] = [];
    }

    metricsRef.current.interactionLatencies[interactionType].push(latencyMs);

  }, []);

  /**
   * Getting the current aggregated metrics snapshot
   */

  const getMetrics = useCallback(() => {
    
    //Calculating the average Latency per interaction type
    const avgLatencies: Record<string, number> = {};
    
    for (const [key, latencies] of Object.entries(metricsRef.current.interactionLatencies)) {
      
      if (latencies.length > 0) {
        const sum = latencies.reduce((acc, val) => acc + val, 0);
        avgLatencies[key] = sum / latencies.length;
      } 
      
      else {
        avgLatencies[key] = 0;
      }
    }

    return {
      loadTimeMs: metricsRef.current.loadTimeMs,
      renderCount: metricsRef.current.renderCount,
      averageInteractionLatenciesMs: avgLatencies,
    };
    
  }, []);

  return {
    recordLoadTime,
    incrementRenderCount,
    recordInteractionLatency,
    getMetrics,
  };
}
