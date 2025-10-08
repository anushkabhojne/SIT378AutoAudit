/**
 * ComplianceMetricsDashboard.tsx
 * 
 * Primary dashboard component implementing comprehensive compliance metrics visualisation
 * for Microsoft 365 environments assessed against CIS Foundations Benchmark v2.0.0.
 * 
 * This component orchestrates four primary visualisation zones:
 * 1. Executive Summary Panel - High-level compliance metrics
 * 2. Compliance Posture Matrix - Detailed control status visualisation  
 * 3. Trend Analysis Visualisation - Historical compliance trends
 * 4. Critical Findings Alert System - Real-time security alerts
 * 
 * @author Senior Lead, AutoAudit
 */

import React, { 
  useState, 
  useEffect, 
  useCallback, 
  useMemo, 
  useReducer,
  useRef,
  ErrorInfo,
  ReactNode 
} 

from 'react';

import { 
  Grid, 
  Box, 
  Container, 
  Paper, 
  Typography, 
  Alert, 
  Skeleton,
  useTheme,
  useMediaQuery,
  Fade,
  Slide,
  Button
} 

from '@mui/material';

import { styled } from '@mui/material/styles';
import { ErrorBoundary } from 'react-error-boundary';

//Internal component imports implementing the modular dashboard architecture
import { ExecutiveSummaryCards } from './components/ExecutiveSummaryCards';
import { CompliancePostureMatrix } from './components/CompliancePostureMatrix';
import { TrendAnalysisChart } from './components/TrendAnalysisChart';
import { CriticalFindingsAlert } from './components/CriticalFindingsAlert';

//Custom hooks for business logic encapsulation and reusability
import { useComplianceData } from '../hooks/useComplianceData';
import { useWebSocketConnection } from '../hooks/useWebSocketConnection';
import { usePerformanceMetrics } from '../hooks/usePerformanceMetrics';
import { useAccessibilityPreferences } from '../hooks/useAccessibilityPreferences';

//Context providers for global state management
import { ComplianceDataProvider } from '../context/ComplianceDataContext';
import { UserPreferencesProvider } from '../context/UserPreferencesContext';
import { AlertProvider } from '../context/AlertContext';

//Type definitions ensuring type safety across component boundaries
import { 
  ComplianceMetrics, 
  DashboardConfiguration, 
  UserPermissions,
  ComplianceAlert,
  PerformanceMetrics,
  AccessibilityPreferences 
} 

from '../types/dashboard.types';

//Utility functions for data processing and validation
import { 
  validateComplianceData, 
  calculateCompliancePercentage,
  aggregateRiskScores,
  formatMetricDisplay 
} 

from '../utils/complianceCalculations';

//Error reporting and logging utilities
import { logError, reportPerformanceMetric } from '../utils/monitoring';

/**
 * Styled components implementing Material Design principles with custom
 * compliance dashboard styling requirements and responsive behaviour
 */

const DashboardContainer = styled(Container)(({ theme }) => ({
  
  //Responsive padding ensuring optimal spacing across device categories
  paddingTop: theme.spacing(3),
  paddingBottom: theme.spacing(3),
  
  //Mobile-first responsive design with progressive enhancement
  [theme.breakpoints.down('sm')]: {
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
  },
  
  //Tablet optimisation with increased spacing for improved touch interaction
  [theme.breakpoints.between('sm', 'md')]: {
    paddingLeft: theme.spacing(2),
    paddingRight: theme.spacing(2),
  },
  
  //Desktop optimisation with maximum content width and centered alignment
  [theme.breakpoints.up('lg')]: {
    maxWidth: '1400px',
    margin: '0 auto',
  },
}));

const DashboardHeader = styled(Box)(({ theme }) => ({
  
  //Header styling with gradient background supporting brand consistency
  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
  color: theme.palette.primary.contrastText,
  padding: theme.spacing(3),
  borderRadius: theme.shape.borderRadius,
  marginBottom: theme.spacing(3),
  
  //Box shadow implementation for visual depth and hierarchy
  boxShadow: theme.shadows[4],
  
  //Animation support for dynamic content updates
  transition: theme.transitions.create(['background', 'box-shadow'], {
    duration: theme.transitions.duration.standard,
  }),
}));

