"use client";

import { useCallback, useRef, useState } from "react";

interface StreamCallbacks {
  onToken: (token: string) => void;
  onComplete: (fullText: string) => void;
  onError: (error: Error) => void;
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
        const token = localStorage.getItem("access_token");
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
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

            try {
              const parsed = JSON.parse(data);
              if (parsed.type === "done") break;
              if (parsed.type === "token") {
                bufferRef.current += parsed.content;
                callbacks.onToken(parsed.content);
              }
            } catch {
              bufferRef.current += data;
              callbacks.onToken(data);
            }
          }
        }

        callbacks.onComplete(bufferRef.current);
      } catch (err: any) {
        if (err.name === "AbortError") return;
        setError(err);
        callbacks.onError(err);
      } finally {
        setIsStreaming(false);
      }
    },
    []
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { stream, cancel, isStreaming, error };
}
