// utils/complianceCalculations.ts

/**
 * complianceCalculations.ts
 * 
 * Utility functions for calculating the compliance metrics, risk scores,
 * and formatting metric values for display.
 * 
 * @author Senior Lead, AutoAudit
 */

/**
 * Calculating the compliance percentage given the compliant and total controls.
 * Returning a number between 0 and 100.
 * 
 * @param compliantCount Number of compliant controls
 * @param totalCount Total number of controls
 * @returns Compliance percentage (0-100)
 */

export function calculateCompliancePercentage(compliantCount: number, totalCount: number): number {
  
  if (totalCount <= 0) 
    return 0;

  return Math.min(Math.max((compliantCount / totalCount) * 100, 0), 100);
}

/**
 * Calculating a risk score based on the control's severity and compliance status.
 * Returning a numeric risk score, i.e., a higher score means higher risk.
 * 
 * @param severity Severity level ('Critical', 'High', 'Medium', 'Low')
 * @param status Compliance status ('Compliant', 'Non-Compliant', etc.)
 * @returns Risk score number
 */

export function calculateRiskScore(severity: string, status: string): number {
  
  const severityWeights: Record<string, number> = {
    Critical: 10,
    High: 7,
    Medium: 4,
    Low: 1,
  };

  const statusWeights: Record<string, number> = {
    'Non-Compliant': 1,
    'Under Review': 0.5,
    Compliant: 0,
    'Not Applicable': 0,
  };

  const severityWeight = severityWeights[severity] ?? 0;
  const statusWeight = statusWeights[status] ?? 0;

  return severityWeight * statusWeight;
}

/**
 * Formatting the metric value for display with appropriate units and precision.
 * Supports 'percentage', 'count', and 'riskScore' types.
 * 
 * @param value Numeric value to format
 * @param type Metric type string
 * @returns Formatted string
 */

export function formatMetricDisplay(value: number, type: 'percentage' | 'count' | 'riskScore'): string {
  
  switch (type) {
    
    case 'percentage':
      return `${value.toFixed(1)}%`;
    
      case 'count':
      return value.toString();
    
      case 'riskScore':
      return value.toFixed(2);
    
      default:
      return value.toString();
  }
}
