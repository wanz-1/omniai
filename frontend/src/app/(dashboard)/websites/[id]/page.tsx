"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Save,
  Sparkles,
  Eye,
  Settings,
  Rocket,
  Search,
  Palette,
  Layers,
  Loader2,
  Download,
  Wand2,
} from "lucide-react";
import { websitesApi } from "@/lib/api-client";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { WebsiteEditor } from "@/modules/websites/WebsiteEditor";
import { WebsitePreview } from "@/modules/websites/WebsitePreview";
import { ThemeCustomizer } from "@/modules/websites/ThemeCustomizer";
import { DeployPanel } from "@/modules/websites/DeployPanel";
import { SEOEditor } from "@/modules/websites/SEOEditor";

type TabId = "editor" | "preview" | "theme" | "seo" | "deploy";

interface WebsiteData {
  id: string;
  name: string;
  template_id?: string;
  framework: string;
  styling: string;
  pages?: any[];
  theme_config?: any;
  preview_url?: string;
  published_url?: string;
  deployment_status: string;
  custom_domain?: string;
  is_published: boolean;
}

export default function WebsiteWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const websiteId = params.id as string;

  const [website, setWebsite] = useState<WebsiteData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>("editor");
  const [activePage, setActivePage] = useState("index");

  useEffect(() => {
    if (websiteId) loadWebsite();
  }, [websiteId]);

  const loadWebsite = async () => {
    setIsLoading(true);
    try {
      const res = await websitesApi.get(websiteId);
      const data = res.data;
      setWebsite(data);
      if (data.pages?.length > 0) {
        setActivePage(data.pages[0].slug);
      }
    } catch {
      toast.error("Failed to load website");
      router.push("/websites");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!website) return;
    setIsGenerating(true);
    try {
      const prompt = `Generate a ${website.template_id || "custom"} website for ${website.name}`;
      await websitesApi.generate(website.id, { prompt });
      const res = await websitesApi.get(website.id);
      setWebsite(res.data);
      toast.success("Website generated!");
      setActiveTab("preview");
    } catch {
      toast.error("Generation failed");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!website) return;
    setIsSaving(true);
    try {
      await websitesApi.update(website.id, {
        name: website.name,
        pages: website.pages,
        theme_config: website.theme_config,
      });
      toast.success("Saved");
    } catch {
      toast.error("Save failed");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCustomize = async (data: any) => {
    if (!website) return;
    try {
      await websitesApi.customize(website.id, data);
    } catch {
      // silent - auto-save
    }
  };

  const handleThemeChange = async (theme: any) => {
    if (!website) return;
    const next = { ...website, theme_config: theme };
    setWebsite(next);
    await handleCustomize({ theme_config: theme });
  };

  const handlePagesChange = async (pages: any[]) => {
    if (!website) return;
    const next = { ...website, pages };
    setWebsite(next);
  };

  const handleAddPage = () => {
    if (!website) return;
    const slug = `page-${(website.pages?.length || 0) + 1}`;
    const newPage = { slug, title: `Page ${(website.pages?.length || 0) + 1}`, sections: [] };
    const pages = [...(website.pages || []), newPage];
    handlePagesChange(pages);
    setActivePage(slug);
  };

  const handleAddSection = (pageSlug: string, sectionType: string) => {
    if (!website) return;
    const pages = (website.pages || []).map((p) => {
      if (p.slug !== pageSlug) return p;
      const defaultContent: Record<string, any> = {
        hero: { heading: "Welcome", subheading: "Subtitle", cta: "Get Started" },
        features: { heading: "Features", items: [{ title: "Feature 1", description: "Description" }] },
        about: { heading: "About", text: "About content" },
        contact: { heading: "Contact Us", email: "email@example.com" },
        cta: { heading: "Ready?", text: "Get started today", button_text: "Start Now" },
        stats: { items: [{ value: "100+", label: "Clients" }] },
        team: { heading: "Team", items: [{ name: "John Doe", role: "CEO" }] },
        testimonials: { heading: "Testimonials", items: [{ quote: "Great service!", author: "Jane" }] },
        pricing: { heading: "Pricing", items: [{ name: "Basic", price: "$9", features: ["Feature 1"] }] },
        faq: { heading: "FAQ", items: [{ question: "Question?", answer: "Answer" }] },
        gallery: { heading: "Gallery", images: [{ alt: "Image 1" }] },
        blog: { heading: "Blog", posts: [{ title: "Post 1", excerpt: "Excerpt" }] },
      };
      return {
        ...p,
        sections: [...(p.sections || []), { type: sectionType, content: defaultContent[sectionType] || {} }],
      };
    });
    handlePagesChange(pages);
  };

  const handleRemoveSection = (pageSlug: string, sectionIndex: number) => {
    if (!website) return;
    const pages = (website.pages || []).map((p) => {
      if (p.slug !== pageSlug) return p;
      return { ...p, sections: (p.sections || []).filter((_: any, i: number) => i !== sectionIndex) };
    });
    handlePagesChange(pages);
  };

  const handleMoveSection = (pageSlug: string, from: number, to: number) => {
    if (!website) return;
    const pages = (website.pages || []).map((p) => {
      if (p.slug !== pageSlug) return p;
      const sections = [...(p.sections || [])];
      const [removed] = sections.splice(from, 1);
      sections.splice(to, 0, removed);
      return { ...p, sections };
    });
    handlePagesChange(pages);
  };

  const handlePublish = async (data: { subdomain?: string; custom_domain?: string }) => {
    if (!website) return;
    setIsPublishing(true);
    try {
      const res = await websitesApi.publish(website.id, data);
      const next = { ...website, published_url: res.data.published_url, is_published: true, deployment_status: "deployed" };
      setWebsite(next);
      toast.success("Published!");
    } catch {
      toast.error("Publish failed");
    } finally {
      setIsPublishing(false);
    }
  };

  const handleDeploy = async (platform: string) => {
    if (!website) return;
    setIsDeploying(true);
    try {
      const res = await websitesApi.deploy(website.id, { platform });
      const next = { ...website, published_url: res.data.url, deployment_status: "deployed" };
      setWebsite(next);
      toast.success(`Deployed to ${platform}!`);
    } catch {
      toast.error("Deploy failed");
    } finally {
      setIsDeploying(false);
    }
  };

  const handleExport = async () => {
    if (!website) return;
    try {
      const res = await websitesApi.export(website.id);
      const blob = new Blob([res.data]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${website.name.replace(/\s+/g, "_").toLowerCase()}.html`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Download started");
    } catch {
      toast.error("Export failed");
    }
  };

  const tabs = [
    { id: "editor" as const, label: "Pages", icon: Layers },
    { id: "preview" as const, label: "Preview", icon: Eye },
    { id: "theme" as const, label: "Theme", icon: Palette },
    { id: "seo" as const, label: "SEO", icon: Search },
    { id: "deploy" as const, label: "Deploy", icon: Rocket },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!website) return null;

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col animate-fade-in">
      <header className="flex items-center justify-between px-4 py-2 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/websites")} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <input
            value={website.name}
            onChange={(e) => setWebsite({ ...website, name: e.target.value })}
            className="text-lg font-semibold bg-transparent border-none outline-none focus-visible:ring-0 px-1"
          />
          <Badge variant="outline">{website.framework}</Badge>
          <Badge variant="outline">{website.styling}</Badge>
          <Badge
            variant={
              website.deployment_status === "deployed"
                ? "success"
                : website.deployment_status === "building"
                  ? "warning"
                  : "default"
            }
          >
            {website.deployment_status}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleExport} title="Download HTML">
            <Download className="w-4 h-4 mr-1.5" />
            Export
          </Button>
          <Button variant="outline" size="sm" onClick={handleSave} isLoading={isSaving}>
            <Save className="w-4 h-4 mr-1.5" />
            Save
          </Button>
          <Button
            size="sm"
            onClick={handleGenerate}
            isLoading={isGenerating}
            disabled={isGenerating}
          >
            <Sparkles className="w-4 h-4 mr-1.5" />
            Generate
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex flex-col border-r border-border bg-card w-56 shrink-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2.5 px-4 py-3 text-sm transition-colors text-left ${
                activeTab === tab.id
                  ? "bg-primary/5 text-primary border-r-2 border-primary font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-hidden">
          {activeTab === "editor" && (
            <WebsiteEditor
              pages={website.pages || []}
              activePage={activePage}
              onPageChange={setActivePage}
              onPagesChange={handlePagesChange}
              onAddPage={handleAddPage}
              onAddSection={handleAddSection}
              onRemoveSection={handleRemoveSection}
              onMoveSection={handleMoveSection}
              className="h-full"
            />
          )}

          {activeTab === "preview" && (
            <WebsitePreview
              previewUrl={website.preview_url ?? null}
              isGenerating={isGenerating}
              onGenerate={handleGenerate}
              className="h-full"
            />
          )}

          {activeTab === "theme" && (
            <div className="p-6 overflow-y-auto h-full max-w-2xl">
              <ThemeCustomizer
                theme={website.theme_config || {}}
                onChange={handleThemeChange}
              />
            </div>
          )}

          {activeTab === "seo" && (
            <div className="p-6 overflow-y-auto h-full max-w-2xl">
              <SEOEditor
                seo={website.theme_config?.seo || {}}
                onChange={(seo) => handleThemeChange({ ...website.theme_config, seo })}
                siteName={website.name}
              />
            </div>
          )}

          {activeTab === "deploy" && (
            <div className="p-6 overflow-y-auto h-full max-w-lg">
              <DeployPanel
                publishedUrl={website.published_url ?? null}
                deploymentStatus={website.deployment_status}
                isPublished={website.is_published}
                customDomain={website.custom_domain ?? null}
                onPublish={handlePublish}
                onDeploy={handleDeploy}
                isPublishing={isPublishing}
                isDeploying={isDeploying}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
