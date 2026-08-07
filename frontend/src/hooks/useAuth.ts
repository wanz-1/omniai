"use client";

import { create } from "zustand";
import apiClient from "@/lib/api-client";

interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  role: string;
  is_verified: boolean;
  two_factor_enabled: boolean;
  credits_balance: number;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, display_name: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  setUser: (user: User) => void;
  refresh: () => Promise<void>;
  clearError: () => void;
}

function safeLocalStorageGet(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeLocalStorageSet(key: string, value: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, value);
  } catch {
    // ignore
  }
}

function safeLocalStorageRemove(key: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  error: null,

  clearError: () => set({ error: null }),

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post("/auth/login", {
        email,
        password,
      });
      const { access_token, refresh_token, user } = response.data as {
        access_token: string;
        refresh_token: string;
        user?: User;
      };

      if (!access_token || !refresh_token) {
        // If 2FA required, backend returns empty tokens — handle separately
        if (response.data && response.data.requires_2fa) {
          throw new Error("Two-factor authentication required");
        }
        throw new Error("Invalid login response");
      }

      safeLocalStorageSet("access_token", access_token);
      safeLocalStorageSet("refresh_token", refresh_token);

      if (user) {
        set({ user, isAuthenticated: true, isLoading: false });
      } else {
        await get().fetchUser();
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Login failed";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  register: async (email: string, password: string, display_name: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post("/auth/register", {
        email,
        password,
        display_name,
      });
      const { access_token, refresh_token } = response.data as {
        access_token: string;
        refresh_token: string;
      };

      if (access_token && refresh_token) {
        safeLocalStorageSet("access_token", access_token);
        safeLocalStorageSet("refresh_token", refresh_token);
      }

      await get().fetchUser();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Registration failed";
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  logout: () => {
    safeLocalStorageRemove("access_token");
    safeLocalStorageRemove("refresh_token");
    set({ user: null, isAuthenticated: false, isLoading: false, error: null });
  },

  fetchUser: async () => {
    try {
      const token = safeLocalStorageGet("access_token");
      if (!token) {
        set({ user: null, isAuthenticated: false, isLoading: false });
        return;
      }
      const response = await apiClient.get("/users/me");
      set({
        user: response.data as User,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch {
      safeLocalStorageRemove("access_token");
      safeLocalStorageRemove("refresh_token");
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  setUser: (user: User) =>
    set({ user, isAuthenticated: true, isLoading: false, error: null }),

  refresh: async () => {
    await get().fetchUser();
  },
}));
