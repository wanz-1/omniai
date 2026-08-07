"use client";

import { useEffect, type ReactNode } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useRouter, usePathname } from "next/navigation";

const publicPaths = [
  "/login",
  "/register",
  "/oauth-callback",
  "/forgot-password",
  "/_next",
  "/favicon.ico",
];

export function AuthProvider({ children }: { children: ReactNode }) {
  const { fetchUser, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // Initial fetch – run once on mount
  useEffect(() => {
    // Use getState to avoid dependency loop; fetchUser is stable but we keep empty deps to run once
    useAuth.getState().fetchUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Redirect logic
  useEffect(() => {
    if (isLoading) return;
    if (!pathname) return;

    const isPublic = publicPaths.some((p) => pathname.startsWith(p));
    // Allow root to decide (landing page may be public)
    const isRoot = pathname === "/";

    if (!isAuthenticated && !isPublic && !isRoot) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, pathname, router]);

  return <>{children}</>;
}
