"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Save,
  Settings,
  MessageSquare,
  Bot,
  BookOpen,
  BarChart3,
  Code,
  Loader2,
  Play,
  Globe,
  Eye,
} from "lucide-react";
import { botsApi } from "@/lib/api-client";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { BotSettingsEditor } from "@/modules/bots/BotSettingsEditor";
import { BotTestConsole } from "@/modules/bots/BotTestConsole";
import { KnowledgeBasePanel } from "@/modules/bots/KnowledgeBasePanel";
import { ConversationList } from "@/modules/bots/ConversationList";
import { AnalyticsPanel } from "@/modules/bots/AnalyticsPanel";
import { BotEmbedPanel } from "@/modules/bots/BotEmbedPanel";

type TabId = "settings" | "test" | "knowledge" | "conversations" | "analytics" | "embed";

interface BotData {
  id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  model: string;
  temperature: number;
  industry?: string;
  tone?: string;
  is_active: boolean;
  deployment_url?: string;
  knowledge_base_config?: {
    files?: string[];
    urls?: string[];
    text?: string;
  };
  widget_config?: any;
}

export default function BotWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const botId = params.id as string;

  const [bot, setBot] = useState<BotData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTraining, setIsTraining] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>("settings");
  const [knowledgeSources, setKnowledgeSources] = useState<any[]>([]);

  useEffect(() => {
    if (!botId) return;
    const loadBot = async () => {
      setIsLoading(true);
      try {
        const res = await botsApi.get(botId);
        setBot(res.data);
      } catch {
        toast.error("Failed to load bot");
        router.push("/bots");
      } finally {
        setIsLoading(false);
      }
    };
    loadBot();
  }, [botId, router]);

  useEffect(() => {
    if (bot?.knowledge_base_config?.text) {
      const textSource = {
        id: "kb-text",
        type: "text" as const,
        name: "Knowledge Base Text",
        content: bot.knowledge_base_config.text,
        addedAt: new Date().toISOString(),
      };
      const fileSources = (bot.knowledge_base_config.files || []).map((f: string, i: number) => ({
        id: `kb-file-${i}`,
        type: "file" as const,
        name: f,
        content: f,
        addedAt: new Date().toISOString(),
      }));
      const urlSources = (bot.knowledge_base_config.urls || []).map((u: string, i: number) => ({
        id: `kb-url-${i}`,
        type: "url" as const,
        name: u,
        content: u,
        addedAt: new Date().toISOString(),
      }));
      setKnowledgeSources([...fileSources, ...urlSources, textSource]);
    }
  }, [bot?.knowledge_base_config]);

  const loadBot = async () => {
    setIsLoading(true);
    try {
      const res = await botsApi.get(botId);
      setBot(res.data);
    } catch {
      toast.error("Failed to load bot");
      router.push("/bots");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!bot) return;
    setIsSaving(true);
    try {
      await botsApi.update(bot.id, {
        name: bot.name,
        description: bot.description,
        system_prompt: bot.system_prompt,
        model: bot.model,
        temperature: bot.temperature,
        industry: bot.industry,
        tone: bot.tone,
      });
      toast.success("Settings saved");
    } catch {
      toast.error("Save failed");
    } finally {
      setIsSaving(false);
    }
  };

  const handleTrain = async () => {
    if (!bot) return;
    setIsTraining(true);
    try {
      const files = knowledgeSources.filter((s: any) => s.type === "file").map((s: any) => s.name);
      const urls = knowledgeSources.filter((s: any) => s.type === "url").map((s: any) => s.content);
      const textSources = knowledgeSources.filter((s: any) => s.type === "text").map((s: any) => s.content);
      await botsApi.train(bot.id, { files, urls, text: textSources.join("\n\n") });
      toast.success("Training started!");
    } catch {
      toast.error("Training failed");
    } finally {
      setIsTraining(false);
    }
  };

  const handleDeploy = async () => {
    if (!bot) return;
    setIsDeploying(true);
    try {
      const res = await botsApi.deploy(bot.id, { channels: ["web"] });
      setBot({ ...bot, deployment_url: res.data.deployment_url, is_active: true });
      toast.success("Bot deployed!");
    } catch {
      toast.error("Deploy failed");
    } finally {
      setIsDeploying(false);
    }
  };

  const tabs = [
    { id: "settings" as const, label: "Settings", icon: Settings },
    { id: "test" as const, label: "Test", icon: Play },
    { id: "knowledge" as const, label: "Knowledge", icon: BookOpen },
    { id: "conversations" as const, label: "Chats", icon: MessageSquare },
    { id: "analytics" as const, label: "Analytics", icon: BarChart3 },
    { id: "embed" as const, label: "Embed", icon: Code },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!bot) return null;

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col animate-fade-in">
      <header className="flex items-center justify-between px-4 py-2 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/bots")} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <input
            value={bot.name}
            onChange={(e) => setBot({ ...bot, name: e.target.value })}
            className="text-lg font-semibold bg-transparent border-none outline-none focus-visible:ring-0 px-1"
          />
          <Badge variant={bot.is_active ? "success" : "default"}>
            {bot.is_active ? "Active" : "Draft"}
          </Badge>
          <Badge variant="outline">{bot.model}</Badge>
        </div>
        <div className="flex items-center gap-2">
          {bot.deployment_url && (
            <Button variant="ghost" size="sm" onClick={() => window.open(bot.deployment_url, "_blank")}>
              <Eye className="w-4 h-4 mr-1.5" />
              View Live
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleDeploy}
            isLoading={isDeploying}
          >
            <Globe className="w-4 h-4 mr-1.5" />
            Deploy
          </Button>
          <Button size="sm" onClick={handleSave} isLoading={isSaving}>
            <Save className="w-4 h-4 mr-1.5" />
            Save
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex flex-col border-r border-border bg-card w-56 shrink-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2.5 px-4 py-3 text-sm transition-colors text-left ${
                activeTab === tab.id
                  ? "bg-primary/5 text-primary border-r-2 border-primary font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-hidden">
          {activeTab === "settings" && (
            <div className="p-6 overflow-y-auto h-full max-w-2xl">
              <BotSettingsEditor
                bot={bot}
                onUpdate={(data) => setBot(data)}
                onSave={handleSave}
                isSaving={isSaving}
              />
            </div>
          )}

          {activeTab === "test" && (
            <BotTestConsole botId={bot.id} className="h-full" />
          )}

          {activeTab === "knowledge" && (
            <div className="h-full max-w-md mx-auto">
              <KnowledgeBasePanel
                sources={knowledgeSources}
                onSourcesChange={setKnowledgeSources}
                onTrain={handleTrain}
                isTraining={isTraining}
              />
            </div>
          )}

          {activeTab === "conversations" && (
            <ConversationList botId={bot.id} className="h-full" />
          )}

          {activeTab === "analytics" && (
            <div className="p-6 overflow-y-auto h-full max-w-3xl">
              <AnalyticsPanel botId={bot.id} />
            </div>
          )}

          {activeTab === "embed" && (
            <div className="p-6 overflow-y-auto h-full max-w-2xl">
              <BotEmbedPanel
                botId={bot.id}
                botName={bot.name}
                embedCode={undefined}
                widgetConfig={bot.widget_config}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
