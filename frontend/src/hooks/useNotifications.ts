"use client";

import { useEffect, useState } from "react";
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

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const { on } = useWebSocket();

  const fetchNotifications = async () => {
    try {
      const response = await notificationsApi.list(true);
      setNotifications(response.data.items || []);
    } catch {}
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await notificationsApi.unreadCount();
      setUnreadCount(response.data.unread_count || 0);
    } catch {}
  };

  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();
  }, []);

  useEffect(() => {
    const unsubscribe = on("notification", (data) => {
      setNotifications((prev) => [data.payload, ...prev]);
      setUnreadCount((prev) => prev + 1);
    });
    return () => { unsubscribe(); };
  }, [on]);

  const markAsRead = async (id: string) => {
    try {
      await notificationsApi.markRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {}
  };

  const markAllAsRead = async () => {
    try {
      await notificationsApi.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {}
  };

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    refresh: fetchNotifications,
  };
}