const MetricsGrid = styled(Grid)(({ theme }) => ({
  
  //Grid spacing optimisation for visual hierarchy and component separation
  spacing: theme.spacing(3),
  
  //Responsive grid behaviour ensuring optimal component distribution
  [theme.breakpoints.down('md')]: {
    '& .MuiGrid-item': {
      paddingLeft: theme.spacing(1),
      paddingRight: theme.spacing(1),
    },
  },
}));

/**
 * Dashboard state management using useReducer for complex state transitions
 * involving multiple data dependencies and coordinated updates
 */

interface DashboardState {
  //Current compliance assessment data with validation status
  complianceData: ComplianceMetrics | null;
  
  //Loading the states for the different dashboard sections, enabling selective loading indicators
  loading: {
    summary: boolean;
    matrix: boolean;
    trends: boolean;
    alerts: boolean;
  };
  
  //Error states with specific error information for targeted error handling
  errors: {
    summary: Error | null;
    matrix: Error | null;
    trends: Error | null;
    alerts: Error | null;
    websocket: Error | null;
  };
  
  //Real-time connection status affecting dashboard functionality
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting' | 'error';
  
  //User interaction state for dashboard customisation and filtering
  filters: {
    timeRange: '7d' | '30d' | '90d' | '365d';
    severityFilter: 'all' | 'critical' | 'high' | 'medium' | 'low';
    controlCategories: string[];
  };
  
  //Performance metrics for monitoring and optimisation
  performanceMetrics: PerformanceMetrics;
  
  //Last update timestamp for data freshness indication
  lastUpdated: Date | null;
}

/**
 * Action types for dashboard state management with comprehensive
 * state update scenarios and error handling capabilities
 */

type DashboardAction =
  | { type: 'LOAD_COMPLIANCE_DATA_START'; section: keyof DashboardState['loading'] }
  | { type: 'LOAD_COMPLIANCE_DATA_SUCCESS'; payload: ComplianceMetrics; section: keyof DashboardState['loading'] }
  | { type: 'LOAD_COMPLIANCE_DATA_ERROR'; payload: Error; section: keyof DashboardState['errors'] }
  | { type: 'UPDATE_REAL_TIME_METRICS'; payload: Partial<ComplianceMetrics> }
  | { type: 'UPDATE_CONNECTION_STATUS'; payload: DashboardState['connectionStatus'] }
  | { type: 'APPLY_FILTERS'; payload: Partial<DashboardState['filters']> }
  | { type: 'UPDATE_PERFORMANCE_METRICS'; payload: PerformanceMetrics }
  | { type: 'RESET_DASHBOARD_STATE' };

/**
 * Dashboard state reducer implementing immutable state updates with
 * comprehensive error handling and performance optimisation
 */

