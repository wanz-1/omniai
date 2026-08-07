"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  FileText,
  Globe,
  Bot,
  MessageSquare,
  Code,
  LayoutDashboard,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Mic,
  Layers,
  Network,
  Store,
  Building,
  Cloud,
  Zap,
  Brain,
  Activity,
  Shield,
  PlayCircle,
  Award,
} from "lucide-react";

const navItems: Array<{
  href: string;
  icon: any;
  label: string;
  badge?: string;
}> = [
  { href: "/", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/documents", icon: FileText, label: "Documents" },
  { href: "/websites", icon: Globe, label: "Websites" },
  { href: "/bots", icon: Bot, label: "Bots" },
  { href: "/chat", icon: MessageSquare, label: "AI Chat" },
  { href: "/multimodal", icon: Layers, label: "Multimodal" },
  { href: "/agents", icon: Mic, label: "Agents" },
  { href: "/active-agents", icon: PlayCircle, label: "Active Agents", badge: "NEW" },
  { href: "/skills", icon: Award, label: "Skills", badge: "NEW" },
  { href: "/agent-network", icon: Network, label: "Agent Network" },
  { href: "/code-studio", icon: Code, label: "Code Studio" },
  { href: "/marketplace", icon: Store, label: "Marketplace" },
  { href: "/industry", icon: Building, label: "Industry" },
  { href: "/infrastructure", icon: Cloud, label: "Infrastructure" },
  { href: "/v3", icon: Zap, label: "V3 Ecosystem" },
  { href: "/v4", icon: Sparkles, label: "V4 Enterprise" },
  { href: "/v5", icon: Brain, label: "V5 Knowledge" },
  { href: "/governance", icon: Shield, label: "Governance" },
  { href: "/status", icon: Activity, label: "Status" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen bg-card border-r border-border transition-all duration-300 flex flex-col",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex items-center h-16 px-4 border-b border-border">
        <Link href="/" className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary via-secondary to-accent flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <span className="font-bold text-lg gradient-text">OmniAI</span>
          )}
        </Link>
      </div>

      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center rounded-lg transition-all duration-200 relative",
                collapsed ? "justify-center p-3" : "px-3 py-2.5 space-x-3",
                isActive
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed ? (
                <span className="flex-1 flex items-center justify-between">
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-500 text-white font-bold">
                      {item.badge}
                    </span>
                  )}
                </span>
              ) : (
                item.badge && (
                  <span className="absolute top-1 right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                )
              )}
            </Link>
          );
        })}
      </nav>

      <div className="p-2 border-t border-border">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-muted text-muted-foreground transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
}
