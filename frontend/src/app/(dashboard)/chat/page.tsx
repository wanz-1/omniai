"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { MessageSquare, Send, Sparkles, Bot, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { chatApi } from "@/lib/api-client";
import { useStreamingAI } from "@/hooks/useStreamingAI";

interface Message {
  role: string;
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { stream: streamAI, cancel, isStreaming } = useStreamingAI();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || isLoading) return;
    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    const msgText = input;
    setInput("");
    setIsLoading(true);
    setStreamingContent("");

    try {
      let sid = sessionId;
      if (!sid) {
        const res = await chatApi.createSession({ title: msgText.slice(0, 100), model: "gpt-4o" });
        sid = res.data.id;
        setSessionId(sid);
      }

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const streamUrl = `${baseUrl}/chat/sessions/${sid}/messages/stream`;

      await streamAI(streamUrl, { content: msgText, stream: true }, {
        onToken: (token) => setStreamingContent((prev) => prev + token),
        onComplete: (fullText) => {
          setMessages((prev) => [...prev, { role: "assistant", content: fullText }]);
          setStreamingContent("");
        },
        onError: (err) => {
          setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${err.message}` }]);
          setStreamingContent("");
        },
      });
    } catch (err: any) {
      toast.error("Failed to send message");
      setStreamingContent("");
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, sessionId, streamAI]);

  const handleNewChat = () => {
    cancel();
    setMessages([]);
    setSessionId(null);
    setStreamingContent("");
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">AI Chat</h1>
          <p className="text-muted-foreground mt-1">Ask anything, get intelligent answers</p>
        </div>
        {messages.length > 0 && (
          <Button variant="outline" size="sm" onClick={handleNewChat}>
            <Trash2 className="w-4 h-4 mr-1.5" />
            New Chat
          </Button>
        )}
      </div>

      <Card className="flex-1 flex flex-col">
        <CardContent className="flex-1 flex flex-col p-4">
          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {messages.length === 0 && !streamingContent && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Sparkles className="w-12 h-12 text-primary mb-4" />
                <h3 className="text-lg font-medium">Ask me anything</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  I can help with writing, coding, analysis, and more
                </p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {streamingContent && (
              <div className="flex justify-start">
                <div className="bg-muted rounded-2xl px-4 py-3 max-w-[80%]">
                  <p className="text-sm whitespace-pre-wrap">{streamingContent}</p>
                  <span className="inline-block w-1.5 h-4 bg-primary ml-0.5 animate-pulse" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="flex items-center space-x-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              className="flex-1"
              disabled={isStreaming}
            />
            <Button onClick={handleSend} isLoading={isLoading && !isStreaming} className="px-4" disabled={isStreaming}>
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