const dashboardReducer = (state: DashboardState, action: DashboardAction): DashboardState => {
  switch (action.type) {
    case 'LOAD_COMPLIANCE_DATA_START':
      
    //Setting the loading state for specific dashboard section, enabling targeted loading indicators
      return {
        ...state,
        
        loading: {
          ...state.loading,
          [action.section]: true,
        },
        
        errors: {
          ...state.errors,
          [action.section]: null,
        },
      };

    case 'LOAD_COMPLIANCE_DATA_SUCCESS':
      //Updating the compliance data with validation and set loading complete
      
      const validatedData = validateComplianceData(action.payload);
      
      return {
        ...state,
        complianceData: validatedData,
        
        loading: {
          ...state.loading,
          [action.section]: false,
        },
        
        errors: {
          ...state.errors,
          [action.section]: null,
        },
        
        lastUpdated: new Date(),
      };

    case 'LOAD_COMPLIANCE_DATA_ERROR':
      //Handling the error states with specific error information and loading state reset

      return {
        ...state,

        loading: {
          ...state.loading,
          [action.section]: false,
        },

        errors: {
          ...state.errors,
          [action.section]: action.payload,
        },
      };

    case 'UPDATE_REAL_TIME_METRICS':
      //Merging the real-time metric updates with the existing compliance data

      if (!state.complianceData) return state;
      
      return {
        ...state,
        
        complianceData: {
          ...state.complianceData,
          ...action.payload,
        },
        
        lastUpdated: new Date(),
      };

    case 'UPDATE_CONNECTION_STATUS':
      //Updating the WebSocket connection status affecting real-time capabilities
      
      return {
        ...state,
        connectionStatus: action.payload,
        
        errors: {
          ...state.errors,
          websocket: action.payload === 'error' ? new Error('WebSocket connection failed') : null,
        },
      };

    case 'APPLY_FILTERS':
      //Updating the dashboard filters triggering data re-aggregation and visualisation updates
      
      return {
        ...state,
        
        filters: {
          ...state.filters,
          ...action.payload,
        },
      };

    case 'UPDATE_PERFORMANCE_METRICS':
      //Updating the performance metrics for monitoring and optimisation
      
      return {
        ...state,
        performanceMetrics: action.payload,
      };

    case 'RESET_DASHBOARD_STATE':
      //Resetting the dashboard to its initial state for user session cleanup or error recovery
      
      return initialDashboardState;

    default:
      //Handling the unexpected action types with warning logging
      
      console.warn(`Unknown dashboard action type: ${(action as any).type}`);
      return state;
  }
};

/**
 * Initial dashboard state with default values and proper type initialisation
 */

const initialDashboardState: DashboardState = {
  complianceData: null,
  
  loading: {
    summary: false,
    matrix: false,
    trends: false,
    alerts: false,
  },
  
  errors: {
    summary: null,
    matrix: null,
    trends: null,
    alerts: null,
    websocket: null,
  },
  
  connectionStatus: 'disconnected',
  
  filters: {
    timeRange: '30d',
    severityFilter: 'all',
    controlCategories: [],
  },
  
  performanceMetrics: {
    loadTime: 0,
    renderTime: 0,
    memoryUsage: 0,
    apiResponseTime: 0,
  },
  lastUpdated: null,
};

/**
 * Dashboard component props interface with comprehensive configuration options
 */

interface ComplianceMetricsDashboardProps {
  //User permissions affecting dashboard feature availability and data access
  userPermissions: UserPermissions;
  
  //Dashboard configuration including theme, layout, and feature toggles
  configuration?: DashboardConfiguration;
  
  //Initial compliance data for immediate rendering before real-time updates
  initialData?: ComplianceMetrics;
  
  //Callback functions for user interaction handling and external system integration
  onMetricClick?: (metricId: string, value: number) => void;
  onAlertAction?: (alertId: string, action: 'acknowledge' | 'resolve') => void;
  onExportRequest?: (exportType: 'pdf' | 'csv' | 'excel') => void;
  
