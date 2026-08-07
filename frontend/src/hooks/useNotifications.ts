"use client";

import { useCallback, useEffect, useState } from "react";
import { useWebSocket } from "./useWebSocket";
import { notificationsApi } from "@/lib/api-client";

interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  body?: string;
  link?: string;
  is_read: boolean;
  created_at: string;
}

interface NotificationPayload {
  payload: Notification;
  type?: string;
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const { on } = useWebSocket();

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await notificationsApi.list(true);
      const data = response.data as { items?: Notification[] };
      setNotifications(data.items || []);
    } catch {
      // Silently ignore fetch errors (e.g., offline)
    }
  }, []);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const response = await notificationsApi.unreadCount();
      const data = response.data as { unread_count?: number };
      setUnreadCount(data.unread_count || 0);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();
  }, [fetchNotifications, fetchUnreadCount]);

  useEffect(() => {
    const unsubscribe = on("notification", (raw: unknown) => {
      try {
        const msg = raw as NotificationPayload;
        const payload = msg.payload;
        if (!payload || !payload.id) return;
        setNotifications((prev) => [payload, ...prev]);
        setUnreadCount((prev) => prev + 1);
      } catch {
        // ignore malformed payload
      }
    });
    return () => {
      try {
        unsubscribe();
      } catch {
        // ignore
      }
    };
  }, [on]);

  const markAsRead = useCallback(async (id: string) => {
    try {
      await notificationsApi.markRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      // ignore
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await notificationsApi.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      // ignore
    }
  }, []);

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    refresh: fetchNotifications,
  };
}
