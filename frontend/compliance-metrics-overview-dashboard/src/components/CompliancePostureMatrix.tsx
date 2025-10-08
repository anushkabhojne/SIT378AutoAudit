//components/CompliancePostureMatrix.tsx

/**
 * CompliancePostureMatrix.tsx
 * 
 * Displaying a detailed heatmap matrix of CIS control categories against compliance status.
 * Supporting interactive drill-down, filtering, and accessibility features.
 * 
 * @author Senior Lead, AutoAudit
 */

import React, { memo, useCallback, useMemo } from 'react';

import {
  Box,
  Typography,
  Tooltip,
  useTheme,
  useMediaQuery,
  Grid,
  Paper,
} 

from '@mui/material';

import { styled } from '@mui/material/styles';
import { ComplianceControl, AccessibilityPreferences, UserPermissions } 

from '../types/dashboard.types';

import { formatMetricDisplay } 

from '../utils/complianceCalculations';

import InfoOutlinedIcon 

from '@mui/icons-material/InfoOutlined';

//Compliance status color mapping for heatmap cells
const statusColorMap: Record<string, string> = {
  Compliant: '#4caf50', //Green
  'Non-Compliant': '#f44336', //Red
  'Not Applicable': '#9e9e9e', //Grey
  'Under Review': '#ff9800', //Orange
};

//Styled cell for heatmap with dynamic background color and hover effect
const MatrixCell = styled(Paper, {
  shouldForwardProp: (prop) => prop !== 'statusColor',
})<{ statusColor: string }>(({ theme, statusColor }) => ({
  
  backgroundColor: statusColor,
  color: theme.palette.getContrastText(statusColor),
  height: 48,
  width: 48,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  cursor: 'pointer',
  userSelect: 'none',
  borderRadius: theme.shape.borderRadius,
  boxShadow: theme.shadows[1],
  
  transition: theme.transitions.create(['background-color', 'box-shadow'], {
    duration: theme.transitions.duration.short,
  }),

  '&:hover, &:focus-visible': {
    
    boxShadow: theme.shadows[6],
    outline: 'none',
    backgroundColor: theme.palette.action.hover,

  },
}));

//Propping the interface for the CompliancePostureMatrix component
interface CompliancePostureMatrixProps {
  controls: ComplianceControl[];
  onControlClick?: (controlId: string, value: number) => void;
  userPermissions: UserPermissions;
  accessibilityPrefs: AccessibilityPreferences;
}

/**
 * CompliancePostureMatrix component rendering a heatmap matrix of the CIS controls.
 * Rows represent control categories, columns represent compliance statuses.
 * Supporting keyboard navigation, tooltips, and drill-down interaction.
 */

