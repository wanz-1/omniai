"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { Mic, Square, Play, Loader2, Trash2 } from "lucide-react";

interface VoiceRecorderProps {
  onRecordingComplete: (blob: Blob, durationMs: number) => void;
  isProcessing?: boolean;
  disabled?: boolean;
}

export function VoiceRecorder({ onRecordingComplete, isProcessing, disabled }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const startTimeRef = useRef(0);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      startTimeRef.current = Date.now();

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setRecordedBlob(blob);
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setDuration(0);

      timerRef.current = setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);
    } catch {
      console.error("Microphone access denied");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
  }, []);

  const playRecording = useCallback(() => {
    if (!recordedBlob) return;
    const url = URL.createObjectURL(recordedBlob);
    const audio = new Audio(url);
    audioRef.current = audio;
    setIsPlaying(true);
    audio.onended = () => {
      setIsPlaying(false);
      URL.revokeObjectURL(url);
    };
    audio.play();
  }, [recordedBlob]);

  const clearRecording = useCallback(() => {
    setRecordedBlob(null);
    setDuration(0);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
  }, []);

  const handleSend = useCallback(() => {
    if (recordedBlob) {
      onRecordingComplete(recordedBlob, duration * 1000);
      clearRecording();
    }
  }, [recordedBlob, duration, onRecordingComplete, clearRecording]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex items-center gap-2">
      {!isRecording && !recordedBlob && (
        <Button
          variant="ghost"
          size="sm"
          onClick={startRecording}
          disabled={disabled}
          title="Start recording"
        >
          <Mic className="w-4 h-4" />
        </Button>
      )}

      {isRecording && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-red-500 animate-pulse">Recording {formatTime(duration)}</span>
          <Button variant="ghost" size="sm" onClick={stopRecording}>
            <Square className="w-4 h-4 fill-red-500 text-red-500" />
          </Button>
        </div>
      )}

      {recordedBlob && !isRecording && (
        <>
          <span className="text-sm text-muted-foreground">{formatTime(duration)}</span>
          <Button variant="ghost" size="sm" onClick={playRecording}>
            {isPlaying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          </Button>
          <Button variant="ghost" size="sm" onClick={clearRecording}>
            <Trash2 className="w-4 h-4" />
          </Button>
          <Button size="sm" onClick={handleSend} isLoading={isProcessing} disabled={disabled}>
            Send
          </Button>
        </>
      )}
    </div>
  );
}
