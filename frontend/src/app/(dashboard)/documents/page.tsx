"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { FileText, Upload, Plus } from "lucide-react";
import Link from "next/link";

export default function DocumentsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Documents</h1>
          <p className="text-muted-foreground mt-1">Humanize, summarize, and translate your documents</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline">
            <Upload className="w-4 h-4 mr-2" />
            Upload
          </Button>
          <Link href="/documents/new">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Document
            </Button>
          </Link>
        </div>
      </div>

      <Card>
        <CardContent>
          <EmptyState
            icon={<FileText className="w-12 h-12" />}
            title="No documents yet"
            description="Upload or create your first document to get started with AI humanization."
            action={
              <Link href="/documents/new">
                <Button>Create Your First Document</Button>
              </Link>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}
