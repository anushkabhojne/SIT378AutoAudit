# Compliance Metrics Overview Dashboard

**Version:** 1.0.0  
**Task:** T2-FE-006  
**Team:** AutoAudit Frontend Team  
**Trimester:** T2 2025

## Quick Start

```bash
# Clone repository
git clone https://github.com/Hardhat-Enterprises/AutoAudit.git
cd AutoAudit/frontend/compliance-metrics-overview-dashboard

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Prerequisites

- **Node.js**: 18.x or higher
- **npm**: 9.x or higher
- **TypeScript**: 5.4.x
- **React**: 18.3.x
- **Material-UI**: 5.14.x

## Installation

### Development Environment Setup

```bash
# Install Node.js and npm (if not already installed)
# Visit https://nodejs.org/ for installation instructions

# Verify installation
node --version  # Should output v18.x.x or higher
npm --version   # Should output 9.x.x or higher

# Clone repository
git clone https://github.com/Hardhat-Enterprises/AutoAudit.git
cd AutoAudit/frontend/compliance-metrics-overview-dashboard

# Install all dependencies
npm install

# Install peer dependencies if not automatically installed
npm install react react-dom typescript @mui/material @emotion/react @emotion/styled

# Install development dependencies
npm install --save-dev @types/react @types/react-dom @types/node eslint prettier jest
```

### Environment Configuration

Create `.env.local` file in project root:

```bash
# API Configuration
REACT_APP_API_URL = http://localhost:8000/api/v1
REACT_APP_WEBSOCKET_URL = ws://localhost:8000/ws

# Authentication
REACT_APP_AUTH_ENABLED = true
REACT_APP_AZURE_AD_CLIENT_ID = your-client-id
REACT_APP_AZURE_AD_TENANT_ID = your-tenant-id

# Feature Flags
REACT_APP_ENABLE_PERFORMANCE_MONITORING = true
REACT_APP_ENABLE_ERROR_REPORTING = true
REACT_APP_ENABLE_ANALYTICS = false

# Performance Settings
REACT_APP_CACHE_TTL_METRICS = 300000
REACT_APP_CACHE_TTL_ALERTS = 60000
REACT_APP_WEBSOCKET_RECONNECT_ATTEMPTS = 5

# Accessibility
REACT_APP_DEFAULT_THEME = light
REACT_APP_ENABLE_HIGH_CONTRAST = true
REACT_APP_ENABLE_REDUCED_MOTION = false
```

## Configuration Management

### Theme Customisation

Edit `src/styles/theme.ts`:

```typescript
import { createTheme } from '@mui/material/styles';

export const theme  =  createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
    },
    success: {
      main: '#4caf50',
    },
    warning: {
      main: '#ff9800',
    },
    error: {
      main: '#f44336',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
    },
  },
  shape: {
    borderRadius: 8,
  },
});
```

### API Endpoint Configuration

Edit `src/utils/apiConfig.ts`:

```typescript
export const API_ENDPOINTS  =  {
  compliance: {
    metrics: '/compliance/metrics',
    assessments: '/compliance/assessments',
    controls: '/compliance/controls',
  },
  alerts: {
    list: '/alerts',
    acknowledge: '/alerts/:id/acknowledge',
    resolve: '/alerts/:id/resolve',
  },
  trends: {
    historical: '/trends/historical',
    predictions: '/trends/predictions',
  },
};
```

## Component Documentation

### ComplianceMetricsDashboard

**Main dashboard component orchestrating all visualisation zones.**

```typescript
import ComplianceMetricsDashboard from './ComplianceMetricsDashboard';

<ComplianceMetricsDashboard
  userPermissions = {{
    roles: ['compliance_viewer', 'security_analyst'],
    permissions: ['view_metrics', 'view_alerts'],
  }}
  configuration = {{
    theme: 'light',
    enableRealTimeUpdates: true,
    refreshInterval: 30000,
  }}
  initialData = {complianceData}
  onMetricClick = {(metricId, value)  = > console.log(metricId, value)}
  onAlertAction = {(alertId, action)  = > handleAlert(alertId, action)}
  onExportRequest = {(type)  = > exportData(type)}
  onError = {(error, errorInfo)  = > logError(error, errorInfo)}
/>
```

**Props:**
- `userPermissions`: User role and permission configuration
- `configuration`: Dashboard display and behaviour settings
- `initialData`: Initial compliance metrics for immediate rendering
- `onMetricClick`: Callback for metric interaction
- `onAlertAction`: Callback for alert management
- `onExportRequest`: Callback for data export
- `onError`: Error handling callback

### ExecutiveSummaryCards

**Displays high-level compliance metrics in card format.**

```typescript
import { ExecutiveSummaryCards } from './components/ExecutiveSummaryCards';

