"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { marketplaceExtendedApi } from "@/lib/api-client";
import { toast } from "sonner";
import {
  Store, Package, User, Code, Puzzle, Building2, Grid,
  Search, Star, Download, Upload, Plus, Settings, Trash2,
  Loader2, CheckCircle, XCircle, ExternalLink, Shield,
} from "lucide-react";

type Tab = "browse" | "creator" | "developer" | "plugins" | "enterprise" | "my-products";

export default function MarketplacePage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("browse");
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => { loadOrg(); }, []);
  useEffect(() => { if (orgId) loadDashboard(); }, [orgId]);

  const loadOrg = async () => {
    try {
      const res = await fetch("/api/organizations");
      const orgs = await res.json();
      if (orgs.length > 0) setOrgId(orgs[0].id);
    } catch {} finally { setLoading(false); }
  };

  const loadDashboard = async () => {
    try {
      const res = await marketplaceExtendedApi.dashboard();
      setDashboard(res.data);
    } catch {}
  };

  const tabs: { key: Tab; label: string; icon: any; description: string }[] = [
    { key: "browse", label: "Browse", icon: Grid, description: "Explore marketplace products" },
    { key: "creator", label: "Creator", icon: User, description: "Your creator profile & analytics" },
    { key: "developer", label: "Developer", icon: Code, description: "SDK & developer tools" },
    { key: "plugins", label: "Plugins", icon: Puzzle, description: "Plugin registry & management" },
    { key: "enterprise", label: "Enterprise", icon: Building2, description: "Enterprise listings & licensing" },
    { key: "my-products", label: "My Products", icon: Package, description: "Products you've published" },
  ];

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Marketplace</h1>
        <p className="text-muted-foreground mt-1">AI marketplace ecosystem — publish, discover, verify, and monetize AI products</p>
      </div>

      {dashboard && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.total_products}</p><p className="text-xs text-muted-foreground">Total Products</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.total_creators}</p><p className="text-xs text-muted-foreground">Creators</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.top_products?.length || 0}</p><p className="text-xs text-muted-foreground">Featured</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.total_products}</p><p className="text-xs text-muted-foreground">Downloads</p></CardContent></Card>
        </div>
      )}

      <div className="flex gap-2 overflow-x-auto pb-2">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
              tab === t.key ? "bg-primary/10 text-primary font-medium border border-primary/30" : "text-muted-foreground hover:bg-muted border border-transparent"
            }`}
          >
            <t.icon className="w-4 h-4" />
            <span className="hidden sm:inline">{t.label}</span>
          </button>
        ))}
      </div>

      {tab === "browse" && <BrowseTab />}
      {tab === "creator" && <CreatorTab />}
      {tab === "developer" && <DeveloperTab />}
      {tab === "plugins" && <PluginsTab />}
      {tab === "enterprise" && <EnterpriseTab />}
      {tab === "my-products" && <MyProductsTab />}
    </div>
  );
}

function BrowseTab() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    marketplaceExtendedApi.products().then((res) => setProducts(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const filtered = products.filter((p) => !search || p.name?.toLowerCase().includes(search.toLowerCase()) || p.description?.toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin" /></div>;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search products..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline"><Grid className="w-4 h-4 mr-2" />Categories</Button>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {filtered.map((p) => (
          <Card key={p.id} className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="text-lg">{p.name}</CardTitle>
              <CardDescription className="line-clamp-2">{p.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Badge variant="outline">{p.item_type || p.category}</Badge>
                {p.rating && <span className="flex items-center gap-1"><Star className="w-3 h-3 fill-yellow-500 text-yellow-500" />{p.rating.toFixed(1)}</span>}
                <span className="flex items-center gap-1"><Download className="w-3 h-3" />{p.downloads || 0}</span>
              </div>
              {p.price > 0 && <p className="mt-2 font-semibold text-primary">${p.price.toFixed(2)}</p>}
              {p.price === 0 && <Badge className="mt-2 bg-green-500/10 text-green-600">Free</Badge>}
            </CardContent>
          </Card>
        ))}
        {filtered.length === 0 && <p className="col-span-3 text-center text-muted-foreground py-8">No products found</p>}
      </div>
    </div>
  );
}

function CreatorTab() {
  const [profile, setProfile] = useState<any>(null);
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      marketplaceExtendedApi.getCreatorProfile(),
      marketplaceExtendedApi.getCreatorDashboard(),
    ]).then(([p, d]) => { setProfile(p.data); setDashboard(d.data); }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin" /></div>;

  return (
    <div className="space-y-6">
      {profile && (
        <Card>
          <CardHeader>
            <CardTitle>{profile.display_name}</CardTitle>
            <CardDescription>{profile.bio || "No bio yet"}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center"><p className="text-2xl font-bold">{profile.total_products}</p><p className="text-xs text-muted-foreground">Products</p></div>
              <div className="text-center"><p className="text-2xl font-bold">{profile.total_sales}</p><p className="text-xs text-muted-foreground">Sales</p></div>
              <div className="text-center"><p className="text-2xl font-bold">${profile.total_revenue?.toFixed(2) || "0.00"}</p><p className="text-xs text-muted-foreground">Revenue</p></div>
              <div className="text-center"><p className="text-2xl font-bold">{profile.average_rating ? profile.average_rating.toFixed(1) : "—"}</p><p className="text-xs text-muted-foreground">Rating</p></div>
            </div>
            {profile.is_verified && <Badge className="mt-4"><Shield className="w-3 h-3 mr-1" />Verified Creator</Badge>}
          </CardContent>
        </Card>
      )}

      {dashboard && (
        <>
          <h3 className="text-lg font-semibold">Analytics</h3>
          <div className="grid gap-4 md:grid-cols-3">
            <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.total_sales}</p><p className="text-xs text-muted-foreground">Total Sales</p></CardContent></Card>
            <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">${dashboard.total_revenue?.toFixed(2) || "0.00"}</p><p className="text-xs text-muted-foreground">Revenue</p></CardContent></Card>
            <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.average_rating ? dashboard.average_rating.toFixed(1) : "—"}</p><p className="text-xs text-muted-foreground">Avg Rating</p></CardContent></Card>
          </div>
          {dashboard.recent_sales?.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Recent Sales</CardTitle></CardHeader>
              <CardContent>
                {dashboard.recent_sales.map((s: any, i: number) => (
                  <div key={i} className="flex justify-between text-sm py-1 border-b last:border-0">
                    <span>{s.product_name || s.product_id}</span>
                    <span className="text-muted-foreground">${s.amount?.toFixed(2) || "0.00"}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function DeveloperTab() {
  const [language, setLanguage] = useState("python");
  const [sdkCode, setSdkCode] = useState("");
  const [generating, setGenerating] = useState(false);
  const [features, setFeatures] = useState("");

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const featList = features.split(",").map((f) => f.trim()).filter(Boolean);
      const res = await marketplaceExtendedApi.generateSDK({ language, features: featList.length > 0 ? featList : undefined });
      setSdkCode(res.data.sdk_code || res.data.code || JSON.stringify(res.data, null, 2));
      toast.success("SDK generated");
    } catch { toast.error("Failed to generate SDK"); } finally { setGenerating(false); }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>SDK Generator</CardTitle>
          <CardDescription>Generate AI marketplace SDKs for any language</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-lg border bg-background"
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="java">Java</option>
                <option value="go">Go</option>
                <option value="rust">Rust</option>
              </select>
            </div>
            <div className="flex-[2]">
              <label className="text-sm font-medium">Features (comma-separated)</label>
              <Input
                placeholder="auth, products, purchases, reviews, plugins"
                value={features}
                onChange={(e) => setFeatures(e.target.value)}
                className="mt-1"
              />
            </div>
          </div>
          <Button onClick={handleGenerate} disabled={generating}>
            {generating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Code className="w-4 h-4 mr-2" />}
            Generate SDK
          </Button>
        </CardContent>
      </Card>

      {sdkCode && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Generated SDK ({language})</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-xs max-h-96 overflow-y-auto"><code>{sdkCode}</code></pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function PluginsTab() {
  const [plugins, setPlugins] = useState<any[]>([]);
  const [installed, setInstalled] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRegister, setShowRegister] = useState(false);
  const [form, setForm] = useState({ name: "", slug: "", plugin_type: "tool", description: "" });

  useEffect(() => {
    Promise.all([
      marketplaceExtendedApi.listPlugins(),
      marketplaceExtendedApi.getInstalledPlugins(),
    ]).then(([p, i]) => { setPlugins(p.data); setInstalled(i.data); }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleRegister = async () => {
    try {
      await marketplaceExtendedApi.registerPlugin(form);
      toast.success("Plugin registered");
      setShowRegister(false);
      setForm({ name: "", slug: "", plugin_type: "tool", description: "" });
      const res = await marketplaceExtendedApi.listPlugins();
      setPlugins(res.data);
    } catch { toast.error("Failed to register plugin"); }
  };

  const handleInstall = async (pluginId: string) => {
    try {
      await marketplaceExtendedApi.installPlugin(pluginId);
      toast.success("Plugin installed");
      const res = await marketplaceExtendedApi.getInstalledPlugins();
      setInstalled(res.data);
    } catch { toast.error("Failed to install plugin"); }
  };

  const handleUninstall = async (installationId: string) => {
    try {
      await marketplaceExtendedApi.uninstallPlugin(installationId);
      toast.success("Plugin uninstalled");
      const res = await marketplaceExtendedApi.getInstalledPlugins();
      setInstalled(res.data);
    } catch { toast.error("Failed to uninstall"); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin" /></div>;

  const installedIds = new Set(installed.map((i: any) => i.plugin_id));

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Plugin Registry</h3>
        <Button onClick={() => setShowRegister(!showRegister)}><Plus className="w-4 h-4 mr-2" />Register Plugin</Button>
      </div>

      {showRegister && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Register New Plugin</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input placeholder="Slug" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} />
            <select
              value={form.plugin_type}
              onChange={(e) => setForm({ ...form, plugin_type: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border bg-background"
            >
              <option value="tool">Tool</option>
              <option value="connector">Connector</option>
              <option value="widget">Widget</option>
              <option value="workflow">Workflow</option>
              <option value="agent">Agent</option>
            </select>
            <Input placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            <Button onClick={handleRegister}><Upload className="w-4 h-4 mr-2" />Register</Button>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {plugins.map((p) => (
          <Card key={p.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-sm">{p.name}</CardTitle>
                  <CardDescription className="line-clamp-1">{p.description}</CardDescription>
                </div>
                <Badge variant={p.is_official ? "default" : "outline"}>{p.plugin_type}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">v{p.version}</span>
                {installedIds.has(p.id) ? (
                  <Button variant="outline" size="sm" onClick={() => handleUninstall(p.installation_id || p.id)}><Trash2 className="w-3 h-3 mr-1" />Uninstall</Button>
                ) : (
                  <Button size="sm" onClick={() => handleInstall(p.id)}><Download className="w-3 h-3 mr-1" />Install</Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
        {plugins.length === 0 && <p className="col-span-2 text-center text-muted-foreground py-8">No plugins available</p>}
      </div>
    </div>
  );
}

function EnterpriseTab() {
  const [enterpriseListings, setEnterpriseListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    marketplaceExtendedApi.products({ item_type: "enterprise" }).then((res) => setEnterpriseListings(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin" /></div>;

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Enterprise Listings</h3>
        <p className="text-sm text-muted-foreground">Private listings, custom licensing, and premium support for enterprise customers</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {enterpriseListings.map((p: any) => (
          <Card key={p.id} className="border-primary/20">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-sm">{p.name}</CardTitle>
                  <CardDescription className="line-clamp-2">{p.description}</CardDescription>
                </div>
                <Badge className="bg-purple-500/10 text-purple-600">Enterprise</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span className="flex items-center gap-1"><Shield className="w-3 h-3" />Premium</span>
                {p.price > 0 && <span className="font-semibold text-primary">${p.price.toFixed(2)}</span>}
                <Badge variant="outline">Custom Licensing</Badge>
              </div>
            </CardContent>
          </Card>
        ))}
        {enterpriseListings.length === 0 && <p className="col-span-2 text-center text-muted-foreground py-8">No enterprise listings yet</p>}
      </div>
    </div>
  );
}

function MyProductsTab() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPublish, setShowPublish] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", short_description: "", item_type: "agent", category: "", price: 0, tags: "" });

  useEffect(() => { loadProducts(); }, []);

  const loadProducts = async () => {
    try {
      const res = await marketplaceExtendedApi.myProducts();
      setProducts(res.data);
    } catch {} finally { setLoading(false); }
  };

  const handlePublish = async () => {
    try {
      await marketplaceExtendedApi.publishProduct({
        ...form,
        tags: form.tags.split(",").map((t) => t.trim()).filter(Boolean),
      });
      toast.success("Product published");
      setShowPublish(false);
      setForm({ name: "", description: "", short_description: "", item_type: "agent", category: "", price: 0, tags: "" });
      loadProducts();
    } catch { toast.error("Failed to publish"); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin" /></div>;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">My Published Products ({products.length})</h3>
        <Button onClick={() => setShowPublish(!showPublish)}><Plus className="w-4 h-4 mr-2" />Publish Product</Button>
      </div>

      {showPublish && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Publish New Product</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input placeholder="Short description" value={form.short_description} onChange={(e) => setForm({ ...form, short_description: e.target.value })} />
            <textarea
              placeholder="Full description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border bg-background min-h-[80px]"
            />
            <div className="flex gap-3">
              <select
                value={form.item_type}
                onChange={(e) => setForm({ ...form, item_type: e.target.value })}
                className="flex-1 px-3 py-2 rounded-lg border bg-background"
              >
                <option value="agent">Agent</option>
                <option value="template">Template</option>
                <option value="workflow">Workflow</option>
                <option value="tool">Tool</option>
                <option value="dataset">Dataset</option>
                <option value="enterprise">Enterprise</option>
              </select>
              <Input
                placeholder="Category"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="flex-1"
              />
            </div>
            <div className="flex gap-3">
              <Input
                type="number"
                placeholder="Price (0 = free)"
                value={form.price}
                onChange={(e) => setForm({ ...form, price: parseFloat(e.target.value) || 0 })}
                className="flex-1"
              />
              <Input
                placeholder="Tags (comma-separated)"
                value={form.tags}
                onChange={(e) => setForm({ ...form, tags: e.target.value })}
                className="flex-[2]"
              />
            </div>
            <Button onClick={handlePublish}><Upload className="w-4 h-4 mr-2" />Publish</Button>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {products.map((p) => (
          <Card key={p.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-sm">{p.name}</CardTitle>
                  <CardDescription className="line-clamp-1">{p.short_description || p.description}</CardDescription>
                </div>
                <Badge variant={p.status === "approved" ? "default" : p.status === "pending" ? "outline" : "error"}>{p.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <Badge variant="outline">{p.item_type}</Badge>
                {p.downloads > 0 && <span className="flex items-center gap-1"><Download className="w-3 h-3" />{p.downloads}</span>}
                {p.rating > 0 && <span className="flex items-center gap-1"><Star className="w-3 h-3 fill-yellow-500 text-yellow-500" />{p.rating.toFixed(1)}</span>}
                {p.price > 0 && <span className="font-semibold">${p.price.toFixed(2)}</span>}
              </div>
            </CardContent>
          </Card>
        ))}
        {products.length === 0 && <p className="col-span-2 text-center text-muted-foreground py-8">No products published yet</p>}
      </div>
    </div>
  );
}
