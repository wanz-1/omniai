"use client";

import { useState } from "react";
import {
  Folder,
  FolderOpen,
  FileCode,
  FileJson,
  FileText,
  Plus,
  Trash2,
  MoreHorizontal,
  ChevronRight,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface FileNode {
  path: string;
  content?: string;
  type?: "file" | "folder";
  children?: FileNode[];
}

interface FileTreeProps {
  files: FileNode[];
  activeFile: string | null;
  onFileSelect: (path: string) => void;
  onFileDelete: (path: string) => void;
  onFileAdd: (parentPath: string) => void;
  className?: string;
}

function getFileIcon(path: string) {
  const ext = path.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "ts":
    case "tsx":
    case "js":
    case "jsx":
      return FileCode;
    case "json":
      return FileJson;
    case "md":
    case "txt":
    case "py":
    case "css":
    case "html":
      return FileText;
    default:
      return FileCode;
  }
}

function TreeNode({
  node,
  depth,
  activeFile,
  onFileSelect,
  onFileDelete,
  onFileAdd,
}: {
  node: FileNode;
  depth: number;
  activeFile: string | null;
  onFileSelect: (path: string) => void;
  onFileDelete: (path: string) => void;
  onFileAdd: (parentPath: string) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const [showActions, setShowActions] = useState(false);
  const isFolder = node.type === "folder" || node.children?.length !== undefined;
  const isActive = activeFile === node.path;
  const Icon = isFolder ? (expanded ? FolderOpen : Folder) : getFileIcon(node.path);

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-1 px-2 py-1 text-xs rounded cursor-pointer group hover:bg-muted/50",
          isActive && "bg-primary/10 text-primary"
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => {
          if (isFolder) setExpanded(!expanded);
          else onFileSelect(node.path);
        }}
        onMouseEnter={() => setShowActions(true)}
        onMouseLeave={() => setShowActions(false)}
      >
        {isFolder && (
          <span className="text-muted-foreground">
            {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </span>
        )}
        <Icon className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
        <span className="truncate flex-1">{node.path.split("/").pop() || node.path}</span>
        {showActions && isFolder && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onFileAdd(node.path);
            }}
            className="p-0.5 hover:bg-muted rounded opacity-0 group-hover:opacity-100"
          >
            <Plus className="w-3 h-3" />
          </button>
        )}
        {showActions && !isFolder && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onFileDelete(node.path);
            }}
            className="p-0.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-muted-foreground hover:text-red-500 opacity-0 group-hover:opacity-100"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        )}
      </div>
      {isFolder && expanded && node.children?.map((child, idx) => (
        <TreeNode
          key={child.path || idx}
          node={child}
          depth={depth + 1}
          activeFile={activeFile}
          onFileSelect={onFileSelect}
          onFileDelete={onFileDelete}
          onFileAdd={onFileAdd}
        />
      ))}
    </div>
  );
}

export function FileTree({
  files,
  activeFile,
  onFileSelect,
  onFileDelete,
  onFileAdd,
  className,
}: FileTreeProps) {
  return (
    <div className={cn("text-sm", className)}>
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <span className="text-xs font-medium text-muted-foreground">Files</span>
        <button
          onClick={() => onFileAdd("/")}
          className="p-0.5 hover:bg-muted rounded"
          title="Add file"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="py-1">
        {files.length === 0 ? (
          <p className="text-xs text-muted-foreground px-3 py-4 text-center">No files yet</p>
        ) : (
          files.map((node, idx) => (
            <TreeNode
              key={node.path || idx}
              node={node}
              depth={0}
              activeFile={activeFile}
              onFileSelect={onFileSelect}
              onFileDelete={onFileDelete}
              onFileAdd={onFileAdd}
            />
          ))
        )}
      </div>
    </div>
  );
}
