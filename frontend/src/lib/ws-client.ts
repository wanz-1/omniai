type MessageHandler = (data: any) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private shouldReconnect = true;

  connect(token: string) {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    this.shouldReconnect = true;

    const configured = process.env.NEXT_PUBLIC_WS_URL;
    let base: string;
    if (configured) {
      base = configured;
    } else if (typeof window !== "undefined") {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      base = `${proto}//${window.location.host}/api/v1/ws`;
    } else {
      base = "ws://localhost:8000/api/v1/ws";
    }
    this.ws = new WebSocket(`${base}?token=${token}`);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const { type, channel } = data;
        if (type) {
          const handlers = this.handlers.get(type);
          handlers?.forEach((handler) => handler(data));
        }
        if (channel) {
          const channelHandlers = this.handlers.get(channel);
          channelHandlers?.forEach((handler) => handler(data));
        }
      } catch {}
    };

    this.ws.onclose = () => {
      if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        setTimeout(() => this.connect(token), 1000 * Math.pow(2, this.reconnectAttempts));
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect() {
    this.shouldReconnect = false;
    this.ws?.close();
    this.ws = null;
  }

  subscribe(channel: string) {
    this.send({ type: "subscribe", channel });
  }

  unsubscribe(channel: string) {
    this.send({ type: "unsubscribe", channel });
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  on(event: string, handler: MessageHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
    return () => this.handlers.get(event)?.delete(handler);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
