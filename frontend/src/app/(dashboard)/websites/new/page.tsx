"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { websitesApi } from "@/lib/api-client";
import { Globe, Sparkles } from "lucide-react";
import { toast } from "sonner";

const templates = [
  { id: "business", name: "Business/Corporate" },
  { id: "portfolio", name: "Portfolio" },
  { id: "ngo", name: "NGO/Charity" },
  { id: "ecommerce", name: "E-Commerce" },
  { id: "restaurant", name: "Restaurant" },
  { id: "hotel", name: "Hotel & Travel" },
  { id: "school", name: "School/Education" },
  { id: "healthcare", name: "Healthcare" },
  { id: "saas", name: "SaaS Startup" },
  { id: "landing", name: "Landing Page" },
];

export default function NewWebsitePage() {
  const [name, setName] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleCreate = async () => {
    if (!name.trim()) {
      toast.error("Website name is required");
      return;
    }
    setIsLoading(true);
    try {
      const response = await websitesApi.create({ name, template_id: templateId || undefined });
      const website = response.data;

      if (prompt.trim()) {
        await websitesApi.generate(website.id, { prompt });
      }

      toast.success("Website created!");
      router.push(`/websites/${website.id}`);
    } catch {
      toast.error("Failed to create website");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">New Website</h1>
        <p className="text-muted-foreground mt-1">Describe your website and let AI build it</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Website Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            id="name"
            label="Website Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Awesome Website"
            required
          />

          <div>
            <label className="text-sm font-medium mb-2 block">Template (optional)</label>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
              <button
                onClick={() => setTemplateId("")}
                className={`p-3 rounded-lg border text-sm transition-all ${
                  !templateId
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border hover:border-muted-foreground"
                }`}
              >
                <Globe className="w-5 h-5 mx-auto mb-1" />
                AI Generate
              </button>
              {templates.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTemplateId(t.id)}
                  className={`p-3 rounded-lg border text-sm transition-all ${
                    templateId === t.id
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border hover:border-muted-foreground"
                  }`}
                >
                  <Globe className="w-5 h-5 mx-auto mb-1" />
                  {t.name}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Describe your website (optional)</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder='e.g., "Build a modern NGO website for Youth4 Integrity Building with donation, volunteer registration, events, blog, and contact pages."'
              className="w-full min-h-[120px] rounded-lg border border-input bg-background p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
            />
          </div>

          <Button onClick={handleCreate} isLoading={isLoading} className="w-full">
            <Sparkles className="w-4 h-4 mr-2" />
            Generate Website
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
