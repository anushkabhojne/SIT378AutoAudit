//hooks/useComplianceData.ts

/**
 * useComplianceData.ts
 * 
 * Custom React hook to manage loading, refreshing, and error handling of compliance data.
 * Integrates with backend API to fetch Microsoft 365 compliance assessment results.
 * Supports initial data injection, error reporting, and loading state management.
 * 
 * @author Senior Lead, AutoAudit
 */

import { useState, useEffect, useCallback } from 'react';
import axios, { AxiosError, CancelTokenSource } from 'axios';
import { ComplianceMetrics, UserPermissions } from '../types/dashboard.types';

/**
 * Hook parameters interface
 */

interface UseComplianceDataParams {
  userPermissions: UserPermissions;
  initialData?: ComplianceMetrics;
  onError?: (error: Error) => void;
}

/**
 * Hook return interface
 */

interface UseComplianceDataReturn {
  complianceData: ComplianceMetrics | null;
  loadComplianceData: () => Promise<ComplianceMetrics>;
  refreshData: () => void;
  isLoading: boolean;
  error: Error | null;
}

/**
 * useComplianceData hook implementation
 * 
 * Manageing the compliance data state, loading, refreshing, and error handling.
 */

export function useComplianceData({
  userPermissions,
  initialData,
  onError,
}: UseComplianceDataParams): UseComplianceDataReturn {
  
  //State for compliance data
  const [complianceData, setComplianceData] = useState<ComplianceMetrics | null>(initialData || null);

  //Loading state
  const [isLoading, setIsLoading] = useState<boolean>(false);

  //Error state
  const [error, setError] = useState<Error | null>(null);

  //Axios cancel token source for request cancellation
  const cancelTokenSourceRef = React.useRef<CancelTokenSource | null>(null);

  /**
   * Fetching the compliance data from the backend API
   */

  const loadComplianceData = useCallback(async (): Promise<ComplianceMetrics> => {
    setIsLoading(true);
    setError(null);

    //Cancelling any ongoing request before starting a new one
    if (cancelTokenSourceRef.current) {
      cancelTokenSourceRef.current.cancel('Operation canceled due to new request.');
    }

    cancelTokenSourceRef.current = axios.CancelToken.source();

    try {
      //API endpoint for compliance data - environment variable or default
      const apiUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

      //Authorisation header with token from userPermissions (assumed to have token)
      const authToken = userPermissions.authToken || '';

      //Perform GET request to fetch compliance data
      const response = await axios.get<ComplianceMetrics>(`${apiUrl}/compliance/assessment`, {
        
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },

        cancelToken: cancelTokenSourceRef.current.token,

        //15 seconds timeout
        timeout: 15000, 
      });

      //Validating the response data structure (basic validation)
      if (!response.data || typeof response.data !== 'object') {
        throw new Error('Invalid compliance data received from server.');
      }

      //Updating the state with the fetched data
      setComplianceData(response.data);
      setIsLoading(false);
      return response.data;
    } 
    
    catch (err) {
      
      if (axios.isCancel(err)) {
        
        //The request was canceled, do not update error state
        setIsLoading(false);
        
        return Promise.reject(new Error('Request canceled'));
      }
      
      const axiosError = err as AxiosError;
      
      const errorMessage =
        axiosError.response?.data?.message ||
        axiosError.message ||
        'Failed to load compliance data from server.';
      
      const errorObj = new Error(errorMessage);
      
      setError(errorObj);
      setIsLoading(false);
      
      if (onError) 
        onError(errorObj);
      
      return Promise.reject(errorObj);
    }

  }, [userPermissions.authToken, onError]);

  /**
   * Refreshing the compliance data by reloading from the API
   */

  const refreshData = useCallback(() => {
    
    loadComplianceData().catch(() => {
      //Error handled in loadComplianceData
    });

  }, [loadComplianceData]);

  /**
   * Effect: If initialData changes externally, updating the state accordingly
   */
  
  useEffect(() => {
    
    if (initialData) {
      setComplianceData(initialData);
      setError(null);
      setIsLoading(false);
    }

  }, [initialData]);

  /**
   * Cleanup: Cancelling any ongoing request on unmount
   */

  useEffect(() => {
    
    return () => {
      
      if (cancelTokenSourceRef.current) {
        cancelTokenSourceRef.current.cancel('Component unmounted.');
      }
    };
    
  }, []);

  return {
    complianceData,
    loadComplianceData,
    refreshData,
    isLoading,
    error,
  };
}
