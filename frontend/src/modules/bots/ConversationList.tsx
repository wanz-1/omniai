"use client";

import { useEffect, useState } from "react";
import { MessageSquare, Search, Calendar, ChevronRight, Loader2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { botsApi } from "@/lib/api-client";
import { toast } from "sonner";

interface Conversation {
  id: string;
  bot_id: string;
  session_id: string;
  channel: string;
  is_active: boolean;
  created_at: string;
}

interface Message {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  created_at: string;
}

interface ConversationListProps {
  botId: string;
  className?: string;
}

export function ConversationList({ botId, className }: ConversationListProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConv, setSelectedConv] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadConversations();
  }, [botId]);

  useEffect(() => {
    if (selectedConv) loadMessages(selectedConv);
  }, [selectedConv]);

  const loadConversations = async () => {
    setIsLoading(true);
    try {
      const res = await botsApi.conversations(botId);
      setConversations(res.data);
    } catch {
      toast.error("Failed to load conversations");
    } finally {
      setIsLoading(false);
    }
  };

  const loadMessages = async (convId: string) => {
    setIsLoadingMessages(true);
    try {
      const res = await botsApi.getConversationMessages(botId, convId);
      setMessages(res.data);
    } catch {
      toast.error("Failed to load messages");
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const filteredConversations = conversations.filter(
    (c) =>
      c.session_id.toLowerCase().includes(search.toLowerCase()) ||
      c.channel.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex items-center justify-between p-3 border-b border-border">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <MessageSquare className="w-4 h-4" />
          Conversations
        </h2>
        <Button variant="ghost" size="sm" onClick={loadConversations}>
          <RefreshCw className="w-3.5 h-3.5" />
        </Button>
      </div>

      <div className="flex-1 flex">
        <div className="w-1/2 border-r border-border flex flex-col">
          <div className="p-2 border-b border-border">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search conversations..."
                className="w-full pl-8 pr-3 py-1.5 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground p-4">
                <MessageSquare className="w-8 h-8 mb-2 opacity-40" />
                <p className="text-xs">No conversations yet</p>
              </div>
            ) : (
              filteredConversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setSelectedConv(conv.id)}
                  className={cn(
                    "w-full text-left px-3 py-2.5 hover:bg-muted/50 transition-colors border-b border-border/50",
                    selectedConv === conv.id && "bg-primary/5"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                      <MessageSquare className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                      <span className="text-sm truncate">{conv.session_id.slice(0, 24)}...</span>
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <Calendar className="w-3 h-3 text-muted-foreground" />
                    <span className="text-[10px] text-muted-foreground">
                      {new Date(conv.created_at).toLocaleDateString()}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                      {conv.channel}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        <div className="flex-1 flex flex-col">
          {selectedConv ? (
            <>
              <div className="px-3 py-2 border-b border-border text-xs text-muted-foreground font-medium">
                Messages
              </div>
              <div className="flex-1 overflow-y-auto p-3 space-y-3">
                {isLoadingMessages ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                  </div>
                ) : messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-xs text-muted-foreground">
                    No messages in this conversation
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={cn(
                        "flex",
                        msg.role === "user" ? "justify-end" : "justify-start"
                      )}
                    >
                      <div
                        className={cn(
                          "max-w-[80%] rounded-2xl px-3 py-2",
                          msg.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-foreground"
                        )}
                      >
                        <p className="text-xs whitespace-pre-wrap">{msg.content}</p>
                        <p className="text-[10px] opacity-60 mt-1">
                          {new Date(msg.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-xs text-muted-foreground">
              Select a conversation to view messages
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
