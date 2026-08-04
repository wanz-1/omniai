"use client";

import { useState } from "react";
import { Wrench, Plus, Trash2, ToggleLeft, ToggleRight, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

interface Tool {
  id?: string;
  name: string;
  tool_type: string;
  description?: string;
  config?: Record<string, any>;
  enabled: boolean;
}

interface AgentToolsConfigProps {
  tools: Tool[];
  onAdd: (tool: Tool) => void;
  onDelete: (id: string) => void;
  onToggle: (id: string) => void;
  className?: string;
}

const TOOL_TYPES = [
  { id: "web_search", label: "Web Search", icon: "🔍" },
  { id: "web_scrape", label: "Web Scraper", icon: "🌐" },
  { id: "document_read", label: "Document Reader", icon: "📄" },
  { id: "document_write", label: "Document Writer", icon: "✍️" },
  { id: "data_analysis", label: "Data Analysis", icon: "📊" },
  { id: "chart_creation", label: "Chart Creator", icon: "📈" },
  { id: "code_execution", label: "Code Runner", icon: "💻" },
  { id: "email", label: "Email", icon: "📧" },
  { id: "database", label: "Database", icon: "🗄️" },
  { id: "api_call", label: "API Calls", icon: "🔌" },
  { id: "file_system", label: "File System", icon: "📁" },
  { id: "image_generation", label: "Image Gen", icon: "🎨" },
  { id: "slack", label: "Slack", icon: "💬" },
  { id: "github", label: "GitHub", icon: "🐙" },
  { id: "google_drive", label: "Google Drive", icon: "☁️" },
  { id: "crm", label: "CRM", icon: "👥" },
  { id: "custom", label: "Custom API", icon: "⚙️" },
];

export function AgentToolsConfig({ tools, onAdd, onDelete, onToggle, className }: AgentToolsConfigProps) {
  const [showAdd, setShowAdd] = useState(false);
  const [selectedType, setSelectedType] = useState("web_search");

  const handleAdd = () => {
    const typeDef = TOOL_TYPES.find((t) => t.id === selectedType);
    onAdd({
      name: typeDef?.label || selectedType,
      tool_type: selectedType,
      description: `Enables ${typeDef?.label.toLowerCase() || selectedType} capabilities`,
      config: {},
      enabled: true,
    });
    setShowAdd(false);
  };

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium flex items-center gap-2">
          <Wrench className="w-4 h-4" />
          Tools ({tools.length})
        </h3>
        <Button variant="outline" size="sm" onClick={() => setShowAdd(!showAdd)}>
          <Plus className="w-3.5 h-3.5 mr-1" /> Add Tool
        </Button>
      </div>

      {showAdd && (
        <div className="p-3 rounded-lg border border-border bg-card space-y-2">
          <div className="grid grid-cols-3 gap-1 max-h-36 overflow-y-auto">
            {TOOL_TYPES.map((t) => (
              <button
                key={t.id}
                onClick={() => setSelectedType(t.id)}
                className={cn("flex flex-col items-center gap-0.5 p-1.5 rounded text-xs transition-colors", selectedType === t.id ? "bg-primary/10 text-primary" : "hover:bg-muted")}
              >
                <span className="text-base">{t.icon}</span>
                <span className="text-[10px]">{t.label}</span>
              </button>
            ))}
          </div>
          <Button size="sm" onClick={handleAdd} className="w-full">Add Selected Tool</Button>
        </div>
      )}

      <div className="space-y-1.5">
        {tools.length === 0 && !showAdd && (
          <p className="text-xs text-muted-foreground text-center py-4">No tools configured</p>
        )}
              {tools.map((tool) => {
          const typeDef = TOOL_TYPES.find((t) => t.id === tool.tool_type);
          return (
            <div key={tool.id || tool.tool_type} className="flex items-center gap-2 p-2 rounded-lg border border-border bg-card">
              <span className="text-base">{typeDef?.icon || "🔧"}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium">{typeDef?.label || tool.name}</span>
                  {tool.enabled ? (
                    <span className="text-[10px] px-1 py-0.5 rounded bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">Active</span>
                  ) : (
                    <span className="text-[10px] px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500">Disabled</span>
                  )}
                </div>
                <p className="text-[10px] text-muted-foreground mt-0.5">{tool.description}</p>
              </div>
              <button onClick={() => tool.id && onToggle(tool.id)} className="p-1 rounded hover:bg-muted transition-colors">
                {tool.enabled ? <ToggleRight className="w-4 h-4 text-primary" /> : <ToggleLeft className="w-4 h-4 text-muted-foreground" />}
              </button>
              {tool.id && (
                <button onClick={() => onDelete(tool.id!)} className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-muted-foreground hover:text-red-500">
                  <Trash2 className="w-3 h-3" />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
