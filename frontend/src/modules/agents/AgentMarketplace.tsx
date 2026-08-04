"use client";

import { useState } from "react";
import { Store, Download, Star, Search, Bot, DollarSign, ArrowRight, Clock, Filter } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

interface MarketplaceAgent {
  id: string;
  name: string;
  role: string;
  description?: string;
  icon?: string;
  color?: string;
  price?: number;
  download_count: number;
  skills?: { name: string }[];
  template_category?: string;
  created_at: string;
}

interface AgentMarketplaceProps {
  agents: MarketplaceAgent[];
  onClone: (id: string) => void;
  isCloning?: string | null;
  className?: string;
}

const CATEGORIES = [
  { id: "all", label: "All" },
  { id: "finance", label: "Finance" },
  { id: "hr", label: "HR" },
  { id: "research", label: "Research" },
  { id: "marketing", label: "Marketing" },
  { id: "project_management", label: "Project Mgmt" },
  { id: "procurement", label: "Procurement" },
  { id: "legal", label: "Legal" },
  { id: "education", label: "Education" },
  { id: "healthcare", label: "Healthcare" },
];

export function AgentMarketplace({ agents, onClone, isCloning, className }: AgentMarketplaceProps) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");

  const filtered = agents.filter((a) => {
    const matchesSearch = a.name.toLowerCase().includes(search.toLowerCase()) || a.role.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = category === "all" || a.template_category === category;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className={cn("animate-fade-in", className)}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Store className="w-6 h-6" />
            Agent Marketplace
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Discover and use specialized AI agents</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search agents..." className="pl-9 pr-3 py-2 rounded-lg border border-border bg-background text-sm w-64" />
        </div>
      </div>

      <div className="flex gap-1 overflow-x-auto pb-2 mb-4">
        {CATEGORIES.map((c) => (
          <button key={c.id} onClick={() => setCategory(c.id)} className={cn("text-xs px-3 py-1.5 rounded-full whitespace-nowrap transition-colors", category === c.id ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-muted/70")}>
            {c.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.length === 0 && (
          <div className="col-span-full flex flex-col items-center justify-center py-16 text-muted-foreground">
            <Store className="w-12 h-12 mb-3 opacity-40" />
            <p className="text-sm font-medium">No agents found</p>
            <p className="text-xs mt-1">Try a different search or category</p>
          </div>
        )}
        {filtered.map((agent) => (
          <div key={agent.id} className="p-4 rounded-xl border border-border bg-card hover:shadow-lg transition-all duration-200 group">
            <div className="flex items-start gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white text-lg font-bold shrink-0" style={{ backgroundColor: agent.color || "#2563EB" }}>
                {agent.icon || agent.name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-sm">{agent.name}</h3>
                <p className="text-xs text-muted-foreground">{agent.role}</p>
              </div>
              {agent.price != null && agent.price > 0 && (
                <Badge variant="outline" className="text-xs">${agent.price}</Badge>
              )}
            </div>
            {agent.description && <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{agent.description}</p>}
            {agent.skills && agent.skills.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-3">
                {agent.skills.slice(0, 3).map((s, i) => (
                  <span key={i} className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted text-muted-foreground">{s.name}</span>
                ))}
              </div>
            )}
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Download className="w-3 h-3" />
                {agent.download_count}
              </span>
              <Button size="sm" variant="outline" onClick={() => onClone(agent.id)} isLoading={isCloning === agent.id} className="opacity-0 group-hover:opacity-100 transition-opacity">
                <Download className="w-3.5 h-3.5 mr-1" /> Use Agent
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
