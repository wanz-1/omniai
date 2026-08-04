"use client";

import { Bot, Star, Download, Clock, MoreVertical } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";

interface AgentCardProps {
  agent: {
    id: string;
    name: string;
    role: string;
    description?: string;
    status: string;
    is_template: boolean;
    template_category?: string;
    icon?: string;
    color?: string;
    download_count: number;
    skills?: { name: string }[];
    created_at: string;
  };
  onSelect?: (id: string) => void;
  className?: string;
}

export function AgentCard({ agent, onSelect, className }: AgentCardProps) {
  const statusColors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
    training: "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
    active: "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400",
    disabled: "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400",
    archived: "bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400",
  };

  return (
    <div
      onClick={() => onSelect?.(agent.id)}
      className={cn(
        "group relative p-4 rounded-xl border border-border bg-card hover:shadow-lg hover:border-primary/30 transition-all duration-200 cursor-pointer",
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-white text-lg font-bold shrink-0"
          style={{ backgroundColor: agent.color || "#2563EB" }}
        >
          {agent.icon || agent.name.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-sm truncate">{agent.name}</h3>
            {agent.is_template && (
              <Badge variant="outline" className="text-[10px] px-1.5 py-0">Template</Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">{agent.role}</p>
          {agent.description && (
            <p className="text-xs text-muted-foreground/70 mt-1 line-clamp-2">{agent.description}</p>
          )}
          {agent.skills && agent.skills.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {agent.skills.slice(0, 3).map((s, i) => (
                <span key={i} className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted text-muted-foreground">
                  {s.name}
                </span>
              ))}
              {agent.skills.length > 3 && (
                <span className="text-[10px] text-muted-foreground">+{agent.skills.length - 3}</span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
          <span className={cn("px-1.5 py-0.5 rounded-full text-[10px]", statusColors[agent.status] || "")}>
            {agent.status}
          </span>
          {agent.is_template && (
            <span className="flex items-center gap-1">
              <Download className="w-3 h-3" />
              {agent.download_count}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {new Date(agent.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
}