<ExecutiveSummaryCards
  metrics = {dashboardMetrics}
  loading = {false}
  onMetricClick = {handleMetricClick}
  userPermissions = {userPermissions}
  isMobile = {false}
  customStyling = {{
    cardBackgroundColor: '#ffffff',
    accentColor: '#1976d2',
  }}
/>
```

### CompliancePostureMatrix

**Heatmap visualisation of CIS control compliance status.**

```typescript
import { CompliancePostureMatrix } from './components/CompliancePostureMatrix';

<CompliancePostureMatrix
  complianceData = {complianceData}
  filters = {dashboardFilters}
  onFilterChange = {handleFilterChange}
  userPermissions = {userPermissions}
  accessibilityPrefs = {accessibilityPreferences}
/>
```

### TrendAnalysisChart

**Line chart displaying historical compliance trends.**

```typescript
import { TrendAnalysisChart } from './components/TrendAnalysisChart';

<TrendAnalysisChart
  trendData = {historicalData}
  timeRange = "30d"
  onTimeRangeChange = {handleTimeRangeChange}
  onExportRequest = {handleExport}
  accessibilityPrefs = {accessibilityPreferences}
  isMobile = {false}
/>
```

### CriticalFindingsAlert

**Real-time critical alert display and management.**

```typescript
import { CriticalFindingsAlert } from './components/CriticalFindingsAlert';

<CriticalFindingsAlert
  alerts = {criticalAlerts}
  onAlertAction = {handleAlertAction}
  userPermissions = {userPermissions}
  connectionStatus = "connected"
/>
```

## Custom Hooks

### useComplianceData

**Manages compliance data fetching and state.**

```typescript
import { useComplianceData } from './hooks/useComplianceData';

const {
  complianceData,
  loadComplianceData,
  refreshData,
  isLoading,
  error,
}  =  useComplianceData({
  userPermissions,
  initialData,
  onError: (error)  = > console.error(error),
});
```

### useWebSocketConnection

**Manages WebSocket connection for real-time updates.**

```typescript
import { useWebSocketConnection } from './hooks/useWebSocketConnection';

const {
  connectionStatus,
  subscribe,
  unsubscribe,
  sendMessage,
}  =  useWebSocketConnection({
  url: 'ws://localhost:8000/ws',
  onMessage: handleMessage,
  onError: handleError,
});
```

### usePerformanceMetrics

**Tracks and reports performance metrics.**

```typescript
import { usePerformanceMetrics } from './hooks/usePerformanceMetrics';

const {
  recordMetric,
  getMetrics,
}  =  usePerformanceMetrics();

recordMetric('dashboard_load_time', 1500);
const metrics  =  getMetrics();
```

### useAccessibilityPreferences

**Manages user accessibility settings.**

```typescript
import { useAccessibilityPreferences } from './hooks/useAccessibilityPreferences';

const {
  preferences,
  updatePreference,
}  =  useAccessibilityPreferences();
```

## State Management

### Global State Architecture

The dashboard uses React Context API for global state management:

```typescript
// ComplianceDataContext - Compliance assessment data
import { ComplianceDataProvider, useComplianceData } from './context/ComplianceDataContext';

// UserPreferencesContext - User settings and filters
import { UserPreferencesProvider, useUserPreferences } from './context/UserPreferencesContext';

// AlertContext - Alert management
import { AlertProvider, useAlerts } from './context/AlertContext';
```

### State Flow

```
User Action → Component Event Handler → Context Update → 
State Change → Component Re-render → UI Update
```

### Local Component State

Components use `useState` and `useReducer` for local state:

```typescript
// Simple state
const [loading, setLoading]  =  useState(false);

// Complex state with reducer
const [state, dispatch]  =  useReducer(reducer, initialState);
```

## API Integration

### REST API Communication

```typescript
import axios from 'axios';

