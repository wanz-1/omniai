"use client";

import { useState } from "react";
import { Plus, Trash2, Star, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

interface Skill {
  id?: string;
  name: string;
  description?: string;
  category?: string;
  proficiency: number;
}

interface AgentSkillsEditorProps {
  skills: Skill[];
  onAdd: (skill: Skill) => void;
  onDelete: (id: string) => void;
  className?: string;
}

const SKILL_CATEGORIES = [
  "Analysis", "Communication", "Creative", "Data", "Finance",
  "HR", "Legal", "Marketing", "Research", "Technical", "Management",
];

export function AgentSkillsEditor({ skills, onAdd, onDelete, className }: AgentSkillsEditorProps) {
  const [showAdd, setShowAdd] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [proficiency, setProficiency] = useState(5);

  const handleAdd = () => {
    if (!name.trim()) return;
    onAdd({ name: name.trim(), description: description.trim() || undefined, category: category || undefined, proficiency });
    setName("");
    setDescription("");
    setCategory("");
    setProficiency(5);
    setShowAdd(false);
  };

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium flex items-center gap-2">
          <BookOpen className="w-4 h-4" />
          Skills ({skills.length})
        </h3>
        <Button variant="outline" size="sm" onClick={() => setShowAdd(!showAdd)}>
          <Plus className="w-3.5 h-3.5 mr-1" /> Add Skill
        </Button>
      </div>

      {showAdd && (
        <div className="p-3 rounded-lg border border-border bg-card space-y-2">
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Skill name" className="w-full px-2 py-1.5 rounded border border-border bg-background text-xs" />
          <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description (optional)" className="w-full px-2 py-1.5 rounded border border-border bg-background text-xs" />
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full px-2 py-1.5 rounded border border-border bg-background text-xs">
            <option value="">No category</option>
            {SKILL_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <div>
            <label className="text-xs text-muted-foreground">Proficiency: {proficiency}/10</label>
            <input type="range" min="1" max="10" value={proficiency} onChange={(e) => setProficiency(parseInt(e.target.value))} className="w-full accent-primary" />
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={handleAdd} disabled={!name.trim()} className="flex-1">Add</Button>
            <Button variant="ghost" size="sm" onClick={() => setShowAdd(false)}>Cancel</Button>
          </div>
        </div>
      )}

      <div className="space-y-1.5">
        {skills.length === 0 && !showAdd && (
          <p className="text-xs text-muted-foreground text-center py-4">No skills defined yet</p>
        )}
        {skills.map((skill) => (
          <div key={skill.id || skill.name} className="flex items-center gap-2 p-2 rounded-lg border border-border bg-card">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium">{skill.name}</span>
                {skill.category && <span className="text-[10px] px-1 py-0.5 rounded bg-muted text-muted-foreground">{skill.category}</span>}
              </div>
              {skill.description && <p className="text-[10px] text-muted-foreground mt-0.5">{skill.description}</p>}
              <div className="flex items-center gap-0.5 mt-1">
                {Array.from({ length: 10 }).map((_, i) => (
                  <Star key={i} className={cn("w-2.5 h-2.5", i < skill.proficiency ? "text-amber-400 fill-amber-400" : "text-muted-foreground/30")} />
                ))}
              </div>
            </div>
            {skill.id && (
              <button onClick={() => onDelete(skill.id!)} className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-muted-foreground hover:text-red-500">
                <Trash2 className="w-3 h-3" />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
