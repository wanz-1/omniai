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
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, display_name: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  setUser: (user: User) => void;
  refresh: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const response = await apiClient.post("/auth/login", { email, password });
    const { access_token, refresh_token, user } = response.data;
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    if (user) {
      set({ user, isAuthenticated: true, isLoading: false });
    } else {
      await useAuth.getState().fetchUser();
    }
  },

  register: async (email: string, password: string, display_name: string) => {
    const response = await apiClient.post("/auth/register", { email, password, display_name });
    const { access_token, refresh_token } = response.data;
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    await useAuth.getState().fetchUser();
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false, isLoading: false });
  },

  fetchUser: async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        set({ user: null, isAuthenticated: false, isLoading: false });
        return;
      }
      const response = await apiClient.get("/users/me");
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  setUser: (user: User) => set({ user, isAuthenticated: true, isLoading: false }),
  refresh: async () => {
    await useAuth.getState().fetchUser();
  },
}));
