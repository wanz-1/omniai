"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BarChart3, CheckCircle, XCircle, Zap, Clock, ThumbsUp, TrendingUp, Target, Brain } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentAnalyticsData {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  total_tokens: number;
  avg_duration_ms?: number;
  avg_satisfaction?: number;
  top_skills?: { name: string; count: number }[];
  daily_usage?: Record<string, number>;
}

interface AgentAnalyticsProps {
  analytics?: AgentAnalyticsData | null;
  className?: string;
}

function dailyUsageSeries(daily_usage?: Record<string, number>) {
  if (!daily_usage) return [];
  return Object.entries(daily_usage)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({ date, tasks: count }));
}

export function AgentAnalyticsPanel({ analytics, className }: AgentAnalyticsProps) {
  const stats = [
    { label: "Total Tasks", value: analytics?.total_tasks ?? 0, icon: BarChart3, color: "text-blue-500 bg-blue-50 dark:bg-blue-950" },
    { label: "Completed", value: analytics?.completed_tasks ?? 0, icon: CheckCircle, color: "text-green-500 bg-green-50 dark:bg-green-950" },
    { label: "Failed", value: analytics?.failed_tasks ?? 0, icon: XCircle, color: "text-red-500 bg-red-50 dark:bg-red-950" },
    { label: "Tokens Used", value: (analytics?.total_tokens ?? 0).toLocaleString(), icon: Zap, color: "text-purple-500 bg-purple-50 dark:bg-purple-950" },
    { label: "Avg Duration", value: analytics?.avg_duration_ms ? `${(analytics.avg_duration_ms / 1000).toFixed(1)}s` : "N/A", icon: Clock, color: "text-amber-500 bg-amber-50 dark:bg-amber-950" },
    { label: "Satisfaction", value: analytics?.avg_satisfaction != null ? `${(analytics.avg_satisfaction * 100).toFixed(0)}%` : "N/A", icon: ThumbsUp, color: "text-emerald-500 bg-emerald-50 dark:bg-emerald-950" },
  ];

  const usage = dailyUsageSeries(analytics?.daily_usage);
  const hasUsage = usage.some((d) => d.tasks > 0);
  const taskBreakdown = [
    { name: "Completed", value: analytics?.completed_tasks ?? 0 },
    { name: "Failed", value: analytics?.failed_tasks ?? 0 },
  ];
  const hasTasks = (analytics?.total_tasks ?? 0) > 0;

  return (
    <div className={cn("space-y-4", className)}>
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="p-4 rounded-xl border border-border bg-card hover:shadow-sm transition-shadow">
              <div className={cn("p-2 rounded-lg w-fit mb-2", stat.color)}>
                <Icon className="w-4 h-4" />
              </div>
              <p className="text-xl font-bold">{stat.value}</p>
              <p className="text-xs text-muted-foreground mt-1">{stat.label}</p>
            </div>
          );
        })}
      </div>

      {analytics?.top_skills && analytics.top_skills.length > 0 && (
        <div className="p-4 rounded-xl border border-border bg-card">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-muted-foreground" />
            <h3 className="text-sm font-medium">Top Skills Used</h3>
          </div>
          <div className="space-y-2">
            {analytics.top_skills.map((skill, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground w-5">{i + 1}.</span>
                <div className="flex-1">
                  <div className="flex justify-between text-xs mb-1">
                    <span>{skill.name}</span>
                    <span className="text-muted-foreground">{skill.count}</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden">
                    <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${Math.min(100, (skill.count / Math.max(...analytics.top_skills!.map((s) => s.count))) * 100)}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="p-4 rounded-xl border border-border bg-card">
        <div className="flex items-center gap-2 mb-3">
          <Brain className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm font-medium">Agent Performance</h3>
        </div>
        {hasUsage ? (
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={usage} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="taskFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.1} />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(d: string) => d.slice(5)} stroke="currentColor" opacity={0.6} />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} stroke="currentColor" opacity={0.6} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="tasks" name="Tasks" stroke="#3b82f6" strokeWidth={2} fill="url(#taskFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="flex items-center justify-center h-24 text-muted-foreground">
            <p className="text-xs">No task activity recorded yet</p>
          </div>
        )}
        {hasTasks && (
          <div className="mt-3">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-muted-foreground" />
              <h4 className="text-xs font-medium">Task Outcomes</h4>
            </div>
            <div className="h-32">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={taskBreakdown} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.1} />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="currentColor" opacity={0.6} />
                  <YAxis tick={{ fontSize: 10 }} allowDecimals={false} stroke="currentColor" opacity={0.6} />
                  <Tooltip contentStyle={{ fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="value" name="Tasks" fill="#10b981" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
