type MessageHandler = (data: unknown) => void;
type WSMessage = {
  type?: string;
  channel?: string;
  payload?: unknown;
  [key: string]: unknown;
};

class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private shouldReconnect = true;
  private currentToken: string | null = null;

  connect(token: string): void {
    if (typeof window === "undefined") return;
    if (this.ws?.readyState === WebSocket.OPEN && this.currentToken === token) return;

    this.shouldReconnect = true;
    this.currentToken = token;

    const wsUrl =
      process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws";

    try {
      // Ensure token is not empty
      if (!token) {
        console.warn("[ws-client] No token provided, skipping connection");
        return;
      }
      this.ws = new WebSocket(`${wsUrl}?token=${encodeURIComponent(token)}`);
    } catch (err) {
      console.error("[ws-client] Failed to create WebSocket", err);
      return;
    }

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string) as WSMessage;
        const { type, channel } = data;

        if (type) {
          const handlers = this.handlers.get(type);
          handlers?.forEach((handler) => {
            try {
              handler(data);
            } catch {
              // ignore handler errors
            }
          });
        }
        if (channel) {
          const channelHandlers = this.handlers.get(channel);
          channelHandlers?.forEach((handler) => {
            try {
              handler(data);
            } catch {
              // ignore
            }
          });
        }
      } catch {
        // ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      if (
        this.shouldReconnect &&
        this.reconnectAttempts < this.maxReconnectAttempts &&
        this.currentToken
      ) {
        this.reconnectAttempts++;
        const delay = 1000 * Math.pow(2, this.reconnectAttempts);
        setTimeout(() => {
          if (this.currentToken) this.connect(this.currentToken);
        }, Math.min(delay, 30000));
      }
    };

    this.ws.onerror = () => {
      // Close will trigger reconnect logic
      try {
        this.ws?.close();
      } catch {
        // ignore
      }
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.currentToken = null;
    try {
      this.ws?.close();
    } catch {
      // ignore
    }
    this.ws = null;
  }

  subscribe(channel: string): void {
    this.send({ type: "subscribe", channel });
  }

  unsubscribe(channel: string): void {
    this.send({ type: "unsubscribe", channel });
  }

  send(data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(data));
      } catch {
        // ignore send errors
      }
    }
  }

  on(event: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
    return () => {
      this.handlers.get(event)?.delete(handler);
    };
  }

  off(event: string, handler: MessageHandler): void {
    this.handlers.get(event)?.delete(handler);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
