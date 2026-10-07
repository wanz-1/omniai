"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import {
  Users, Activity, TrendingUp, DollarSign, AlertTriangle, Loader2,
  Search, Shield, CheckCircle, XCircle
} from "lucide-react";

interface Overview {
  total_users: number;
  total_organizations: number;
  total_projects: number;
  total_agents: number;
  total_api_calls: number;
  active_users_24h: number;
  active_users_7d: number;
  revenue_mtd: number;
  new_users_today: number;
  new_orgs_today: number;
}

interface AdminUser {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  role: string;
  two_factor_enabled: boolean;
  credits_balance: number;
  created_at: string;
  last_login_at: string | null;
  organization_count: number;
  project_count: number;
}

type Tab = "overview" | "users" | "marketplace" | "usage";

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("overview");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [userSearch, setUserSearch] = useState("");
  const [usersLoading, setUsersLoading] = useState(false);

  useEffect(() => {
    if (tab === "overview") {
      const loadOverview = async () => {
        try {
          const res = await apiClient.get("/admin/overview");
          setOverview(res.data);
        } catch {
          toast.error("Failed to load overview");
        }
      };
      loadOverview();
    }
    if (tab === "users") {
      const loadUsers = async () => {
        setUsersLoading(true);
        try {
          const params: any = { limit: 50 };
          const res = await apiClient.get("/admin/users", { params });
          setUsers(res.data);
        } catch {
          toast.error("Failed to load users");
        } finally {
          setUsersLoading(false);
        }
      };
      loadUsers();
    }
  }, [tab]);

  const loadOverview = async () => {
    try {
      const res = await apiClient.get("/admin/overview");
      setOverview(res.data);
    } catch {
      toast.error("Failed to load overview");
    }
  };

  const loadUsers = async (search?: string) => {
    setUsersLoading(true);
    try {
      const params: any = { limit: 50 };
      if (search || userSearch) params.search = search || userSearch;
      const res = await apiClient.get("/admin/users", { params });
      setUsers(res.data);
    } catch {
      toast.error("Failed to load users");
    } finally {
      setUsersLoading(false);
    }
  };

  const handleSuspend = async (userId: string, name: string) => {
    try {
      await apiClient.put(`/admin/users/${userId}/suspend`);
      toast.success(`${name} suspended`);
      loadUsers();
    } catch {
      toast.error("Failed to suspend user");
    }
  };

  const handleRestore = async (userId: string, name: string) => {
    try {
      await apiClient.put(`/admin/users/${userId}/restore`);
      toast.success(`${name} restored`);
      loadUsers();
    } catch {
      toast.error("Failed to restore user");
    }
  };

  const tabs: { key: Tab; label: string; icon: any }[] = [
    { key: "overview", label: "Overview", icon: Activity },
    { key: "users", label: "Users", icon: Users },
    { key: "marketplace", label: "Marketplace", icon: Shield },
    { key: "usage", label: "Usage", icon: TrendingUp },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <p className="text-muted-foreground mt-1">Monitor and manage the OmniAI platform</p>
      </div>

      <div className="flex gap-2 border-b pb-2">
        {tabs.map(({ key, label, icon: Icon }) => (
          <Button
            key={key}
            variant={tab === key ? "primary" : "ghost"}
            size="sm"
            onClick={() => setTab(key)}
          >
            <Icon className="w-4 h-4 mr-2" />
            {label}
          </Button>
        ))}
      </div>

      {tab === "overview" && overview && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                <Users className="w-4 h-4" /> Total Users
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{overview.total_users}</p>
              <p className="text-xs text-muted-foreground">+{overview.new_users_today} today</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                <Activity className="w-4 h-4" /> Active Users
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{overview.active_users_24h}</p>
              <p className="text-xs text-muted-foreground">{overview.active_users_7d} in 7 days</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                <DollarSign className="w-4 h-4" /> Revenue (MTD)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">${overview.revenue_mtd.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                <TrendingUp className="w-4 h-4" /> API Calls
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{overview.total_api_calls.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">Organizations</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{overview.total_organizations}</p>
              <p className="text-xs text-muted-foreground">+{overview.new_orgs_today} today</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">Projects</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{overview.total_projects}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">AI Agents</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{overview.total_agents}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {tab === "users" && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                className="flex h-10 w-full rounded-lg border border-input bg-background pl-10 pr-3 py-2 text-sm"
                placeholder="Search users..."
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && loadUsers()}
              />
            </div>
            <Button size="sm" onClick={() => loadUsers()}>Search</Button>
          </div>

          {usersLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          ) : (
            <div className="space-y-2">
              {users.map((u) => (
                <div key={u.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold shrink-0">
                      {u.display_name.charAt(0).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{u.display_name}</p>
                      <p className="text-xs text-muted-foreground truncate">{u.email}</p>
                    </div>
                    <div className="hidden md:flex items-center gap-2 ml-4">
                      <Badge variant={u.is_active ? "success" : "error"}>{u.is_active ? "Active" : "Suspended"}</Badge>
                      {u.is_superuser && <Badge variant="default">Admin</Badge>}
                      {u.two_factor_enabled && <Badge variant="outline">2FA</Badge>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-muted-foreground hidden sm:block">
                      {u.organization_count} orgs
                    </span>
                    {u.is_active ? (
                      <Button variant="ghost" size="sm" onClick={() => handleSuspend(u.id, u.display_name)}>
                        <AlertTriangle className="w-4 h-4 text-yellow-500" />
                      </Button>
                    ) : (
                      <Button variant="ghost" size="sm" onClick={() => handleRestore(u.id, u.display_name)}>
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
              {users.length === 0 && (
                <p className="text-center text-muted-foreground py-8">No users found</p>
              )}
            </div>
          )}
        </div>
      )}

      {tab === "marketplace" && (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-muted-foreground">
              Marketplace moderation is available via the Admin API.
              Use the <code className="text-sm bg-muted px-1 rounded">/admin/marketplace/items</code> endpoint to review and approve/reject submissions.
            </p>
          </CardContent>
        </Card>
      )}

      {tab === "usage" && (
        <Card>
          <CardHeader>
            <CardTitle>Daily Usage</CardTitle>
            <CardDescription>Platform usage over the last 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Usage analytics available via <code className="text-sm bg-muted px-1 rounded">/admin/usage/daily</code> API endpoint.
              A chart visualization will be added in a future update.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
