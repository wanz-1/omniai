"use client";

import { useState } from "react";
import { Search, Eye } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

interface SEOData {
  title?: string;
  description?: string;
  keywords?: string;
  og_title?: string;
  og_description?: string;
  og_image?: string;
  canonical_url?: string;
}

interface SEOEditorProps {
  seo: SEOData;
  onChange: (seo: SEOData) => void;
  siteName: string;
  className?: string;
}

export function SEOEditor({ seo, onChange, siteName, className }: SEOEditorProps) {
  const [preview, setPreview] = useState(false);

  const update = (key: string, value: string) => {
    onChange({ ...seo, [key]: value });
  };

  const previewTitle = seo.title || siteName;
  const previewDesc = seo.description || "";
  const previewUrl = `https://${siteName.toLowerCase().replace(/\s+/g, "-")}.com`;

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <CardTitle className="text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4" />
            SEO
          </div>
          <button
            onClick={() => setPreview(!preview)}
            className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
          >
            <Eye className="w-3.5 h-3.5" />
            {preview ? "Edit" : "Preview"}
          </button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {preview ? (
          <div className="p-3 rounded-lg border border-border bg-white dark:bg-gray-900">
            <div className="text-xs text-green-700 dark:text-green-400">{previewUrl}</div>
            <div className="text-sm text-blue-600 dark:text-blue-400 font-medium cursor-pointer hover:underline">
              {previewTitle || "Title"}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-0.5 line-clamp-2">
              {previewDesc || "Description"}
            </div>
          </div>
        ) : (
          <>
            <div>
              <label className="text-xs font-medium mb-1 block">Meta Title</label>
              <input
                value={seo.title || ""}
                onChange={(e) => update("title", e.target.value)}
                placeholder={siteName}
                maxLength={70}
                className="w-full h-9 px-3 rounded-lg border border-input bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <span className="text-[10px] text-muted-foreground mt-0.5 block">
                {(seo.title || siteName).length}/70 characters
              </span>
            </div>
            <div>
              <label className="text-xs font-medium mb-1 block">Meta Description</label>
              <textarea
                value={seo.description || ""}
                onChange={(e) => update("description", e.target.value)}
                placeholder="Brief description for search results..."
                maxLength={160}
                rows={2}
                className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
              />
              <span className="text-[10px] text-muted-foreground mt-0.5 block">
                {(seo.description || "").length}/160 characters
              </span>
            </div>
            <div>
              <label className="text-xs font-medium mb-1 block">Keywords</label>
              <input
                value={seo.keywords || ""}
                onChange={(e) => update("keywords", e.target.value)}
                placeholder="keyword1, keyword2, keyword3"
                className="w-full h-9 px-3 rounded-lg border border-input bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            <div>
              <label className="text-xs font-medium mb-1 block">Canonical URL</label>
              <input
                value={seo.canonical_url || ""}
                onChange={(e) => update("canonical_url", e.target.value)}
                placeholder="https://example.com"
                className="w-full h-9 px-3 rounded-lg border border-input bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
