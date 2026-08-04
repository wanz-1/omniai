"use client";

import { useCallback, useEffect, useRef } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import Highlight from "@tiptap/extension-highlight";
import Underline from "@tiptap/extension-underline";
import { cn } from "@/lib/utils";

interface DocumentEditorProps {
  content: string;
  onChange: (html: string) => void;
  readonly?: boolean;
  placeholder?: string;
  className?: string;
  label?: string;
  highlightChanges?: { from: string; to: string } | null;
}

export function DocumentEditor({
  content,
  onChange,
  readonly = false,
  placeholder = "Start writing...",
  className,
  label,
  highlightChanges,
}: DocumentEditorProps) {
  const prevContentRef = useRef(content);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        history: {
          depth: 100,
        },
      }),
      Placeholder.configure({ placeholder }),
      Highlight,
      Underline,
    ],
    content,
    editable: !readonly,
    onUpdate: ({ editor }: { editor: any }) => {
      onChange(editor.getHTML());
    },
  });

  useEffect(() => {
    if (editor && content !== prevContentRef.current) {
      prevContentRef.current = content;
      if (editor.getHTML() !== content) {
        editor.commands.setContent(content, false);
      }
    }
  }, [content, editor]);

  const toolbarItems = readonly
    ? []
    : [
        { icon: "B", action: () => editor?.chain().focus().toggleBold().run(), active: editor?.isActive("bold"), label: "Bold" },
        { icon: "I", action: () => editor?.chain().focus().toggleItalic().run(), active: editor?.isActive("italic"), label: "Italic" },
        { icon: "U", action: () => editor?.chain().focus().toggleUnderline().run(), active: editor?.isActive("underline"), label: "Underline" },
        { icon: "H", action: () => editor?.chain().focus().toggleHighlight().run(), active: editor?.isActive("highlight"), label: "Highlight" },
        { icon: "H1", action: () => editor?.chain().focus().toggleHeading({ level: 1 }).run(), active: editor?.isActive("heading", { level: 1 }), label: "Heading 1" },
        { icon: "H2", action: () => editor?.chain().focus().toggleHeading({ level: 2 }).run(), active: editor?.isActive("heading", { level: 2 }), label: "Heading 2" },
        { icon: "•", action: () => editor?.chain().focus().toggleBulletList().run(), active: editor?.isActive("bulletList"), label: "Bullet List" },
        { icon: "1.", action: () => editor?.chain().focus().toggleOrderedList().run(), active: editor?.isActive("orderedList"), label: "Ordered List" },
      ];

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {label && (
        <div className="text-sm font-medium text-muted-foreground mb-2 px-1">{label}</div>
      )}
      {!readonly && (
        <div className="flex items-center gap-1 p-2 border-b border-border bg-muted/30 rounded-t-lg flex-wrap">
          {toolbarItems.map((item) => (
            <button
              key={item.label}
              onClick={item.action}
              title={item.label}
              className={cn(
                "w-8 h-8 flex items-center justify-center rounded text-sm font-medium transition-colors hover:bg-muted",
                item.active && "bg-primary/10 text-primary"
              )}
            >
              {item.icon}
            </button>
          ))}
        </div>
      )}
      <div
        className={cn(
          "flex-1 overflow-y-auto p-4 prose prose-sm max-w-none",
          readonly && "bg-muted/20"
        )}
      >
        <EditorContent editor={editor} className="outline-none min-h-full" />
      </div>
    </div>
  );
}
