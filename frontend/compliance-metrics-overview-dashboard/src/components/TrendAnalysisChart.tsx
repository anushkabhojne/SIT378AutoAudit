//components/TrendAnalysisChart.tsx

/**
 * TrendAnalysisChart.tsx
 * 
 * Displaying the historical compliance percentage trends over configurable time ranges.
 * Implementing an interactive line chart with tooltips, legends, and accessibility features.
 * Using Chart.js with react-chartjs-2 wrapper.
 * 
 * @author Senior Lead, AutoAudit
 */

import React, { memo, useMemo, useCallback } from 'react';

import {
  Box,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  useTheme,
} 

from '@mui/material';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  Filler,
} 

from 'chart.js';

import { Line } from 'react-chartjs-2';
import { AccessibilityPreferences } from '../types/dashboard.types';
import { formatMetricDisplay } from '../utils/complianceCalculations';

//Registering Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  Filler
);

//Supported time ranges for trend analysis
const TIME_RANGES = ['7d', '30d', '90d', '365d'] as const;
type TimeRange = typeof TIME_RANGES[number];

//Propping the interface for the TrendAnalysisChart component
interface TrendAnalysisChartProps {
  trendData: Array<{ date: string; compliancePercentage: number }>;
  timeRange: TimeRange;
  onTimeRangeChange: (range: TimeRange) => void;
  accessibilityPrefs: AccessibilityPreferences;
}

/**
 * TrendAnalysisChart component rendering a responsive line chart showing compliance trends.
 * Supporting time range selection and accessibility features.
 */

export const TrendAnalysisChart: React.FC<TrendAnalysisChartProps> = memo(
  
  ({ trendData, timeRange, onTimeRangeChange, accessibilityPrefs }) => {
    const theme = useTheme();

    //Filtering the trend data based on the selected time range
    
    const filteredTrendData = useMemo(() => {
      if (!trendData || trendData.length === 0) return [];

      const now = new Date();
      let cutoffDate: Date;

      switch (timeRange) {
        
        case '7d':
          cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        
        case '30d':
          cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        
        case '90d':
          cutoffDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
          break;
        
        case '365d':
          cutoffDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
          break;
        
        default:
          cutoffDate = new Date(0);
      }

      return trendData.filter((point) => new Date(point.date) >= cutoffDate);
    }, [trendData, timeRange]);

    //Preparing the chart labels and data points
    const labels = useMemo(() => filteredTrendData.map((point) => point.date), [filteredTrendData]);
    const dataPoints = useMemo(() => filteredTrendData.map((point) => point.compliancePercentage), [filteredTrendData]);

    //Chart.js data object
    const data = useMemo(
      () => ({
        labels,
        datasets: [
          {
            label: 'Compliance %',
            data: dataPoints,
            fill: true,

            //20% opacity
            backgroundColor: theme.palette.primary.light + '33', 

            borderColor: theme.palette.primary.main,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: theme.palette.primary.main,
            pointHoverBackgroundColor: theme.palette.primary.dark,
          },
        ],
      }),

      [labels, dataPoints, theme.palette.primary]
    );

    //Chart.js options object
    const options = useMemo(
      () => ({
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 800,
          easing: 'easeOutQuart',
        },

        plugins: {
          legend: {
            display: true,
            position: 'top' as const,
            
            labels: {
              color: theme.palette.text.primary,
              
              font: {
                size: 14,
                weight: 'bold',
              },
            },
          },

          tooltip: {
            enabled: true,
            mode: 'nearest' as const,
            intersect: false,
            
            callbacks: {
              label: (context: any) => {
                const value = context.parsed.y;
                return `Compliance: ${formatMetricDisplay(value, 'percentage')}`;
              },
            },

            backgroundColor: theme.palette.background.paper,
            titleColor: theme.palette.text.primary,
            bodyColor: theme.palette.text.primary,
            borderColor: theme.palette.divider,
            borderWidth: 1,
          },

          title: {
            display: true,
            text: 'Compliance Trend Over Time',
            color: theme.palette.text.primary,
            
            font: {
              size: 18,
              weight: 'bold',
            },
          },
        },
        
        scales: {
          
          x: {
            type: 'category' as const,
            ticks: {
              color: theme.palette.text.primary,
              maxRotation: 45,
              minRotation: 45,
              autoSkip: true,
              maxTicksLimit: 10,
            },

            grid: {
              display: false,
            },
          },
          
          y: {
            min: 0,
            max: 100,
            
            ticks: {
              color: theme.palette.text.primary,
              callback: (value: number) => `${value}%`,
            },
            
            grid: {
              color: theme.palette.divider,
            },
            
            title: {
              display: true,
              text: 'Compliance Percentage',
              color: theme.palette.text.primary,
              
              font: {
                size: 14,
                weight: 'normal',
              },
            },
          },
        },
        
        interaction: {
          mode: 'nearest' as const,
          intersect: false,
        },
        
        elements: {
          line: {
            borderWidth: 3,
          },
        },
        
        //Accessibility: ARIA live region for chart updates
        aria: {
          enabled: true,
          label: 'Compliance trend line chart',
          role: 'img',
        },
      }),
      
      [theme.palette]
    );

    //Handler for time range toggle button change
    const handleTimeRangeChange = useCallback(
      
      (_event: React.MouseEvent<HTMLElement>, newRange: TimeRange | null) => {
        
        if (newRange !== null && newRange !== timeRange) {
          onTimeRangeChange(newRange);
        }
      },

      [onTimeRangeChange, timeRange]
    );

    return (
      <Box
        sx = {{
          height: 320,
          width: '100%',
          position: 'relative',
          userSelect: 'none',
        }}
        aria-label = "Compliance trend analysis chart"
        role = "region"
      >
        {/* Time range selector */}
        <Box
          sx = {{
            display: 'flex',
            justifyContent: 'flex-end',
            mb: 1,
          }}
        >
          <ToggleButtonGroup
            value={timeRange}
            exclusive
            onChange = {handleTimeRangeChange}
            aria-label = "Select time range for compliance trend"
            size = "small"
          >
            {TIME_RANGES.map((range) => (
              <ToggleButton key = {range} value = {range} aria-label = {`Show data for last ${range}`}>
                {range.toUpperCase()}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>

        {/* Line chart */}
        <Line data = {data} options = {options} aria-live = "polite" aria-atomic = "true" />
      </Box>
    );
  }
);

TrendAnalysisChart.displayName = 'TrendAnalysisChart';
