//components/ComplianceSummary.tsx

/**
 * ComplianceSummary.tsx
 * 
 * React component to display a summary of compliance metrics.
 * Showing the overall compliance percentage, counts of compliant and non-compliant controls,
 * and last assessment date.
 * 
 * @author Senior Lead, AutoAudit
 */

import React, { useEffect } 

from 'react';

import { ComplianceMetrics } 

from '../types/dashboard.types';

import { calculateCompliancePercentage, formatMetricDisplay } 

from '../utils/complianceCalculations';

interface ComplianceSummaryProps {
  complianceMetrics: ComplianceMetrics | null;
  isLoading: boolean;
  error: Error | null;
}

/**
 * ComplianceSummary component
 * 
 * @param props ComplianceSummaryProps
 * @returns JSX.Element
 */

export const ComplianceSummary: React.FC<ComplianceSummaryProps> = ({
  complianceMetrics,
  isLoading,
  error,
}) => {
  
  //Calculating the compliance percentage, if the data is available
  const compliancePercentage = complianceMetrics
    ? calculateCompliancePercentage(
        complianceMetrics.compliantControls,
        complianceMetrics.totalControls
      )
    : 0;

  //Formatting the last assessment date
  const lastAssessmentDate = complianceMetrics
    ? new Date(complianceMetrics.lastAssessmentDate).toLocaleString()
    : 'N/A';

  //Accessibility: aria-live region for dynamic updates
  useEffect(() => {
    //Could add side effects or analytics here if needed
  }, [compliancePercentage, lastAssessmentDate]);

  if (isLoading) {
    return <div role = "status" aria-live = "polite">Loading compliance summary...</div>;
  }

  if (error) {
    
    return (
      
      <div role = "alert" aria-live = "assertive" style = {{ color: 'red' }}>
        Error loading compliance summary: {error.message}
      </div>

    );
  }

  if (!complianceMetrics) {
    return <div>No compliance data available.</div>;
  }

  return (
    <section aria-label = "Compliance Summary" className = "compliance-summary">
      <h2>Compliance Summary</h2>
      <p>
        Overall Compliance:{' '}
        <strong aria-live = "polite" aria-atomic = "true">
          {formatMetricDisplay(compliancePercentage, 'percentage')}
        </strong>
      </p>
      <p>
        Compliant Controls:{' '}
        <strong>{formatMetricDisplay(complianceMetrics.compliantControls, 'count')}</strong>
      </p>
      <p>
        Non-Compliant Controls:{' '}
        <strong>{formatMetricDisplay(complianceMetrics.nonCompliantControls, 'count')}</strong>
      </p>
      <p>Last Assessment Date: {lastAssessmentDate}</p>
    </section>
  );
};
