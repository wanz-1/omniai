"use client";

import { Sparkles, Download, ArrowRight, Bot, DollarSign, Users, Search, FileText, Target, ShoppingCart } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

interface TemplateAgent {
  id: string;
  name: string;
  role: string;
  description: string;
  icon: string;
  color: string;
  skills: string[];
  category: string;
}

const PRE_BUILT_AGENTS: TemplateAgent[] = [
  { id: "finance", name: "Finance Agent", role: "Financial Analyst & Budget Manager", description: "Manages budgets, analyzes expenses, prepares financial reports, provides recommendations, and handles NGO financial management.", icon: "💰", color: "#10B981", skills: ["Budget Preparation", "Forecasting", "Expense Analysis", "Financial Reports", "Invoice Review", "NGO Finance"], category: "finance" },
  { id: "hr", name: "HR Agent", role: "Human Resources Assistant", description: "Screens CVs, schedules interviews, answers employee FAQs, assists with policy documentation, and supports training programs.", icon: "👥", color: "#8B5CF6", skills: ["CV Screening", "Interview Scheduling", "Employee FAQs", "Policy Assistance", "Training Support"], category: "hr" },
  { id: "research", name: "Research Agent", role: "Research Analyst", description: "Conducts internet research, writes reports, collects data, performs literature reviews, and generates summaries.", icon: "🔬", color: "#06B6D4", skills: ["Internet Research", "Report Writing", "Data Collection", "Literature Review", "Summaries"], category: "research" },
  { id: "marketing", name: "Marketing Agent", role: "Marketing Campaign Manager", description: "Creates content, plans campaigns, manages social media posts, analyzes markets, and optimizes marketing strategies.", icon: "📈", color: "#F59E0B", skills: ["Content Creation", "Campaign Planning", "Social Media", "Market Analysis", "SEO"], category: "marketing" },
  { id: "project_manager", name: "Project Manager Agent", role: "Project Coordinator", description: "Tracks tasks, plans projects, generates progress reports, coordinates teams, and manages deadlines.", icon: "🎯", color: "#2563EB", skills: ["Task Tracking", "Project Planning", "Progress Reports", "Team Coordination", "Risk Management"], category: "project_management" },
  { id: "procurement", name: "Procurement Agent", role: "Procurement & Supply Chain Manager", description: "Compares suppliers, processes purchase requests, plans procurement, and manages inventory.", icon: "📦", color: "#EC4899", skills: ["Supplier Comparison", "Purchase Requests", "Procurement Planning", "Inventory Support", "Vendor Management"], category: "procurement" },
];

interface PreBuiltAgentsProps {
  onSelect: (agent: TemplateAgent) => void;
  className?: string;
}

export function PreBuiltAgents({ onSelect, className }: PreBuiltAgentsProps) {
  return (
    <div className={cn("space-y-4", className)}>
      <div className="text-center mb-6">
        <h2 className="text-xl font-bold">Pre-Built AI Agents</h2>
        <p className="text-sm text-muted-foreground mt-1">Choose a ready-made agent template and customize it</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {PRE_BUILT_AGENTS.map((agent) => (
          <div key={agent.id} className="group relative p-5 rounded-2xl border border-border bg-card hover:shadow-lg hover:border-primary/30 transition-all duration-200">
            <div className="flex items-start gap-3 mb-3">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" style={{ backgroundColor: agent.color + "20" }}>
                <span>{agent.icon}</span>
              </div>
              <div>
                <h3 className="font-semibold">{agent.name}</h3>
                <p className="text-xs text-muted-foreground">{agent.role}</p>
              </div>
            </div>

            <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{agent.description}</p>

            <div className="flex flex-wrap gap-1 mb-4">
              {agent.skills.slice(0, 4).map((s, i) => (
                <span key={i} className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted text-muted-foreground">{s}</span>
              ))}
              {agent.skills.length > 4 && <span className="text-[10px] text-muted-foreground">+{agent.skills.length - 4}</span>}
            </div>

            <Button size="sm" onClick={() => onSelect(agent)} className="w-full opacity-0 group-hover:opacity-100 transition-opacity">
              <Download className="w-3.5 h-3.5 mr-1" /> Use This Template
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
