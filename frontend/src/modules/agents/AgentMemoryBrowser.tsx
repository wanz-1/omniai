"use client";

import { useState } from "react";
import { Brain, Search, Trash2, Filter, RefreshCw, Bookmark, Clock, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

interface Memory {
  id: string;
  key: string;
  content: string;
  memory_type: string;
  category?: string;
  importance: number;
  created_at: string;
}

interface AgentMemoryBrowserProps {
  memories: Memory[];
  onDelete: (id: string) => void;
  onClear: () => void;
  className?: string;
}

export function AgentMemoryBrowser({ memories, onDelete, onClear, className }: AgentMemoryBrowserProps) {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const filtered = memories.filter((m) => {
    const matchesSearch = m.key.toLowerCase().includes(search.toLowerCase()) || m.content.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === "all" || m.memory_type === typeFilter;
    return matchesSearch && matchesType;
  });

  const typeColors: Record<string, string> = {
    fact: "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
    preference: "bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400",
    conversation: "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400",
    decision: "bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400",
    document: "bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400",
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="p-3 border-b border-border space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Memory ({memories.length})
          </h3>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={onClear} disabled={memories.length === 0}>
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search memories..."
            className="w-full pl-8 pr-3 py-1.5 rounded-lg border border-border bg-background text-xs"
          />
        </div>
        <div className="flex gap-1 overflow-x-auto">
          {["all", "fact", "preference", "conversation", "decision", "document"].map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={cn("text-[10px] px-2 py-1 rounded-full whitespace-nowrap transition-colors", typeFilter === t ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-muted/70")}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground p-4">
            <Brain className="w-8 h-8 mb-2 opacity-40" />
            <p className="text-xs">No memories found</p>
          </div>
        )}
        {filtered.map((mem) => (
          <div key={mem.id} className="p-2 rounded-lg border border-border bg-card hover:border-primary/30 transition-colors">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-medium truncate">{mem.key}</span>
                  <span className={cn("text-[10px] px-1 py-0.5 rounded shrink-0", typeColors[mem.memory_type] || "bg-gray-100 text-gray-600")}>
                    {mem.memory_type}
                  </span>
                  {mem.importance >= 7 && <AlertTriangle className="w-3 h-3 text-amber-500 shrink-0" />}
                </div>
                <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">{mem.content}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Clock className="w-2.5 h-2.5 text-muted-foreground" />
                  <span className="text-[10px] text-muted-foreground">{new Date(mem.created_at).toLocaleDateString()}</span>
                  {mem.category && <span className="text-[10px] px-1 py-0.5 rounded bg-muted text-muted-foreground">{mem.category}</span>}
                </div>
              </div>
              <button onClick={() => onDelete(mem.id)} className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-muted-foreground hover:text-red-500 shrink-0">
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
