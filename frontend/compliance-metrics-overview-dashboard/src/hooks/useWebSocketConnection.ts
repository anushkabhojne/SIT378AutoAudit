//hooks/useWebSocketConnection.ts

/**
 * useWebSocketConnection.ts
 * 
 * Custom React hook to manage WebSocket connection lifecycle, message handling,
 * automatic reconnection with exponential backoff, and error management.
 * Designed for real-time compliance dashboard updates.
 * 
 * @author Senior Lead, AutoAudit
 */

import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseWebSocketConnectionParams {
  url: string;
  onMessage: (message: WebSocketMessage) => void;
  onError?: (error: Error) => void;
  protocols?: string | string[];
  maxRetries?: number;
  retryInitialDelayMs?: number;
  retryMaxDelayMs?: number;
}

interface UseWebSocketConnectionReturn {
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting' | 'error';
  sendMessage: (data: any) => void;
  subscribe: (type: string, handler: (message: WebSocketMessage) => void) => void;
  unsubscribe: (type: string, handler: (message: WebSocketMessage) => void) => void;
}

/**
 * useWebSocketConnection hook implementation
 * 
 * Manages WebSocket connection with automatic reconnection, message dispatching,
 * and error handling.
 */

export function useWebSocketConnection({
  url,
  onMessage,
  onError,
  protocols,
  maxRetries = 10,
  retryInitialDelayMs = 1000,
  retryMaxDelayMs = 30000,
}: UseWebSocketConnectionParams): UseWebSocketConnectionReturn {
  
  //WebSocket instance reference
  const wsRef = useRef<WebSocket | null>(null);

  //Connection status state
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'reconnecting' | 'error'>('disconnected');

  //Retry count for reconnection attempts
  const retryCountRef = useRef<number>(0);

  //Timer ID for reconnection delay
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  //Message handlers map: message type -> array of handler functions
  const messageHandlersRef = useRef<Map<string, Set<(message: WebSocketMessage) => void>>>(new Map());

  //Flag to track manual close to prevent reconnection
  const manualCloseRef = useRef<boolean>(false);

  /**
   * Dispatching the incoming message to registered handlers and global onMessage callback
   * @param event MessageEvent from WebSocket
   */

  const handleMessage = useCallback(
    
    (event: MessageEvent) => {
      
      try {
        const data = JSON.parse(event.data) as WebSocketMessage;
        
        if (!data.type) {
          throw new Error('Received WebSocket message without type field.');
        }

        //Calling the global onMessage callback
        onMessage(data);

        //Calling the registered handlers for this message type
        const handlers = messageHandlersRef.current.get(data.type);
        
        if (handlers) {
          
          handlers.forEach((handler) => {
            try {
              handler(data);
            } 
            
            catch (handlerError) {
              console.error('Error in WebSocket message handler:', handlerError);
            }
          });
        }
      } 
      
      catch (parseError) {
        console.error('Failed to parse WebSocket message:', parseError);
        
        if (onError) 
          onError(new Error('Invalid WebSocket message format.'));
      }
    },
    
    [onMessage, onError]
  );

  /**
   * Handling the WebSocket open event
   */

  const handleOpen = useCallback(() => {
    
    setConnectionStatus('connected');
    retryCountRef.current = 0;
    
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

  }, []);

  /**
   * Handling the WebSocket close event
   * @param event CloseEvent
   */

  const handleClose = useCallback(
    
    (event: CloseEvent) => {
      wsRef.current = null;
      
      if (manualCloseRef.current) {
        setConnectionStatus('disconnected');
        return;
      }
      
      setConnectionStatus('reconnecting');
      
      //Scheduling reconnection with exponential backoff
      const retryCount = retryCountRef.current;
      const delay = Math.min(retryInitialDelayMs * 2 ** retryCount, retryMaxDelayMs);
      
      reconnectTimerRef.current = setTimeout(() => {
        retryCountRef.current += 1;
        connect();
      }, delay);
    },

    [retryInitialDelayMs, retryMaxDelayMs]
  );

  /**
   * Handling the WebSocket error event
   * @param event Event
   */

  const handleError = useCallback(
    
    (event: Event) => {
      setConnectionStatus('error');
      if (onError) onError(new Error('WebSocket connection error.'));
    },

    [onError]
  );

  /**
   * Establishing the WebSocket connection and setting up event listeners
   */

  const connect = useCallback(() => {
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    try {
      const ws = protocols ? new WebSocket(url, protocols) : new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = handleOpen;
      ws.onmessage = handleMessage;
      ws.onclose = handleClose;
      ws.onerror = handleError;
      setConnectionStatus('reconnecting');
    } 
    
    catch (connectionError) {
      setConnectionStatus('error');
      
      if (onError) 
        onError(new Error('Failed to create WebSocket connection.'));
    }

  }, [url, protocols, handleOpen, handleMessage, handleClose, handleError, onError]);

  /**
   * Sending a message through the WebSocket connection
   * @param data Data to send (will be JSON-stringified)
   */

  const sendMessage = useCallback((data: any) => {
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      
      try {
        wsRef.current.send(JSON.stringify(data));
      } 
      
      catch (sendError) {
        console.error('Failed to send WebSocket message:', sendError);
        
        if (onError) 
          onError(new Error('Failed to send WebSocket message.'));
      }
    } 
    
    else {
      console.warn('WebSocket is not open. Message not sent.');
    }

  }, [onError]);

  /**
   * Subscribing to messages of a specific type
   * @param type Message type string
   * @param handler Handler function to call on message
   */

  const subscribe = useCallback((type: string, handler: (message: WebSocketMessage) => void) => {
    
    const handlers = messageHandlersRef.current.get(type) || new Set();
    handlers.add(handler);
    messageHandlersRef.current.set(type, handlers);

  }, []);

  /**
   * Unsubscribing a handler from a specific message type
   * @param type Message type string
   * @param handler Handler function to remove
   */

  const unsubscribe = useCallback((type: string, handler: (message: WebSocketMessage) => void) => {
    
    const handlers = messageHandlersRef.current.get(type);
    
    if (handlers) {
      handlers.delete(handler);

      if (handlers.size === 0) {
        messageHandlersRef.current.delete(type);
      }
    }

  }, []);

  /**
   * Effect: Establishing a WebSocket connection on mount and cleaning up on unmount
   */

  useEffect(() => {
    manualCloseRef.current = false;
    connect();

    return () => {
      
      manualCloseRef.current = true;
      
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
    
  }, [connect]);

  return {
    connectionStatus,
    sendMessage,
    subscribe,
    unsubscribe,
  };
}
