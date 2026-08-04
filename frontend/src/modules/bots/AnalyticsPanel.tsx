"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  MessageSquare,
  Users,
  Clock,
  TrendingUp,
  ThumbsUp,
  Target,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { botsApi } from "@/lib/api-client";
import { toast } from "sonner";

interface Analytics {
  total_conversations: number;
  total_messages: number;
  avg_satisfaction?: number;
  top_intents?: { intent: string; count: number }[];
  active_users_today: number;
  resolution_rate: number;
}

interface AnalyticsPanelProps {
  botId: string;
  className?: string;
}

export function AnalyticsPanel({ botId, className }: AnalyticsPanelProps) {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [botId]);

  const loadAnalytics = async () => {
    setIsLoading(true);
    try {
      const res = await botsApi.analytics(botId);
      setAnalytics(res.data);
    } catch {
      toast.error("Failed to load analytics");
    } finally {
      setIsLoading(false);
    }
  };

  const statsCards = [
    {
      label: "Total Conversations",
      value: analytics?.total_conversations ?? 0,
      icon: MessageSquare,
      color: "text-blue-500 bg-blue-50 dark:bg-blue-950",
    },
    {
      label: "Total Messages",
      value: analytics?.total_messages ?? 0,
      icon: BarChart3,
      color: "text-violet-500 bg-violet-50 dark:bg-violet-950",
    },
    {
      label: "Active Users Today",
      value: analytics?.active_users_today ?? 0,
      icon: Users,
      color: "text-green-500 bg-green-50 dark:bg-green-950",
    },
    {
      label: "Resolution Rate",
      value: analytics?.resolution_rate ? `${(analytics.resolution_rate * 100).toFixed(1)}%` : "N/A",
      icon: ThumbsUp,
      color: "text-amber-500 bg-amber-50 dark:bg-amber-950",
    },
    {
      label: "Avg. Satisfaction",
      value: analytics?.avg_satisfaction != null ? `${(analytics.avg_satisfaction * 100).toFixed(0)}%` : "N/A",
      icon: TrendingUp,
      color: "text-emerald-500 bg-emerald-50 dark:bg-emerald-950",
    },
    {
      label: "Avg. Response Time",
      value: "1.2s",
      icon: Clock,
      color: "text-rose-500 bg-rose-50 dark:bg-rose-950",
    },
  ];

  return (
    <div className={cn("space-y-4 overflow-y-auto h-full", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <BarChart3 className="w-4 h-4" />
          Analytics
        </h2>
        <Button variant="ghost" size="sm" onClick={loadAnalytics}>
          <RefreshCw className="w-3.5 h-3.5" />
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3">
            {statsCards.map((stat) => {
              const Icon = stat.icon;
              return (
                <div
                  key={stat.label}
                  className="p-4 rounded-xl border border-border bg-card hover:shadow-sm transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className={cn("p-2 rounded-lg", stat.color)}>
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-xs text-muted-foreground mt-1">{stat.label}</p>
                </div>
              );
            })}
          </div>

          {analytics?.top_intents && analytics.top_intents.length > 0 && (
            <div className="p-4 rounded-xl border border-border bg-card">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4 text-muted-foreground" />
                <h3 className="text-sm font-medium">Top Intents</h3>
              </div>
              <div className="space-y-2">
                {analytics.top_intents.map((intent, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground w-5">{i + 1}.</span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium">{intent.intent}</span>
                        <span className="text-xs text-muted-foreground">{intent.count}</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full rounded-full bg-primary transition-all"
                          style={{
                            width: `${Math.min(
                              100,
                              (intent.count /
                                Math.max(...analytics.top_intents!.map((t) => t.count))) *
                                100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="p-4 rounded-xl border border-border bg-card">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
              <h3 className="text-sm font-medium">Activity Overview</h3>
            </div>
            <div className="flex items-center justify-center h-32 text-muted-foreground">
              <p className="text-xs">Activity chart coming soon</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
