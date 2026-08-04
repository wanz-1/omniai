"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";

interface CodeEditorProps {
  code: string;
  onChange: (code: string) => void;
  language?: string;
  readonly?: boolean;
  className?: string;
  label?: string;
}

// Simple syntax highlighting using regex patterns
function highlightCode(code: string, language: string): string {
  let highlighted = code
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  const patterns: Record<string, RegExp[]> = {
    python: [
      /(import|from|def|class|return|if|elif|else|for|while|try|except|with|as|pass|break|continue|and|or|not|in|is|None|True|False|async|await)\b/g,
      /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g,
      /(#.*$)/gm,
      /(\b\d+\.?\d*\b)/g,
      /(\b[A-Z][a-zA-Z0-9_]*\b)/g,
    ],
    javascript: [
      /(const|let|var|function|return|if|else|for|while|try|catch|async|await|import|export|from|class|new|this|throw|switch|case|break|continue|typeof|instanceof)\b/g,
      /`(?:[^`\\]|\\.)*`|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/g,
      /(\/\/.*$)/gm,
      /(\b\d+\.?\d*\b)/g,
    ],
    typescript: [
      /(const|let|var|function|return|if|else|for|while|try|catch|async|await|import|export|from|class|new|this|interface|type|enum|extends|implements|typeof|instanceof|as|keyof)\b/g,
      /`(?:[^`\\]|\\.)*`|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/g,
      /(\/\/.*$)/gm,
      /(\b\d+\.?\d*\b)/g,
      /(:|=>)/g,
    ],
    default: [
      /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g,
      /(\/\/.*$)/gm,
      /(\b\d+\.?\d*\b)/g,
    ],
  };

  const langPatterns = patterns[language] || patterns.default;

  const classes = ["text-blue-600 dark:text-blue-400", "text-green-600 dark:text-green-400", "text-gray-400 dark:text-gray-500", "text-orange-600 dark:text-orange-400", "text-purple-600 dark:text-purple-400"];

  langPatterns.forEach((pattern, idx) => {
    highlighted = highlighted.replace(pattern, (match) => {
      return `<span class="${classes[idx % classes.length]}">${match}</span>`;
    });
  });

  return highlighted;
}

export function CodeEditor({
  code,
  onChange,
  language = "python",
  readonly = false,
  className,
  label,
}: CodeEditorProps) {
  const lineCount = useMemo(() => code.split("\n").length, [code]);
  const lines = useMemo(() => Array.from({ length: lineCount }, (_, i) => i + 1), [lineCount]);

  return (
    <div className={cn("flex flex-col", className)}>
      {label && (
        <div className="text-sm font-medium text-muted-foreground mb-1.5 px-1">{label}</div>
      )}
      <div className="flex-1 relative rounded-lg border border-border overflow-hidden bg-[#1E1E1E] dark:bg-[#1E1E1E] bg-muted font-mono text-sm">
        <div className="flex h-full">
          <div className="select-none text-right px-3 py-3 text-gray-500 text-xs leading-5 border-r border-gray-800 bg-[#252526] min-w-[44px]">
            {lines.map((n) => (
              <div key={n}>{n}</div>
            ))}
          </div>
          {readonly ? (
            <pre className="flex-1 p-3 m-0 overflow-auto text-xs leading-5 text-gray-200 whitespace-pre-wrap break-all">
              <code dangerouslySetInnerHTML={{ __html: highlightCode(code, language) }} />
            </pre>
          ) : (
            <textarea
              value={code}
              onChange={(e) => onChange(e.target.value)}
              className="flex-1 p-3 m-0 bg-transparent text-xs leading-5 text-gray-200 resize-none outline-none border-none font-mono"
              spellCheck={false}
              style={{ tabSize: 2 }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