  //Error handling callback for external error reporting and user notification
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

/**
 * Error boundary component for graceful error handling and user feedback
 */

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class DashboardErrorBoundary extends React.Component<
  { children: ReactNode; onError?: (error: Error, errorInfo: ErrorInfo) => void },
  ErrorBoundaryState
> {
  constructor(props: { children: ReactNode; onError?: (error: Error, errorInfo: ErrorInfo) => void }) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  /**
   * Static method for error boundary state updates during error conditions
   */

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  /**
   * Component error handling with logging and external error reporting
   */

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    //Logging the error details for debugging and monitoring
    logError('Dashboard Error Boundary', error, { errorInfo });
    
    //Updating the component state with the error information
    this.setState({ errorInfo });
    
    //Executing the external error handling callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  render() {
    //Displaying the error fallback UI when the error boundary is triggered
    if (this.state.hasError) {
      
      return (
        <Paper elevation = {3} sx = {{ p: 3, m: 2 }}>
          <Alert severity = "error">
            <Typography variant = "h6" gutterBottom>
              Dashboard Error
            </Typography>
            <Typography variant = "body2">
              An unexpected error occurred while loading the compliance dashboard. 
              Please refresh the page or contact system administrator if the issue persists.
            </Typography>
            {/* Development environment error details for debugging */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Box sx = {{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                <Typography variant = "caption" component = "pre">
                  {this.state.error.toString()}
                </Typography>
              </Box>
            )}
          </Alert>
        </Paper>
      );
    }

    return this.props.children;
  }
}

/**
 * Main Compliance Metrics Dashboard Component
 * 
 * Implementing enterprise-grade compliance visualisation with real-time updates,
 * responsive design, accessibility compliance, and comprehensive error handling
 */

const ComplianceMetricsDashboard: React.FC<ComplianceMetricsDashboardProps> = ({
  userPermissions,
  configuration = {},
  initialData,
  onMetricClick,
  onAlertAction,
  onExportRequest,
  onError,
}) => {
  
  //Theme and responsive design hooks for adaptive UI behaviour
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  
  //Performance measurement refs for monitoring dashboard performance
  const mountTimeRef = useRef<number>(Date.now());
  const renderCountRef = useRef<number>(0);
  
  //Dashboard state management using reducer for complex state coordination
  const [dashboardState, dispatchDashboard] = useReducer(dashboardReducer, initialDashboardState);

  /**
   * WebSocket message handler implementing real-time dashboard updates
   * with message validation and appropriate component state updates
   */

  const handleWebSocketMessage = useCallback((message: any): void => {
    try {
      
      //Validating the incoming WebSocket message structure and type
      if (!message || typeof message !== 'object') {
        throw new Error('Invalid WebSocket message format');
      }

      //Routing the messages based on their type to appropriate state update handlers
      switch (message.type) {
        
        case 'compliance-data-update':
          
        //Handling real-time compliance metric updates with validation
          if (message.data && validateComplianceData(message.data)) {
            
            dispatchDashboard({
              type: 'UPDATE_REAL_TIME_METRICS',
              payload: message.data,
            });
          }

          break;

        case 'critical-alert-new':
          //Handling the new critical compliance alerts with immediate notification
          
          if (message.alert) {
            //Triggering an immediate alert display and user notification
            handleNewCriticalAlert(message.alert);
          }
          break;

        case 'assessment-status-change':
          //Handling the assessment status updates affecting dashboard loading states
          updateAssessmentStatus(message.status);
          break;

        case 'user-session-update':
          //Handling the user session changes affecting permissions and data access
          
          if (message.permissions) {
            validateUserPermissions(message.permissions);
          }

          break;

        default:
          //Logging the unknown message types for debugging and monitoring
          console.warn('Unknown WebSocket message type:', message.type);
          break;
      }
    } 
    
    catch (error) {
      console.error('Error processing WebSocket message:', error);
      logError('WebSocket Message Handler', error as Error, { message });
    }
  }, []);
  
  //Custom hooks for business logic encapsulation and external service integration
  const { 
    complianceData, 
    loadComplianceData, 
    refreshData, 
    isLoading: dataLoading,
    error: dataError 
  } = useComplianceData({
    userPermissions,
    initialData,
    
    onError: (error) => dispatchDashboard({ 
      type: 'LOAD_COMPLIANCE_DATA_ERROR', 
      payload: error, 
      section: 'summary' 
    }),
  });
  
  //WebSocket connection for real-time compliance updates and alerts
  const { 
    connectionStatus, 
    subscribe, 
    unsubscribe,
    sendMessage 
  } = useWebSocketConnection({
    url: process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws',
    onMessage: handleWebSocketMessage,
    
    onError: (error) => dispatchDashboard({ 
      type: 'UPDATE_CONNECTION_STATUS', 
      payload: 'error' 
    }),
  });
  
  //Performance monitoring for dashboard optimisation and user experience measurement
  const { recordMetric, getMetrics } = usePerformanceMetrics();
  
  //Accessibility preferences for inclusive design implementation
  const { preferences: accessibilityPrefs } = useAccessibilityPreferences();

  /**
   * Handling new critical alerts with immediate user notification
   */

  const handleNewCriticalAlert = useCallback((alert: ComplianceAlert): void => {
    try {
      //Logging critical alert for monitoring and auditing
      logError('Critical Compliance Alert', new Error(`Critical alert: ${alert.title}`), { alert });
      
      //Updating the dashboard state with a new alert
      if (dashboardState.complianceData) {
        const updatedAlerts = [...(dashboardState.complianceData.alerts || []), alert];
        
        dispatchDashboard({
          type: 'UPDATE_REAL_TIME_METRICS',
          payload: { alerts: updatedAlerts },
        });
      }
    } 
    
    catch (error) {
      console.error('Error handling critical alert:', error);
    }

  }, [dashboardState.complianceData]);

  /**
   * Updating the assessment status based on real-time updates
   */
  
  const updateAssessmentStatus = useCallback((status: string): void => {
    //Handling the assessment status changes that might affect loading states
    if (status === 'running') {
      dispatchDashboard({ type: 'LOAD_COMPLIANCE_DATA_START', section: 'summary' });
    } 
    
    else if (status === 'completed') {
      //Triggering the data refresh when the assessment completes
      refreshData();
    }
  }, [refreshData]);

  /**
   * Validating the user permissions for security and access control
   */

  const validateUserPermissions = useCallback((permissions: UserPermissions): void => {
    //Implementing the permission validation logic
    
    if (!permissions || !permissions.canViewDashboard) {
      const error = new Error('Insufficient permissions to view dashboard');
      
      dispatchDashboard({ 
        type: 'LOAD_COMPLIANCE_DATA_ERROR', 
        payload: error, 
        section: 'summary' 
      });
    }
  }, []);

  /**
   * Handling the filter changes with data re-aggregation
   */

  const handleFilterChange = useCallback((newFilters: Partial<DashboardState['filters']>): void => {
    
    dispatchDashboard({
      type: 'APPLY_FILTERS',
      payload: newFilters,
    });
  }, []);

  /**
   * Handling the alert actions (i.e., acknowledge and resolve)
   */
  
  const handleAlertAction = useCallback((alertId: string, action: 'acknowledge' | 'resolve'): void => {
    
    try {
      //Executing the external alert action handler, if provided

      if (onAlertAction) {
        onAlertAction(alertId, action);
      }
      
      //Updating the local state to reflect alert action
      if (dashboardState.complianceData?.alerts) {
        
        const updatedAlerts = dashboardState.complianceData.alerts.map(alert =>
          
          alert.id === alertId 
            ? { ...alert, status: action === 'resolve' ? 'resolved' : 'acknowledged' }
            : alert
        );
        
        dispatchDashboard({
          type: 'UPDATE_REAL_TIME_METRICS',
          payload: { alerts: updatedAlerts },
        });
      }
    } 
    
    catch (error) {
      console.error('Error handling alert action:', error);
      logError('Alert Action Handler', error as Error, { alertId, action });
    }
  }, [onAlertAction, dashboardState.complianceData]);

  /**
   * Error message rendering component with retry functionality
   */

  const renderErrorMessage = useCallback((error: Error, retryFunction?: () => void) => (
    <Paper elevation = {2} sx = {{ p: 3 }}>
      <Alert 
        severity = "error" 
        action = {
          retryFunction && (
            <Button color = "inherit" size = "small" onClick = {retryFunction}>
              Retry
            </Button>
          )
        }
      >
        <Typography variant = "subtitle1" gutterBottom>
          Failed to Load Data
        </Typography>
        <Typography variant = "body2">
          {error.message || 'An unexpected error occurred while loading dashboard data.'}
        </Typography>
      </Alert>
    </Paper>
  ), []);

  /**
   * Filtered compliance data based on current dashboard filters
   */

  const filteredComplianceData = useMemo(() => {
    if (!dashboardState.complianceData) return null;

    //Applying the time range filter
    let filtered = { ...dashboardState.complianceData };
    
    //Applying the severity filter to alerts
    if (dashboardState.filters.severityFilter !== 'all') {
      
      filtered.alerts = filtered.alerts?.filter(
        alert => alert.severity === dashboardState.filters.severityFilter
      );
    }

    //Applying the control category filter
    if (dashboardState.filters.controlCategories.length > 0) {
      //Filtering the compliance data based on selected control categories
      //Implementation would depend on the specific data structure
    }

    return filtered;

  }, [dashboardState.complianceData, dashboardState.filters]);

  /**
   * Component lifecycle and data loading effects
   */

  useEffect(() => {
    //Recording the component mount time for performance monitoring

    const mountTime = Date.now() - mountTimeRef.current;
    recordMetric('dashboard-mount-time', mountTime);

    //Initialising the dashboard data loading

    if (!dashboardState.complianceData && !dataLoading) {
      dispatchDashboard({ type: 'LOAD_COMPLIANCE_DATA_START', section: 'summary' });
      loadComplianceData();
    }

    //Cleaning up the function for the component unmount
    return () => {
      
      //Unsubscribing from the WebSocket channels
      unsubscribe('compliance-updates');
      unsubscribe('critical-alerts');
      
      //Reporting the final performance metrics
      const metrics = getMetrics();
      reportPerformanceMetric('dashboard-session', metrics);

    };
  }, []);

  /**
   * WebSocket subscription management for real-time updates
   */

  useEffect(() => {
    if (connectionStatus === 'connected') {
      
      //Subscribing to the relevant WebSocket channels for real-time updates
      subscribe('compliance-updates');
      subscribe('critical-alerts');
      subscribe('assessment-status');
    }

  }, [connectionStatus, subscribe]);

  /**
   * Updating the dashboard state when external compliance data changes
   */

  useEffect(() => {
    
    if (complianceData) {
      
      dispatchDashboard({
        type: 'LOAD_COMPLIANCE_DATA_SUCCESS',
        payload: complianceData,
        section: 'summary',
      });
    }

  }, [complianceData]);

  /**
   * Handling the data errors from external hooks
   */

  useEffect(() => {
    
    if (dataError) {
      
      dispatchDashboard({
        type: 'LOAD_COMPLIANCE_DATA_ERROR',
        payload: dataError,
        section: 'summary',
      });
    }

  }, [dataError]);

  /**
   * Updating the connection status from WebSocket hook
   */

  useEffect(() => {
    
    dispatchDashboard({
      type: 'UPDATE_CONNECTION_STATUS',
      payload: connectionStatus,
    });

  }, [connectionStatus]);

  /**
   * Tracking the render performance for optimisation
   */

  useEffect(() => {
    renderCountRef.current += 1;
    const renderTime = performance.now();
    recordMetric('dashboard-render-time', renderTime);
  });

  //Early return for critical errors or missing permissions
  if (!userPermissions?.canViewDashboard) {
    return (
      <Paper elevation = {3} sx = {{ p: 3, m: 2 }}>
        <Alert severity = "warning">
          <Typography variant = "h6" gutterBottom>
            Access Denied
          </Typography>
          <Typography variant = "body2">
            You do not have sufficient permissions to view the compliance dashboard.
            Please contact your administrator for access.
          </Typography>
        </Alert>
      </Paper>
    );
  }

  return (
    <DashboardErrorBoundary onError = {onError}>
      <ComplianceDataProvider>
        <UserPreferencesProvider>
          <AlertProvider>
            <DashboardContainer maxWidth = {false}>
              {/* Dashboard Header with Title and Status Indicators */}
              <Slide direction = "down" in = {true} mountOnEnter unmountOnExit>
                <DashboardHeader>
                  <Typography variant = "h4" component = "h1" gutterBottom>
                    Microsoft 365 Compliance Dashboard
                  </Typography>
                  <Typography variant = "subtitle1" sx = {{ opacity: 0.9 }}>
                    CIS Foundations Benchmark v2.0.0 Assessment Results
                  </Typography>
                  <Box sx = {{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant = "body2" sx = {{ opacity: 0.8 }}>
                      Connection Status: {connectionStatus}
                    </Typography>
                    {dashboardState.lastUpdated && (
                      <Typography variant = "body2" sx = {{ opacity: 0.8 }}>
                        Last Updated: {dashboardState.lastUpdated.toLocaleString()}
                      </Typography>
                    )}
                  </Box>
                </DashboardHeader>
              </Slide>

              {/* Executive Summary Cards */}
              <Fade in = {true} timeout = {600}>
                <Box mb = {4} aria-label = "Executive Summary">
                  {dashboardState.loading.summary ? (
                    <Grid container spacing = {3}>
                      {[1, 2, 3, 4].map((i) => (
                        <Grid item xs = {12} sm = {6} md = {3} key = {i}>
                          <Skeleton variant = "rectangular" height = {120} />
                        </Grid>
                      ))}
                    </Grid>
                  ) : dashboardState.errors.summary ? (
                    renderErrorMessage(dashboardState.errors.summary, () => refreshData())
                  ) : (
                    <ExecutiveSummaryCards
                      complianceData = {filteredComplianceData}
                      onMetricClick = {onMetricClick}
                      userPermissions = {userPermissions}
                      configuration = {configuration}
                    />
                  )}
                </Box>
              </Fade>

              {/* Compliance Posture Matrix */}
              <Fade in = {true} timeout = {800}>
                <Box mb = {4} aria-label = "Compliance Posture Matrix">
                  {dashboardState.loading.matrix ? (
                    <Skeleton variant = "rectangular" height = {400} />
                  ) : dashboardState.errors.matrix ? (
                    renderErrorMessage(dashboardState.errors.matrix, () => refreshData())
                  ) : (
                    <CompliancePostureMatrix
                      complianceData = {filteredComplianceData}
                      filters = {dashboardState.filters}
                      onFilterChange = {handleFilterChange}
                      userPermissions = {userPermissions}
                      accessibilityPrefs = {accessibilityPrefs}
                    />
                  )}
                </Box>
              </Fade>

              {/* Trend Analysis Visualisation */}
              <Fade in = {true} timeout = {1000}>
                <Box mb = {4} aria-label = "Compliance Trends">
                  {dashboardState.loading.trends ? (
                    <Skeleton variant = "rectangular" height = {300} />
                  ) : dashboardState.errors.trends ? (
                    renderErrorMessage(dashboardState.errors.trends, () => refreshData())
                  ) : (
                    <TrendAnalysisChart
                      trendData = {filteredComplianceData?.trendData || []}
                      timeRange = {dashboardState.filters.timeRange}
                      onTimeRangeChange = {(range) => handleFilterChange({ timeRange: range })}
                      accessibilityPrefs = {accessibilityPrefs}
                    />
                  )}
                </Box>
              </Fade>

              {/* Critical Findings Alert System */}
              <Fade in = {true} timeout = {1200}>
                <Box mt = {4} aria-live = "assertive" aria-atomic = "true" aria-relevant = "additions">
                  {dashboardState.loading.alerts ? (
                    <Skeleton variant = "rectangular" height = {150} />
                  ) : dashboardState.errors.alerts ? (
                    renderErrorMessage(dashboardState.errors.alerts, () => refreshData())
                  ) : (
                    <CriticalFindingsAlert
                      alerts = {filteredComplianceData?.alerts || []}
                      onAlertAction = {handleAlertAction}
                      userPermissions = {userPermissions}
                      accessibilityPrefs = {accessibilityPrefs}
                    />
                  )}
                </Box>
              </Fade>
            </DashboardContainer>
          </AlertProvider>
        </UserPreferencesProvider>
      </ComplianceDataProvider>
    </DashboardErrorBoundary>
  );
};

export default ComplianceMetricsDashboard;
