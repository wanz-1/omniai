"use client";

import { useEffect, useCallback } from "react";
import { wsClient } from "@/lib/ws-client";
import { useAuth } from "./useAuth";

export function useWebSocket() {
  const { isAuthenticated, user } = useAuth();

  useEffect(() => {
    if (isAuthenticated && user) {
      const token = localStorage.getItem("access_token");
      if (token) {
        wsClient.connect(token);
        wsClient.subscribe(`notifications:${user.id}`);
      }
    }
    return () => {
      wsClient.disconnect();
    };
  }, [isAuthenticated, user?.id]);

  const subscribe = useCallback((channel: string) => {
    wsClient.subscribe(channel);
  }, []);

  const unsubscribe = useCallback((channel: string) => {
    wsClient.unsubscribe(channel);
  }, []);

  const send = useCallback((data: any) => {
    wsClient.send(data);
  }, []);

  const on = useCallback((event: string, handler: (data: any) => void) => {
    return wsClient.on(event, handler);
  }, []);

  return { subscribe, unsubscribe, send, on, isConnected: wsClient.isConnected() };
}
