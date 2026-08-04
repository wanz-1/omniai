"use client";

import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { EmptyState } from "@/components/common/EmptyState";
import { Bot, Plus } from "lucide-react";
import Link from "next/link";

export default function BotsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Bots</h1>
          <p className="text-muted-foreground mt-1">Create and deploy AI chatbots</p>
        </div>
        <Link href="/bots/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Bot
          </Button>
        </Link>
      </div>

      <Card>
        <CardContent>
          <EmptyState
            icon={<Bot className="w-12 h-12" />}
            title="No bots yet"
            description="Create your first AI chatbot for your website, WhatsApp, Telegram, or API."
            action={
              <Link href="/bots/new">
                <Button>Create Your First Bot</Button>
              </Link>
            }
          />
        </CardContent>
      </Card>
    </div>
  );
}
