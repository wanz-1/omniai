"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { documentsApi } from "@/lib/api-client";
import { toast } from "sonner";

export default function NewDocumentPage() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      toast.error("Title is required");
      return;
    }
    setIsLoading(true);
    try {
      const response = await documentsApi.create({ title, content });
      toast.success("Document created");
      router.push(`/documents/${response.data.id}`);
    } catch {
      toast.error("Failed to create document");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">New Document</h1>
        <p className="text-muted-foreground mt-1">Create a document to humanize with AI</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Document Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              id="title"
              label="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter document title"
              required
            />
            <div>
              <label className="text-sm font-medium mb-2 block">Content</label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Paste or write your document content here..."
                className="w-full min-h-[300px] rounded-lg border border-input bg-background p-4 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
              />
            </div>
            <Button type="submit" isLoading={isLoading}>
              Create Document
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
