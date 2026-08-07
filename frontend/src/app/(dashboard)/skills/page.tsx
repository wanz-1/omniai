"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, Award, BookOpen, Filter, Plus, Loader2, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { toast } from "sonner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface Skill {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  levels: Record<string, string>;
  prerequisites: string[];
  tools: string[];
  tags: string[];
}

const CATEGORY_COLORS: Record<string, string> = {
  technical: "bg-blue-500/10 text-blue-600 border-blue-200",
  cognitive: "bg-purple-500/10 text-purple-600 border-purple-200",
  creative: "bg-pink-500/10 text-pink-600 border-pink-200",
  interpersonal: "bg-green-500/10 text-green-600 border-green-200",
  domain: "bg-orange-500/10 text-orange-600 border-orange-200",
  automation: "bg-yellow-500/10 text-yellow-600 border-yellow-200",
  analysis: "bg-cyan-500/10 text-cyan-600 border-cyan-200",
  communication: "bg-indigo-500/10 text-indigo-600 border-indigo-200",
};

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [filtered, setFiltered] = useState<Skill[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState<string[]>([]);

  const loadSkills = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_BASE}/skills/library`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      setSkills(data.skills || []);
      setFiltered(data.skills || []);
      setCategories(data.categories || []);
    } catch {
      // Fallback to local library if API not available (dev)
      try {
        const mod = await import("@/lib/api-client");
        // Use backend service file directly as fallback? For now show empty
        toast.error("Could not load skills from backend, using local fallback");
        // Fallback minimal
        setSkills([]);
        setFiltered([]);
      } catch {
        toast.error("Failed to load skills");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSkills();
  }, [loadSkills]);

  useEffect(() => {
    let result = skills;
    if (category !== "all") {
      result = result.filter((s) => s.category === category);
    }
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q) ||
          s.tags.some((t) => t.toLowerCase().includes(q))
      );
    }
    setFiltered(result);
  }, [search, category, skills]);

  const levelDescription = (skill: Skill, level: number) => {
    return skill.levels?.[String(level)] || skill.levels?.[String(Math.min(level, 10))] || `${level}/10`;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Award className="w-6 h-6 text-yellow-500" />
            Skill Library
          </h1>
          <p className="text-muted-foreground mt-1">
            60+ production skills for AI agents — technical, cognitive, creative, domain
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          {skills.length} skills
        </Badge>
      </div>

      <div className="flex flex-col md:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search skills, e.g. Python, SEO, leadership..."
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-border bg-background text-sm"
          />
        </div>
        <div className="flex items-center gap-2 overflow-x-auto">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <button
            onClick={() => setCategory("all")}
            className={`px-3 py-1 rounded-full text-xs border whitespace-nowrap ${
              category === "all" ? "bg-primary text-primary-foreground" : "bg-muted"
            }`}
          >
            All
          </button>
          {["technical", "cognitive", "creative", "interpersonal", "domain", "automation", "analysis", "communication"].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-3 py-1 rounded-full text-xs border capitalize whitespace-nowrap ${
                category === cat ? "bg-primary text-primary-foreground" : "bg-muted/50 hover:bg-muted"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((skill) => (
            <Card key={skill.id} className="hover:shadow-lg transition-shadow group">
              <CardContent className="p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl group-hover:scale-110 transition-transform">{skill.icon}</span>
                    <div>
                      <div className="font-medium text-sm">{skill.name}</div>
                      <div className="text-[10px] text-muted-foreground">{skill.id}</div>
                    </div>
                  </div>
                  <Badge className={`text-[10px] border ${CATEGORY_COLORS[skill.category] || ""}`}>
                    {skill.category}
                  </Badge>
                </div>

                <p className="text-xs text-muted-foreground line-clamp-2">{skill.description}</p>

                <div className="space-y-1">
                  <div className="text-[11px] font-medium flex items-center gap-1">
                    <BookOpen className="w-3 h-3" />
                    Levels
                  </div>
                  <div className="text-[11px] text-muted-foreground space-y-0.5">
                    <div>
                      <span className="font-medium">1:</span> {levelDescription(skill, 1)}
                    </div>
                    <div>
                      <span className="font-medium">5:</span> {levelDescription(skill, 5)}
                    </div>
                    <div>
                      <span className="font-medium">10:</span> {levelDescription(skill, 10)}
                    </div>
                  </div>
                </div>

                {skill.prerequisites.length > 0 && (
                  <div className="text-[11px]">
                    <span className="text-muted-foreground">Prereq:</span>{" "}
                    <span className="font-mono text-xs">{skill.prerequisites.join(", ")}</span>
                  </div>
                )}

                <div className="flex flex-wrap gap-1">
                  {skill.tools.slice(0, 3).map((t) => (
                    <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-muted">
                      {t}
                    </span>
                  ))}
                  {skill.tools.length > 3 && (
                    <span className="text-[10px] text-muted-foreground">+{skill.tools.length - 3}</span>
                  )}
                </div>

                <div className="flex flex-wrap gap-1">
                  {skill.tags.slice(0, 4).map((tag) => (
                    <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
                      #{tag}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {filtered.length === 0 && !loading && (
        <Card className="p-8 text-center">
          <Sparkles className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
          <h3 className="font-medium">No skills found</h3>
          <p className="text-sm text-muted-foreground">Try different search or category</p>
        </Card>
      )}

      <Card className="bg-gradient-to-br from-yellow-500/5 to-orange-500/5 border-yellow-200">
        <CardContent className="p-4 text-sm">
          <h4 className="font-medium flex items-center gap-2">
            <Award className="w-4 h-4" />
            How skills work for Active Agents
          </h4>
          <ul className="list-disc list-inside text-muted-foreground mt-2 space-y-1 text-xs">
            <li>Each active agent has skills with proficiency 1-10</li>
            <li>Completing tasks grants XP → chance to level up (lower level = faster)</li>
            <li>Missing prerequisites are suggested when adding new skill</li>
            <li>Use <code className="bg-muted px-1 rounded">/skills/active-agent/{"{id}"}</code> to manage skills via API</li>
            <li>Auto-learn analyzes goals & tasks and suggests top skills</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
