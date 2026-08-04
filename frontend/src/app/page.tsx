"use client";

import { useAuth } from "@/hooks/useAuth";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { FileText, Globe, Bot, MessageSquare, Code, ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";

const quickActions = [
  { href: "/documents", icon: FileText, label: "Humanize Document", color: "from-blue-500 to-blue-600" },
  { href: "/websites", icon: Globe, label: "Build Website", color: "from-purple-500 to-purple-600" },
  { href: "/bots", icon: Bot, label: "Create Bot", color: "from-green-500 to-green-600" },
  { href: "/chat", icon: MessageSquare, label: "AI Chat", color: "from-cyan-500 to-cyan-600" },
  { href: "/code", icon: Code, label: "Generate Code", color: "from-orange-500 to-orange-600" },
];

const statsCards = [
  { label: "Documents", value: "0", icon: FileText },
  { label: "Websites", value: "0", icon: Globe },
  { label: "Bots", value: "0", icon: Bot },
  { label: "Credits", value: "0", icon: Sparkles },
];

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <DashboardShell>
      <div className="space-y-8 animate-fade-in">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Welcome back, {user?.display_name || "User"}. Here is your overview.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {statsCards.map((stat) => (
            <Card key={stat.label}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                    <p className="text-3xl font-bold mt-1">{stat.value}</p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                    <stat.icon className="w-6 h-6 text-primary" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {quickActions.map((action) => (
              <Link key={action.href} href={action.href}>
                <Card className="card-hover cursor-pointer group">
                  <CardContent className="p-6">
                    <div
                      className={`w-12 h-12 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center mb-4`}
                    >
                      <action.icon className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="font-medium">{action.label}</h3>
                    <p className="text-sm text-muted-foreground mt-1 flex items-center group-hover:text-primary transition-colors">
                      Get started <ArrowRight className="w-3 h-3 ml-1" />
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { step: "1", title: "Humanize a document", desc: "Upload any document and let AI make it sound natural." },
                { step: "2", title: "Build a website", desc: "Describe your ideal website and watch AI build it." },
                { step: "3", title: "Create a chatbot", desc: "Build an AI bot for your business in minutes." },
                { step: "4", title: "Generate code", desc: "Describe what you want and get production-ready code." },
              ].map((item) => (
                <div key={item.step} className="flex items-start space-x-4">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-bold text-primary">{item.step}</span>
                  </div>
                  <div>
                    <h4 className="font-medium">{item.title}</h4>
                    <p className="text-sm text-muted-foreground">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