// API client configuration
const apiClient  =  axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
apiClient.interceptors.request.use((config)  = > {
  const token  =  localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization  =  `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response)  = > response,
  (error)  = > {
    if (error.response?.status  =  =  =  401) {
      // Handle authentication error
    }
    return Promise.reject(error);
  }
);

// Fetch compliance metrics
export const fetchComplianceMetrics  =  async ()  = > {
  const response  =  await apiClient.get('/compliance/metrics');
  return response.data;
};
```

### Data Fetching Patterns

```typescript
// Using custom hook
const { data, loading, error }  =  useComplianceData();

// Manual fetching with error handling
const fetchData  =  async ()  = > {
  try {
    setLoading(true);
    const data  =  await fetchComplianceMetrics();
    setComplianceData(data);
  } catch (error) {
    setError(error);
  } finally {
    setLoading(false);
  }
};
```

## Real-Time Communication

### WebSocket Integration

```typescript
// WebSocket connection management
const ws  =  new WebSocket(process.env.REACT_APP_WEBSOCKET_URL);

ws.onopen  =  ()  = > {
  console.log('WebSocket connected');
  setConnectionStatus('connected');
};

ws.onmessage  =  (event)  = > {
  const message  =  JSON.parse(event.data);
  handleMessage(message);
};

ws.onerror  =  (error)  = > {
  console.error('WebSocket error:', error);
  setConnectionStatus('error');
};

ws.onclose  =  ()  = > {
  console.log('WebSocket disconnected');
  setConnectionStatus('disconnected');
  // Attempt reconnection
  setTimeout(reconnect, 5000);
};
```

### Message Handling

```typescript
const handleMessage  =  (message: WebSocketMessage)  = > {
  switch (message.type) {
    case 'compliance-data-update':
      updateComplianceData(message.data);
      break;
    case 'critical-alert-new':
      addNewAlert(message.alert);
      break;
    case 'assessment-status-change':
      updateAssessmentStatus(message.status);
      break;
  }
};
```

## Performance Optimisation

### Code Splitting

```typescript
// Lazy load components
const TrendAnalysisChart  =  React.lazy(()  = > import('./components/TrendAnalysisChart'));

// Use with Suspense
<Suspense fallback = {<LoadingSpinner />}>
  <TrendAnalysisChart data = {trendData} />
</Suspense>
```

### Memoization

```typescript
//Memoise expensive calculations
const dashboardMetrics  =  useMemo(()  = > {
  return calculateMetrics(complianceData, filters);
}, [complianceData, filters]);

//Memoise components
const MemoizedChart  =  React.memo(TrendAnalysisChart);
```

### Virtualisation

```typescript
// Virtual scrolling for large lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height = {600}
  itemCount = {alerts.length}
  itemSize = {80}
  width = "100%"
>
  {({ index, style })  = > (
    <AlertItem alert = {alerts[index]} style = {style} />
  )}
</FixedSizeList>
```

## Security Implementation

### Authentication

```typescript
// OAuth 2.0 with PKCE
import { PublicClientApplication } from '@azure/msal-browser';

const msalConfig  =  {
  auth: {
    clientId: process.env.REACT_APP_AZURE_AD_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${process.env.REACT_APP_AZURE_AD_TENANT_ID}`,
    redirectUri: window.location.origin,
  },
};

const msalInstance  =  new PublicClientApplication(msalConfig);

// Login
await msalInstance.loginPopup({
  scopes: ['User.Read', 'Compliance.Read'],
});

// Get token
const tokenResponse  =  await msalInstance.acquireTokenSilent({
  scopes: ['Compliance.Read'],
});
```

### Content Security Policy

```html
<!-- index.html -->
<meta http-equiv = "Content-Security-Policy" 
      content = "default-src 'self'; 
               script-src 'self' 'nonce-{RANDOM_NONCE}'; 
               style-src 'self' 'unsafe-inline'; 
               img-src 'self' data: https:; 
               connect-src 'self' wss://api.example.com;">
```

### Input Sanitisation

```typescript
import DOMPurify from 'dompurify';

// Sanitise user input
const sanitisedInput  =  DOMPurify.sanitize(userInput);

// Safe rendering
<div dangerouslySetInnerHTML = {{ __html: sanitisedInput }} />
```

## Accessibility Features

### ARIA Labels

```typescript
<button
  aria-label = "Refresh compliance metrics"
  aria-describedby = "refresh-help-text"
  onClick = {handleRefresh}
>
  <RefreshIcon />
</button>
<span id = "refresh-help-text" className = "sr-only">
  Click to reload all compliance data
</span>
```

### Keyboard Navigation

```typescript
const handleKeyDown  =  (event: React.KeyboardEvent)  = > {
  switch (event.key) {
    case 'Enter':
    case ' ':
      handleClick();
      break;
    case 'Escape':
      handleClose();
      break;
    case 'ArrowDown':
      focusNextItem();
      break;
    case 'ArrowUp':
      focusPreviousItem();
      break;
  }
};
```

### Screen Reader Support

```typescript
// Live regions for dynamic content
<div aria-live = "polite" aria-atomic = "true">
  {alertMessage}
</div>

// Status messages
<div role = "status" aria-live = "assertive">
  Loading compliance data...
</div>
```

## Testing Strategy

### Unit Tests

```typescript
// ComplianceMetricsDashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ComplianceMetricsDashboard from './ComplianceMetricsDashboard';

