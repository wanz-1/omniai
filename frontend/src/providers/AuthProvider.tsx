"use client";

import { useEffect, type ReactNode } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useRouter, usePathname } from "next/navigation";

const publicPaths = ["/login", "/register", "/oauth-callback", "/forgot-password"];

export function AuthProvider({ children }: { children: ReactNode }) {
  const { fetchUser, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  useEffect(() => {
    if (!isLoading) {
      const isPublic = publicPaths.some((p) => pathname?.startsWith(p));
      if (!isAuthenticated && !isPublic && pathname !== "/") {
        router.push("/login");
      }
    }
  }, [isLoading, isAuthenticated, pathname, router]);

  return <>{children}</>;
}
