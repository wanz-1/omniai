"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

const FONTS = [
  "Inter", "Roboto", "Poppins", "Open Sans", "Playfair Display",
  "Montserrat", "Lato", "Nunito", "Merriweather", "Space Grotesk",
];

const PRESET_PALETTES = [
  { name: "Ocean", colors: ["#2563EB", "#7C3AED", "#06B6D4", "#F8FAFC"] },
  { name: "Forest", colors: ["#059669", "#10B981", "#34D399", "#F8FAFC"] },
  { name: "Sunset", colors: ["#DC2626", "#F59E0B", "#F97316", "#F8FAFC"] },
  { name: "Midnight", colors: ["#1E293B", "#334155", "#475569", "#F8FAFC"] },
  { name: "Rose", colors: ["#E11D48", "#F43F5E", "#FB7185", "#FFF1F2"] },
  { name: "Purple", colors: ["#7C3AED", "#8B5CF6", "#A78BFA", "#F8FAFC"] },
];

interface ThemeCustomizerProps {
  theme: {
    primary_color?: string;
    secondary_color?: string;
    accent_color?: string;
    font?: string;
    dark_mode?: boolean;
  };
  onChange: (theme: any) => void;
  className?: string;
}

export function ThemeCustomizer({ theme, onChange, className }: ThemeCustomizerProps) {
  const [localTheme, setLocalTheme] = useState(theme);

  const update = (key: string, value: any) => {
    const next = { ...localTheme, [key]: value };
    setLocalTheme(next);
    onChange(next);
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <CardTitle className="text-sm">Theme</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-xs font-medium mb-2 block">Color Palette</label>
          <div className="grid grid-cols-3 gap-2">
            {PRESET_PALETTES.map((palette) => (
              <button
                key={palette.name}
                onClick={() => {
                  update("primary_color", palette.colors[0]);
                  update("secondary_color", palette.colors[1]);
                  update("accent_color", palette.colors[2]);
                }}
                className="p-2 rounded-lg border border-border hover:border-primary/50 transition-colors"
              >
                <div className="flex gap-0.5 mb-1">
                  {palette.colors.slice(0, 3).map((c, i) => (
                    <div key={i} className="flex-1 h-4 rounded-sm" style={{ background: c }} />
                  ))}
                </div>
                <span className="text-[10px] text-muted-foreground">{palette.name}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium mb-1 block">Primary</label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={localTheme.primary_color || "#2563EB"}
                onChange={(e) => update("primary_color", e.target.value)}
                className="w-8 h-8 rounded cursor-pointer border border-input"
              />
              <span className="text-xs text-muted-foreground font-mono">
                {localTheme.primary_color}
              </span>
            </div>
          </div>
          <div>
            <label className="text-xs font-medium mb-1 block">Secondary</label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={localTheme.secondary_color || "#7C3AED"}
                onChange={(e) => update("secondary_color", e.target.value)}
                className="w-8 h-8 rounded cursor-pointer border border-input"
              />
              <span className="text-xs text-muted-foreground font-mono">
                {localTheme.secondary_color}
              </span>
            </div>
          </div>
          <div>
            <label className="text-xs font-medium mb-1 block">Accent</label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={localTheme.accent_color || "#06B6D4"}
                onChange={(e) => update("accent_color", e.target.value)}
                className="w-8 h-8 rounded cursor-pointer border border-input"
              />
              <span className="text-xs text-muted-foreground font-mono">
                {localTheme.accent_color}
              </span>
            </div>
          </div>
        </div>

        <div>
          <label className="text-xs font-medium mb-1 block">Font</label>
          <select
            value={localTheme.font || "Inter"}
            onChange={(e) => update("font", e.target.value)}
            className="w-full h-9 rounded-lg border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {FONTS.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={localTheme.dark_mode || false}
            onChange={(e) => update("dark_mode", e.target.checked)}
            className="rounded border-border"
          />
          <span className="text-sm">Dark Mode</span>
        </label>
      </CardContent>
    </Card>
  );
}
