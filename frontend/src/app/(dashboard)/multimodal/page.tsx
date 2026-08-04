"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { VoiceRecorder } from "@/modules/media/VoiceRecorder";
import { VisionAnalyzer } from "@/modules/media/VisionAnalyzer";
import { VideoProcessor } from "@/modules/media/VideoProcessor";
import { voiceApi, visionApi } from "@/lib/api-client";
import { toast } from "sonner";
import { MessageSquare, Mic, Image, Video, Send, Loader2 } from "lucide-react";

type Modality = "text" | "voice" | "image" | "video";

export default function MultimodalPage() {
  const [modality, setModality] = useState<Modality>("text");
  const [textInput, setTextInput] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [processing, setProcessing] = useState(false);
  const [voiceSessionId, setVoiceSessionId] = useState<string | null>(null);

  const handleTextSend = async () => {
    if (!textInput.trim()) return;
    const userMsg = { role: "user", text: textInput };
    setMessages((prev) => [...prev, userMsg]);
    setTextInput("");
    setProcessing(true);

    try {
      const res = await fetch("/api/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("access_token")}` },
        body: JSON.stringify({ prompt: textInput, stream: false }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.text || data.response || "No response" }]);
    } catch {
      toast.error("Failed to get response");
    } finally {
      setProcessing(false);
    }
  };

  const handleVoiceResult = async (blob: Blob, durationMs: number) => {
    setProcessing(true);
    try {
      if (!voiceSessionId) {
        const sessionRes = await voiceApi.createSession({ language: "en" });
        setVoiceSessionId(sessionRes.data.id);
        const res = await voiceApi.processMessage(sessionRes.data.id, new File([blob], "voice.webm", { type: "audio/webm" }));
        const userMsg = { role: "user", text: res.data.user_message.text, modality: "voice" };
        const aiMsg = { role: "assistant", text: res.data.assistant_message.text, modality: "voice" };
        setMessages((prev) => [...prev, userMsg, aiMsg]);
      } else {
        const res = await voiceApi.processMessage(voiceSessionId, new File([blob], "voice.webm", { type: "audio/webm" }));
        const userMsg = { role: "user", text: res.data.user_message.text, modality: "voice" };
        const aiMsg = { role: "assistant", text: res.data.assistant_message.text, modality: "voice" };
        setMessages((prev) => [...prev, userMsg, aiMsg]);
      }
    } catch {
      toast.error("Voice processing failed");
    } finally {
      setProcessing(false);
    }
  };

  const handleVisionResult = (result: any) => {
    setMessages((prev) => [
      ...prev,
      { role: "user", text: "Analyzed image", modality: "image" },
      { role: "assistant", text: result.description || JSON.stringify(result, null, 2), modality: "image" },
    ]);
  };

  const modalities: { key: Modality; label: string; icon: any }[] = [
    { key: "text", label: "Text", icon: MessageSquare },
    { key: "voice", label: "Voice", icon: Mic },
    { key: "image", label: "Image", icon: Image },
    { key: "video", label: "Video", icon: Video },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Multimodal Workspace</h1>
        <p className="text-muted-foreground mt-1">Chat using text, voice, images, and video</p>
      </div>

      <div className="flex gap-2 border-b pb-2">
        {modalities.map(({ key, label, icon: Icon }) => (
          <Button
            key={key}
            variant={modality === key ? "primary" : "ghost"}
            size="sm"
            onClick={() => setModality(key)}
          >
            <Icon className="w-4 h-4 mr-2" />
            {label}
          </Button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          {modality === "text" && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex gap-2">
                  <input
                    className="flex-1 h-10 rounded-lg border border-input bg-background px-3 py-2 text-sm"
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleTextSend()}
                    placeholder="Type your message..."
                  />
                  <Button onClick={handleTextSend} isLoading={processing} size="sm">
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {modality === "voice" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Voice Input</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center p-8">
                  <VoiceRecorder onRecordingComplete={handleVoiceResult} isProcessing={processing} />
                </div>
                {voiceSessionId && (
                  <p className="text-xs text-muted-foreground text-center">
                    Session active. Keep speaking.
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {modality === "image" && (
            <VisionAnalyzer onResult={handleVisionResult} />
          )}

          {modality === "video" && (
            <VideoProcessor />
          )}
        </div>

        <div>
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="text-sm">Conversation</CardTitle>
            </CardHeader>
            <CardContent>
              {messages.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  Ask AI anything using text, voice, images, or video
                </p>
              ) : (
                <div className="space-y-4 max-h-[500px] overflow-y-auto">
                  {messages.map((msg, i) => (
                    <div key={i} className={`flex gap-3 ${msg.role === "assistant" ? "" : "flex-row-reverse"}`}>
                      <div
                        className={`rounded-xl px-4 py-2 max-w-[80%] text-sm ${
                          msg.role === "assistant"
                            ? "bg-muted/50"
                            : "bg-primary text-primary-foreground"
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          {msg.modality && (
                            <span className="text-xs opacity-70">{msg.modality}</span>
                          )}
                        </div>
                        <p className="whitespace-pre-wrap">{msg.text}</p>
                      </div>
                    </div>
                  ))}
                  {processing && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing...
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
