"use client";

import { useCallback, useRef, useState } from "react";

interface StreamCallbacks {
  onToken: (token: string) => void;
  onComplete: (fullText: string) => void;
  onError: (error: Error) => void;
}

interface SSEEvent {
  type?: string;
  content?: string;
  [key: string]: unknown;
}

function safeGetToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem("access_token");
  } catch {
    return null;
  }
}

export function useStreamingAI() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bufferRef = useRef<string>("");

  const stream = useCallback(
    async (url: string, body: unknown, callbacks: StreamCallbacks) => {
      setIsStreaming(true);
      setError(null);
      bufferRef.current = "";
      abortRef.current = new AbortController();

      try {
        const token = safeGetToken();
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(body),
          signal: abortRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6).trim();
            if (!data) continue;
            if (data === "[DONE]") break;

            try {
              const parsed = JSON.parse(data) as SSEEvent;
              if (parsed.type === "done") break;
              if (parsed.type === "token" && typeof parsed.content === "string") {
                bufferRef.current += parsed.content;
                callbacks.onToken(parsed.content);
              } else if (typeof parsed.content === "string") {
                bufferRef.current += parsed.content;
                callbacks.onToken(parsed.content);
              }
            } catch {
              // Fallback: treat raw line as token
              bufferRef.current += data;
              callbacks.onToken(data);
            }
          }
        }

        callbacks.onComplete(bufferRef.current);
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") return;
        const errorObj = err instanceof Error ? err : new Error(String(err));
        setError(errorObj);
        callbacks.onError(errorObj);
      } finally {
        setIsStreaming(false);
      }
    },
    []
  );

  const cancel = useCallback(() => {
    try {
      abortRef.current?.abort();
    } catch {
      // ignore
    }
    setIsStreaming(false);
  }, []);

  return { stream, cancel, isStreaming, error };
}
