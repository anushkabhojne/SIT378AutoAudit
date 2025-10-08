//components/CriticalFindingsAlert.tsx

/**
 * CriticalFindingsAlert.tsx
 * 
 * Displaying a prioritised list of critical compliance alerts requiring immediate attention.
 * Supporting real-time alert updates, user acknowledgment, resolution tracking, and accessibility.
 * 
 * @author Senior Lead, AutoAudit
 */

import React, { memo, useCallback } from 'react';

import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Tooltip,
  useTheme,
} 

from '@mui/material';

import CheckCircleOutlineIcon 

from '@mui/icons-material/CheckCircleOutline';

import DoneOutlineIcon 

from '@mui/icons-material/DoneOutline';

import WarningAmberIcon 

from '@mui/icons-material/WarningAmber';

import ReportProblemIcon 

from '@mui/icons-material/ReportProblem';

import { ComplianceAlert, AccessibilityPreferences, UserPermissions } 

from '../types/dashboard.types';

import { formatMetricDisplay } 

from '../utils/complianceCalculations';

//Severity colour mapping for chips and icons
const severityColorMap: Record<string, 'error' | 'warning' | 'info' | 'success'> = {
  Critical: 'error',
  High: 'warning',
  Medium: 'info',
  Low: 'success',
};

//Icon mapping for severity levels
const severityIconMap: Record<string, React.ReactElement> = {
  Critical: <ReportProblemIcon aria-hidden = "true" />,
  High: <WarningAmberIcon aria-hidden = "true" />,
  Medium: <CheckCircleOutlineIcon aria-hidden = "true" />,
  Low: <DoneOutlineIcon aria-hidden = "true" />,
};

//Propping the interface for the CriticalFindingsAlert component
interface CriticalFindingsAlertProps {
  alerts: ComplianceAlert[];
  onAlertAction?: (alertId: string, action: 'acknowledge' | 'resolve') => void;
  userPermissions: UserPermissions;
  accessibilityPrefs: AccessibilityPreferences;
}

/**
 * CriticalFindingsAlert component rendering a list of critical compliance alerts.
 * Alerts are sorted by severity and timestamp, with interactive acknowledgment and resolution.
 */

export const CriticalFindingsAlert: React.FC<CriticalFindingsAlertProps> = memo(
  
  ({ alerts, onAlertAction, userPermissions, accessibilityPrefs }) => {
    
    const theme = useTheme();

    //Sorting the alerts by severity (Critical > High > Medium > Low) and timestamp descending
    const sortedAlerts = React.useMemo(() => {
      
      const severityOrder = { Critical: 4, High: 3, Medium: 2, Low: 1 };
      
      return [...alerts].sort((a, b) => {
        
        const severityDiff = (severityOrder[b.severityLabel] || 0) - (severityOrder[a.severityLabel] || 0);
        
        if (severityDiff !== 0) 
          return severityDiff;

        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      });

    }, [alerts]);

    /**
     * Handler for alert acknowledgment
     * @param alertId string alert identifier
     */

    const handleAcknowledge = useCallback(
      
      (alertId: string) => {
        if (onAlertAction) onAlertAction(alertId, 'acknowledge');
      },

      [onAlertAction]

    );

    /**
     * Handler for alert resolution
     * @param alertId string alert identifier
     */

    const handleResolve = useCallback(
      
      (alertId: string) => {
        if (onAlertAction) onAlertAction(alertId, 'resolve');
      },

      [onAlertAction]
    );

    if (alerts.length === 0) {
      return (
        <Box role = "region" aria-live = "polite" aria-atomic = "true" aria-label = "No critical compliance alerts">
          <Typography variant = "body1" color = "textSecondary" sx = {{ p: 2 }}>
            No critical compliance alerts at this time.
          </Typography>
        </Box>
      );
    }

    return (
      <Box role = "region" aria-live = "assertive" aria-atomic = "true" aria-label = "Critical compliance alerts">
        <Typography variant = "h6" component = "h2" sx = {{ mb: 2 }}>
          Critical Findings
        </Typography>
        <List dense>
          {sortedAlerts.map((alert) => {
            const severity = alert.severityLabel || 'Low';
            const severityColor = severityColorMap[severity] || 'info';
            const severityIcon = severityIconMap[severity] || <InfoIcon aria-hidden = "true" />;

            //Formatting the timestamp for display
            const timestamp = new Date(alert.timestamp).toLocaleString();

            //Determining if the user can acknowledge or resolve based on permissions
            const canAcknowledge = userPermissions.canAcknowledgeAlerts ?? true;
            const canResolve = userPermissions.canResolveAlerts ?? false;

            return (
              <ListItem
                key = {alert.id}
                divider
                tabIndex = {0}
                role = "listitem"
                aria-label = {`Alert: ${alert.title}, severity: ${severity}, detected at ${timestamp}`}
                sx = {{
                  bgcolor: alert.acknowledged ? theme.palette.action.selected : 'inherit',
                }}
              >
                <Tooltip title = {`Severity: ${severity}`} arrow>
                  <Box sx = {{ mr: 2, display: 'flex', alignItems: 'center', color: theme.palette[severityColor].main }}>
                    {severityIcon}
                  </Box>
                </Tooltip>
                <ListItemText
                  primary = {
                    <Typography variant = "subtitle1" component = "span" sx = {{ fontWeight: 'bold' }}>
                      {alert.title}
                    </Typography>
                  }
                  secondary = {
                    <>
                      <Typography variant = "body2" color = "textSecondary" noWrap>
                        {alert.description}
                      </Typography>
                      <Typography variant = "caption" color = "textSecondary">
                        Detected: {timestamp}
                      </Typography>
                    </>
                  }
                />
                <ListItemSecondaryAction>
                  {canAcknowledge && !alert.acknowledged && (
                    <Tooltip title = "Acknowledge alert" arrow>
                      <IconButton
                        edge = "end"
                        aria-label = {`Acknowledge alert ${alert.title}`}
                        onClick = {() => handleAcknowledge(alert.id)}
                        size = "large"
                      >
                        <CheckCircleOutlineIcon color = "primary" />
                      </IconButton>
                    </Tooltip>
                  )}
                  {canResolve && !alert.resolved && (
                    <Tooltip title  = "Resolve alert" arrow>
                      <IconButton
                        edge = "end"
                        aria-label = {`Resolve alert ${alert.title}`}
                        onClick = {() => handleResolve(alert.id)}
                        size = "large"
                      >
                        <DoneOutlineIcon color = "success" />
                      </IconButton>
                    </Tooltip>
                  )}
                  {alert.acknowledged && (
                    <Chip
                      label = "Acknowledged"
                      color = "primary"
                      size = "small"
                      sx = {{ ml: 1 }}
                      aria-label = "Alert acknowledged"
                    />
                  )}
                  {alert.resolved && (
                    <Chip
                      label = "Resolved"
                      color = "success"
                      size = "small"
                      sx = {{ ml: 1 }}
                      aria-label = "Alert resolved"
                    />
                  )}
                </ListItemSecondaryAction>
              </ListItem>
            );
          })}
        </List>
      </Box>
    );
  }
);

CriticalFindingsAlert.displayName = 'CriticalFindingsAlert';
