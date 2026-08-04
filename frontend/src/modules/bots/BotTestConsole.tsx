"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Send, Bot, User, RefreshCw, Trash2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { useStreamingAI } from "@/hooks/useStreamingAI";
import { botsApi } from "@/lib/api-client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface BotTestConsoleProps {
  botId: string;
  className?: string;
}

export function BotTestConsole({ botId, className }: BotTestConsoleProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streamingContent, setStreamingContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { stream, cancel, isStreaming } = useStreamingAI();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || isStreaming) return;
    const userMsg: Message = { id: Date.now().toString(), role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreamingContent("");

    const testBody = { message: input };
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const streamUrl = `${baseUrl}/bots/${botId}/test/stream`;

    await stream(streamUrl, testBody, {
      onToken: (token) => setStreamingContent((prev) => prev + token),
      onComplete: (fullText) => {
        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: fullText,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setStreamingContent("");
      },
      onError: (err) => {
        const errorMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `Error: ${err.message}`,
        };
        setMessages((prev) => [...prev, errorMsg]);
        setStreamingContent("");
      },
    });
  }, [input, isStreaming, botId, stream]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = () => {
    cancel();
    setMessages([]);
    setStreamingContent("");
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex items-center justify-between p-3 border-b border-border">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Bot className="w-4 h-4" />
          Test Console
        </h2>
        <div className="flex items-center gap-1">
          {isStreaming && (
            <Button variant="ghost" size="sm" onClick={cancel}>
              <Loader2 className="w-3 h-3 animate-spin mr-1" />
              Stop
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={handleClear} disabled={messages.length === 0}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && !streamingContent && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
            <Bot className="w-10 h-10 mb-3 opacity-40" />
            <p className="text-sm font-medium">Test your bot</p>
            <p className="text-xs mt-1">Send a message to see how your bot responds</p>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[80%] rounded-2xl px-4 py-2.5",
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-foreground"
              )}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {streamingContent && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-2xl px-4 py-2.5 max-w-[80%]">
              <p className="text-sm whitespace-pre-wrap">{streamingContent}</p>
              <span className="inline-block w-1.5 h-4 bg-primary ml-0.5 animate-pulse" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex items-center gap-2 p-3 border-t border-border">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a test message..."
          className="flex-1 px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          disabled={isStreaming}
        />
        <Button size="sm" onClick={handleSend} disabled={!input.trim() || isStreaming}>
          <Send className="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>
  );
}
