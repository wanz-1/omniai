"use client";

import { useState } from "react";
import { Plus, GripVertical, Trash2, ChevronDown, ChevronRight, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

const SECTION_TYPES = [
  { id: "hero", label: "Hero", icon: "H" },
  { id: "features", label: "Features", icon: "F" },
  { id: "about", label: "About", icon: "A" },
  { id: "contact", label: "Contact", icon: "C" },
  { id: "cta", label: "CTA", icon: "→" },
  { id: "stats", label: "Stats", icon: "Σ" },
  { id: "team", label: "Team", icon: "T" },
  { id: "testimonials", label: "Testimonials", icon: "💬" },
  { id: "pricing", label: "Pricing", icon: "$" },
  { id: "faq", label: "FAQ", icon: "?" },
  { id: "gallery", label: "Gallery", icon: "G" },
  { id: "blog", label: "Blog", icon: "B" },
];

interface Page {
  slug: string;
  title: string;
  sections: any[];
}

interface WebsiteEditorProps {
  pages: Page[];
  activePage: string;
  onPageChange: (slug: string) => void;
  onPagesChange: (pages: Page[]) => void;
  onAddPage: () => void;
  onAddSection: (pageSlug: string, sectionType: string) => void;
  onRemoveSection: (pageSlug: string, sectionIndex: number) => void;
  onMoveSection: (pageSlug: string, fromIndex: number, toIndex: number) => void;
  className?: string;
}

export function WebsiteEditor({
  pages,
  activePage,
  onPageChange,
  onPagesChange,
  onAddPage,
  onAddSection,
  onRemoveSection,
  onMoveSection,
  className,
}: WebsiteEditorProps) {
  const activePageData = pages.find((p) => p.slug === activePage);
  const [showAddSection, setShowAddSection] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState<Set<number>>(new Set());

  const toggleCollapse = (idx: number) => {
    const next = new Set(collapsedSections);
    if (next.has(idx)) next.delete(idx);
    else next.add(idx);
    setCollapsedSections(next);
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex items-center gap-1 p-2 border-b border-border bg-muted/20 overflow-x-auto shrink-0">
        {pages.map((page) => (
          <button
            key={page.slug}
            onClick={() => onPageChange(page.slug)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors",
              activePage === page.slug
                ? "bg-primary/10 text-primary font-medium"
                : "text-muted-foreground hover:bg-muted"
            )}
          >
            <FileText className="w-3.5 h-3.5" />
            {page.title}
          </button>
        ))}
        <button
          onClick={onAddPage}
          className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground"
          title="Add page"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {activePageData?.sections.map((section, idx) => (
          <div
            key={idx}
            className="rounded-lg border border-border bg-card overflow-hidden group"
          >
            <div className="flex items-center gap-2 px-3 py-2 bg-muted/20 border-b border-border">
              <GripVertical className="w-3.5 h-3.5 text-muted-foreground cursor-grab opacity-0 group-hover:opacity-100 transition-opacity" />
              <button onClick={() => toggleCollapse(idx)} className="p-0.5">
                {collapsedSections.has(idx) ? (
                  <ChevronRight className="w-3.5 h-3.5" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5" />
                )}
              </button>
              <span className="text-xs font-medium px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                {section.type}
              </span>
              <div className="flex-1" />
              <button
                onClick={() => onRemoveSection(activePage, idx)}
                className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-muted-foreground hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
            {!collapsedSections.has(idx) && (
              <div className="p-3 text-xs text-muted-foreground space-y-2">
                {Object.entries(section.content || {}).map(([key, val]) => (
                  <div key={key} className="flex items-start gap-2">
                    <span className="font-medium text-foreground w-24 flex-shrink-0">{key}:</span>
                    <span className="truncate">
                      {typeof val === "string"
                        ? val
                        : Array.isArray(val)
                          ? `${val.length} items`
                          : JSON.stringify(val).slice(0, 80)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        <div className="relative">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAddSection(!showAddSection)}
            className="w-full"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            Add Section
          </Button>

          {showAddSection && (
            <div className="absolute top-full left-0 right-0 mt-1 p-2 bg-card border border-border rounded-lg shadow-lg z-10 grid grid-cols-3 gap-1 max-h-48 overflow-y-auto">
              {SECTION_TYPES.map((st) => (
                <button
                  key={st.id}
                  onClick={() => {
                    onAddSection(activePage, st.id);
                    setShowAddSection(false);
                  }}
                  className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-muted text-xs transition-colors"
                >
                  <span className="text-base">{st.icon}</span>
                  <span className="text-[10px] text-muted-foreground">{st.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
