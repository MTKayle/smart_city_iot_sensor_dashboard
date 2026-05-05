import { useEffect, useRef, useState } from 'react';
import type { Telemetry, Alert } from '../types';
import { normalizeTelemetry } from '../utils/telemetry';

/**
 * WebSocket connection status
 */
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

/**
 * WebSocket message types from server
 */
interface WebSocketMessage {
  type: 'telemetry' | 'alert' | 'connection_ack' | 'heartbeat' | 'pong';
  data?: Telemetry | Alert;
  message?: string;
}

/**
 * Callback functions for different message types
 */
export interface WebSocketCallbacks {
  onTelemetry?: (data: Telemetry) => void;
  onAlert?: (data: Alert) => void;
  onConnectionAck?: (message: string) => void;
}

/**
 * Custom React hook for managing WebSocket connection lifecycle.
 * 
 * Features:
 * - Automatic connection on mount
 * - Exponential backoff reconnection (1s, 2s, 4s, 8s, max 60s)
 * - Message parsing and type-based dispatch
 * - Connection status tracking
 * - Automatic cleanup on unmount
 * 
 * Requirements: 10.1, 10.2, 10.3, 10.4
 * 
 * @param url - WebSocket server URL (default: ws://backend:8000/ws)
 * @param callbacks - Callback functions for different message types
 * @returns Connection status
 */
export const useWebSocket = (
  url: string = 'ws://backend:8000/ws',
  callbacks: WebSocketCallbacks = {}
): ConnectionStatus => {
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectDelayRef = useRef<number>(1000); // Start with 1 second
  const isMountedRef = useRef<boolean>(true);

  // Store callbacks in refs so connection lifecycle doesn't depend on them
  const callbacksRef = useRef<WebSocketCallbacks>(callbacks);
  callbacksRef.current = callbacks;

  /**
   * Initialize WebSocket connection on mount.
   * Only depends on `url` — callback changes do NOT cause reconnection.
   */
  useEffect(() => {
    isMountedRef.current = true;

    const connect = () => {
      if (!isMountedRef.current) return;

      // Don't create a new connection if one is already open/connecting
      if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
        return;
      }

      try {
        setStatus('connecting');
        const ws = new WebSocket(url);

        ws.onopen = () => {
          if (!isMountedRef.current) {
            ws.close();
            return;
          }
          console.log('WebSocket connected');
          setStatus('connected');
          reconnectDelayRef.current = 1000; // Reset delay on successful connection
        };

        ws.onmessage = (event: MessageEvent) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            const cbs = callbacksRef.current;

            switch (message.type) {
              case 'telemetry':
                if (message.data && cbs.onTelemetry) {
                  // Backend broadcasts nested {data: {co2, pm25, ...}} but UI components
                  // read flat .pm25/.co2/etc. Normalize to expose both shapes,
                  // and derive AQI from PM2.5 (backend doesn't include it in WS payload).
                  cbs.onTelemetry(normalizeTelemetry(message.data as Telemetry));
                }
                break;
              case 'alert':
                if (message.data && cbs.onAlert) {
                  cbs.onAlert(message.data as Alert);
                }
                break;
              case 'connection_ack':
                if (message.message && cbs.onConnectionAck) {
                  cbs.onConnectionAck(message.message);
                }
                break;
              case 'heartbeat':
              case 'pong':
                // Silently handle heartbeat/pong messages
                break;
              default:
                console.warn('Unknown message type:', message.type);
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setStatus('error');
        };

        ws.onclose = () => {
          if (!isMountedRef.current) return;

          console.log('WebSocket disconnected');
          setStatus('disconnected');

          // Implement exponential backoff reconnection (capped at 30s for snappier recovery)
          const delay = Math.min(reconnectDelayRef.current, 30000);
          console.log(`Reconnecting in ${delay}ms...`);

          reconnectTimeoutRef.current = window.setTimeout(() => {
            reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 30000);
            connect();
          }, delay);
        };

        wsRef.current = ws;
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        setStatus('error');

        // Retry connection with exponential backoff
        const delay = Math.min(reconnectDelayRef.current, 60000);
        reconnectTimeoutRef.current = window.setTimeout(() => {
          reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 60000);
          connect();
        }, delay);
      }
    };

    connect();

    /**
     * Cleanup: close connection and clear timeouts on unmount
     */
    return () => {
      isMountedRef.current = false;

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [url]); // Only reconnect if URL changes, NOT on callback changes

  return status;
};
