"use client";

import { useState } from "react";
import { Globe, Rocket, GitBranch, ExternalLink, Loader2, Check, Copy } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

interface DeployPanelProps {
  publishedUrl: string | null;
  deploymentStatus: string;
  isPublished: boolean;
  customDomain: string | null;
  onPublish: (data: { subdomain?: string; custom_domain?: string }) => void;
  onDeploy: (platform: string) => void;
  isPublishing: boolean;
  isDeploying: boolean;
  className?: string;
}

export function DeployPanel({
  publishedUrl,
  deploymentStatus,
  isPublished,
  customDomain,
  onPublish,
  onDeploy,
  isPublishing,
  isDeploying,
  className,
}: DeployPanelProps) {
  const [subdomain, setSubdomain] = useState("");
  const [customDom, setCustomDom] = useState("");
  const [copied, setCopied] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "deployed": return "success";
      case "building": return "warning";
      case "draft": return "default";
      default: return "outline";
    }
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <CardTitle className="text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Rocket className="w-4 h-4" />
            Deploy
          </div>
          <Badge variant={getStatusColor(deploymentStatus) as any}>
            {deploymentStatus}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {publishedUrl && (
          <div className="flex items-center justify-between p-2 rounded-lg bg-primary/5 border border-primary/20">
            <div className="flex items-center gap-2 min-w-0">
              <ExternalLink className="w-4 h-4 text-primary flex-shrink-0" />
              <span className="text-sm truncate">{publishedUrl}</span>
            </div>
            <button onClick={() => handleCopy(publishedUrl)} className="p-1 hover:bg-muted rounded flex-shrink-0">
              {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        )}

        <div>
          <label className="text-xs font-medium mb-1 block">Subdomain</label>
          <div className="flex items-center gap-2">
            <input
              value={subdomain}
              onChange={(e) => setSubdomain(e.target.value.replace(/[^a-z0-9-]/g, ""))}
              placeholder="my-site"
              className="flex-1 h-9 px-3 rounded-lg border border-input bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <span className="text-xs text-muted-foreground whitespace-nowrap">.omniai.app</span>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPublish({ subdomain })}
            isLoading={isPublishing}
            disabled={isPublishing || !subdomain}
            className="w-full mt-2"
          >
            <Globe className="w-4 h-4 mr-1.5" />
            Publish
          </Button>
        </div>

        <div>
          <label className="text-xs font-medium mb-1 block">Custom Domain</label>
          <input
            value={customDom}
            onChange={(e) => setCustomDom(e.target.value)}
            placeholder="example.com"
            className="w-full h-9 px-3 rounded-lg border border-input bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring mb-2"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPublish({ custom_domain: customDom })}
            isLoading={isPublishing}
            disabled={isPublishing || !customDom}
            className="w-full"
          >
            <Globe className="w-4 h-4 mr-1.5" />
            Connect Domain
          </Button>
        </div>

        <div className="border-t border-border pt-3">
          <label className="text-xs font-medium mb-2 block">Deploy to Platform</label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: "vercel", label: "Vercel", icon: "▲" },
              { id: "netlify", label: "Netlify", icon: "♮" },
              { id: "self-hosted", label: "Self", icon: "🖥" },
            ].map((platform) => (
              <button
                key={platform.id}
                onClick={() => onDeploy(platform.id)}
                disabled={isDeploying}
                className="flex flex-col items-center gap-1 p-3 rounded-lg border border-border hover:border-primary/50 hover:bg-muted/30 transition-all disabled:opacity-50"
              >
                <span className="text-lg">{platform.icon}</span>
                <span className="text-xs text-muted-foreground">{platform.label}</span>
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