describe('ComplianceMetricsDashboard', ()  = > {
  it('renders dashboard with metrics', ()  = > {
    render(<ComplianceMetricsDashboard userPermissions = {mockPermissions} />);
    
    expect(screen.getByText('Microsoft 365 Compliance Dashboard')).toBeInTheDocument();
  });

  it('handles metric click interaction', async ()  = > {
    const handleClick  =  jest.fn();
    render(
      <ComplianceMetricsDashboard 
        userPermissions = {mockPermissions}
        onMetricClick = {handleClick}
      />
    );
    
    await userEvent.click(screen.getByText('Overall Compliance'));
    expect(handleClick).toHaveBeenCalledWith('overall-compliance', 85);
  });
});
```

### Integration Tests

```typescript
// dashboard.integration.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import App from './App';

const server  =  setupServer(
  rest.get('/api/v1/compliance/metrics', (req, res, ctx)  = > {
    return res(ctx.json(mockMetrics));
  })
);

beforeAll(()  = > server.listen());
afterEach(()  = > server.resetHandlers());
afterAll(()  = > server.close());

describe('Dashboard Integration', ()  = > {
  it('fetches and displays compliance data', async ()  = > {
    render(<App />);
    
    await waitFor(()  = > {
      expect(screen.getByText('85%')).toBeInTheDocument();
    });
  });
});
```

### E2E Tests

```typescript
// dashboard.e2e.test.ts
import puppeteer from 'puppeteer';

describe('Dashboard E2E', ()  = > {
  let browser;
  let page;

  beforeAll(async ()  = > {
    browser  =  await puppeteer.launch();
    page  =  await browser.newPage();
  });

  afterAll(async ()  = > {
    await browser.close();
  });

  it('loads dashboard and displays metrics', async ()  = > {
    await page.goto('http://localhost:3000');
    await page.waitForSelector('.metric-card');
    
    const metricText  =  await page.$eval('.metric-value', el  = > el.textContent);
    expect(metricText).toBe('85%');
  });
});
```

## Deployment Guidelines

### Production Build

```bash
# Build optimised production bundle
npm run build

# Build output in build/ directory
# Files are minified, hashed, and optimised
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from = builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```bash
# Build and run Docker container
docker build -t autoaudit-dashboard .
docker run -p 80:80 autoaudit-dashboard
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: compliance-dashboard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: compliance-dashboard
  template:
    metadata:
      labels:
        app: compliance-dashboard
    spec:
      containers:
      - name: dashboard
        image: autoaudit-dashboard:latest
        ports:
        - containerPort: 80
        env:
        - name: REACT_APP_API_URL
          valueFrom:
            configMapKeyRef:
              name: dashboard-config
              key: api-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Development Workflow

### Branch Strategy

```bash
# Feature development
git checkout -b feature/T2-FE-006-executive-summary
git commit -m "feat: implement executive summary cards"
git push origin feature/T2-FE-006-executive-summary

# Create pull request
# After review and approval, merge to main
```

### Code Quality Checks

```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Type check
npm run type-check

# Run all checks
npm run validate
```

### Pre-commit Hooks

```json
// package.json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged"
    }
  },
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write",
      "git add"
    ]
  }
}
```

## Troubleshooting Guide

### Common Issues

**Issue: Dashboard not loading**
```bash
# Check API connection
curl http://localhost:8000/api/v1/compliance/metrics

# Verify environment variables
echo $REACT_APP_API_URL

# Check browser console for errors
# Open DevTools → Console tab
```

**Issue: WebSocket connection fails**
```bash
# Verify WebSocket URL
echo $REACT_APP_WEBSOCKET_URL

# Test WebSocket connection
wscat -c ws://localhost:8000/ws

# Check firewall settings
# Ensure port 8000 is open
```

**Issue: Performance degradation**
```bash
# Profile React components
# Open React DevTools → Profiler tab
# Record interaction and analyse render times

# Check bundle size
npm run build -- --stats
npx webpack-bundle-analyzer build/bundle-stats.json
```

### Debug Mode

```typescript
// Enable debug logging
localStorage.setItem('debug', 'autoaudit:*');

// View performance metrics
console.log(window.__PERFORMANCE_METRICS__);

// Check React component tree
console.log(window.__REACT_DEVTOOLS_GLOBAL_HOOK__);
```

## Contributing Guidelines

### Code Style

- Follow TypeScript strict mode
- Use functional components with hooks
- Implement proper error boundaries
- Write comprehensive JSDoc comments
- Maintain 95%+ test coverage

### Pull Request Process

1. Create a feature branch from `main`
2. Implement changes with tests
3. Run validation: `npm run validate`
4. Update documentation
5. Submit a pull request with a description
6. Address review comments
7. Merge after approval

### Commit Message Convention

```
feat: add new executive summary cards
fix: resolve WebSocket reconnection issue
docs: update API integration guide
test: add unit tests for metric calculations
refactor: optimise dashboard rendering
perf: implement virtualisation for alert list
```
