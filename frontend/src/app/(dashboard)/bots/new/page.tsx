"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { botsApi } from "@/lib/api-client";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";

export default function NewBotPage() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleCreate = async () => {
    if (!name.trim()) {
      toast.error("Bot name is required");
      return;
    }
    setIsLoading(true);
    try {
      const response = await botsApi.create({
        name,
        description: description || undefined,
        system_prompt: systemPrompt || undefined,
      });
      toast.success("Bot created!");
      router.push(`/bots/${response.data.id}`);
    } catch {
      toast.error("Failed to create bot");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">New Bot</h1>
        <p className="text-muted-foreground mt-1">Create an AI chatbot for your needs</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Bot Configuration</CardTitle>
          <CardDescription>Define your bot personality and knowledge</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            id="name"
            label="Bot Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Customer Support Bot"
            required
          />
          <Input
            id="description"
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="A helpful customer support bot..."
          />
          <div>
            <label className="text-sm font-medium mb-2 block">System Prompt</label>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="You are a helpful AI assistant that..."
              className="w-full min-h-[150px] rounded-lg border border-input bg-background p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
            />
          </div>
          <Button onClick={handleCreate} isLoading={isLoading} className="w-full">
            <Sparkles className="w-4 h-4 mr-2" />
            Create Bot
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
