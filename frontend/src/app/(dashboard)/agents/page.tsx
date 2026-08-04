"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, Plus, Loader2, Sparkles, Store, Search } from "lucide-react";
import { agentsApi } from "@/lib/api-client";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { AgentCard } from "@/modules/agents/AgentCard";
import { cn } from "@/lib/utils";

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    setIsLoading(true);
    try {
      const res = await agentsApi.list();
      setAgents(res.data);
    } catch {
      toast.error("Failed to load agents");
    } finally {
      setIsLoading(false);
    }
  };

  const filtered = agents.filter((a) =>
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    a.role.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bot className="w-6 h-6" />
            AI Agents
          </h1>
          <p className="text-muted-foreground mt-1">Build and manage your AI workforce</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => router.push("/agents/marketplace")}>
            <Store className="w-4 h-4 mr-1.5" />
            Marketplace
          </Button>
          <Button onClick={() => router.push("/agents/new")}>
            <Plus className="w-4 h-4 mr-1.5" />
            Create Agent
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[40vh] text-center">
          <Bot className="w-16 h-16 text-primary/30 mb-4" />
          <h3 className="text-lg font-medium">No agents yet</h3>
          <p className="text-sm text-muted-foreground mt-1 mb-4 max-w-md">
            Create your first AI agent or import one from the marketplace
          </p>
          <div className="flex gap-3">
            <Button onClick={() => router.push("/agents/new")}>
              <Sparkles className="w-4 h-4 mr-1.5" />
              Create Agent
            </Button>
            <Button variant="outline" onClick={() => router.push("/agents/marketplace")}>
              <Store className="w-4 h-4 mr-1.5" />
              Browse Marketplace
            </Button>
          </div>
        </div>
      ) : (
        <>
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search agents..." className="w-full pl-9 pr-3 py-2 rounded-lg border border-border bg-background text-sm" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((agent) => (
              <AgentCard key={agent.id} agent={agent} onSelect={(id) => router.push(`/agents/${id}`)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
