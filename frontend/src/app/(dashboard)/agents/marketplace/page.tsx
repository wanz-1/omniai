"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { agentsApi } from "@/lib/api-client";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { AgentMarketplace } from "@/modules/agents/AgentMarketplace";

export default function MarketplacePage() {
  const router = useRouter();
  const [agents, setAgents] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCloning, setIsCloning] = useState<string | null>(null);

  useEffect(() => {
    loadMarketplace();
  }, []);

  const loadMarketplace = async () => {
    setIsLoading(true);
    try {
      const res = await agentsApi.marketplace();
      // If empty, show templates as fallback
      if (res.data.length === 0) {
        const templatesRes = await agentsApi.templates();
        setAgents(templatesRes.data);
      } else {
        setAgents(res.data);
      }
    } catch {
      toast.error("Failed to load marketplace");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClone = async (agentId: string) => {
    setIsCloning(agentId);
    try {
      const res = await agentsApi.clone(agentId);
      toast.success("Agent cloned!");
      router.push(`/agents/${res.data.id}`);
    } catch {
      toast.error("Failed to clone agent");
    } finally {
      setIsCloning(null);
    }
  };

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-[60vh]"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;
  }

  return (
    <AgentMarketplace
      agents={agents}
      onClone={handleClone}
      isCloning={isCloning}
    />
  );
}
