"use client";

import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { Globe, Plus } from "lucide-react";
import Link from "next/link";

export default function WebsitesPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Websites</h1>
          <p className="text-muted-foreground mt-1">Build and deploy websites with AI</p>
        </div>
        <Link href="/websites/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Website
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {["Business/Corporate", "Portfolio", "NGO/Charity", "E-Commerce", "Restaurant", "Hotel & Travel", "School/Education", "Healthcare", "SaaS Startup", "Landing Page"].map((template) => (
          <Card key={template} className="card-hover cursor-pointer">
            <CardContent className="p-6">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center mb-4">
                <Globe className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-medium">{template}</h3>
              <p className="text-sm text-muted-foreground mt-1">AI-powered {template.toLowerCase()} website</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