export const CompliancePostureMatrix: React.FC<CompliancePostureMatrixProps> = memo(
  
  ({ controls, onControlClick, userPermissions, accessibilityPrefs }) => {
    
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

    //Extracting the unique categories from controls, sorted alphabetically
    const categories = useMemo(() => {
      const uniqueCategories = Array.from(new Set(controls.map((c) => c.category)));
      uniqueCategories.sort();
      return uniqueCategories;
    }, [controls]);

    //Compliance statuses to display as columns
    const complianceStatuses = ['Compliant', 'Non-Compliant', 'Not Applicable', 'Under Review'];

    //Grouping the controls by category and status for matrix cell counts
    const matrixData = useMemo(() => {
      
      const data: Record<string, Record<string, ComplianceControl[]>> = {};
      
      categories.forEach((category) => {
        data[category] = {};
        
        complianceStatuses.forEach((status) => {
          data[category][status] = [];
        });

      });

      controls.forEach((control) => {
        
        const status = control.status || 'Not Applicable';
        
        if (data[control.category] && data[control.category][status]) {
          data[control.category][status].push(control);
        }

      });

      return data;
    
    }, [controls, categories, complianceStatuses]);

    /**
     * Handling the cell click to drill down into detailed control assessments.
     * Passing the first control's id and risk score as value.
     */

    const handleCellClick = useCallback(
      
      (category: string, status: string) => {
        
        const controlsInCell = matrixData[category][status];
        
        if (controlsInCell.length > 0 && onControlClick) {
          
          //Passing the first control id and risk score as example
          onControlClick(controlsInCell[0].id, controlsInCell[0].riskScore || 0);

        }
      },

      [matrixData, onControlClick]
    );

    /**
     * Rendering a single matrix cell with tooltip and accessibility features.
     */

    const renderCell = (category: string, status: string) => {
      const controlsInCell = matrixData[category][status];
      const count = controlsInCell.length;
      const statusColor = statusColorMap[status] || theme.palette.grey[500];

      //Tooltip content with control descriptions and remediation recommendations
      const tooltipContent = (
        <Box maxWidth = {300}>
          <Typography variant = "subtitle2" gutterBottom>
            {category} - {status} ({count} control{count !== 1 ? 's' : ''})
          </Typography>
          {count === 0 ? (
            <Typography variant = "body2" color = "textSecondary">
              No controls in this category with this status.
            </Typography>
          ) : (
            controlsInCell.slice(0, 5).map((control) => (
              <Box key = {control.id} mb = {1}>
                <Typography variant = "body2" fontWeight = "bold">
                  {control.id}: {control.name}
                </Typography>
                <Typography variant = "caption" color = "textSecondary" noWrap>
                  {control.description}
                </Typography>
                {control.remediation && (
                  <Typography variant = "caption" color = "textPrimary" sx = {{ fontStyle: 'italic' }}>
                    Remediation: {control.remediation}
                  </Typography>
                )}
              </Box>
            ))
          )}
          {count > 5 && (
            <Typography variant = "caption" color = "textSecondary">
              And {count - 5} more...
            </Typography>
          )}
        </Box>
      );

      return (
        <Tooltip
          key={`${category}-${status}`}
          title={tooltipContent}
          enterDelay = {300}
          leaveDelay = {100}
          arrow
          placement = "top"
          disableInteractive = {false}
        >
          <MatrixCell
            statusColor = {statusColor}
            tabIndex = {0}
            role = "button"
            aria-label = {`${count} controls in category ${category} with status ${status}`}
            onClick={() => handleCellClick(category, status)}
            
            onKeyDown={(e) => {
              
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleCellClick(category, status);
              }
            }}
          >
            <Typography variant = "body1" aria-live = "polite" aria-atomic = "true">
              {count}
            </Typography>
          </MatrixCell>
        </Tooltip>
      );
    };

    return (
      <Box
        role = "table"
        aria-label = "Compliance Posture Matrix"
        sx = {{
          overflowX: 'auto',
          width: '100%',
          borderCollapse: 'collapse',
          borderSpacing: 0,
        }}
      >
        {/* Table header */}
        <Grid container sx={{ fontWeight: 'bold', mb: 1 }}>
          <Grid item xs = {3} />
          {complianceStatuses.map((status) => (
            <Grid
              item
              key = {`header-${status}`}
              xs
              sx = {{
                textAlign: 'center',
                color: theme.palette.text.primary,
                userSelect: 'none',
              }}
              role = "columnheader"
              tabIndex={-1}
            >
              {status}
            </Grid>
          ))}
        </Grid>

        {/* Table rows */}
        {categories.map((category) => (
          <Grid
            container
            key={`row-${category}`}
            role="row"
            sx={{ mb: 1, alignItems: 'center' }}
          >
            {/* Category label */}
            <Grid
              item
              xs = {3}
              role = "rowheader"
              tabIndex = {-1}
              sx = {{
                fontWeight: 'bold',
                color: theme.palette.text.primary,
                userSelect: 'none',
                pr: 1,
              }}
            >
              <Box display = "flex" alignItems = "center">
                <InfoOutlinedIcon
                  fontSize = "small"
                  color = "action"
                  aria-hidden = "true"
                  sx = {{ mr: 0.5 }}
                />
                <Typography variant = "body1">{category}</Typography>
              </Box>
            </Grid>

            {/* Status cells */}
            {complianceStatuses.map((status) => (
              <Grid
                item
                xs
                key = {`${category}-${status}`}
                role = "gridcell"
                tabIndex = {-1}
                sx = {{ display: 'flex', justifyContent: 'center' }}
              >
                {renderCell(category, status)}
              </Grid>
            ))}
          </Grid>
        ))}
      </Box>
    );
  }
);

CompliancePostureMatrix.displayName = 'CompliancePostureMatrix';
