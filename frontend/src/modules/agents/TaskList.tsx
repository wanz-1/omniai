"use client";

import { useState } from "react";
import { ListTodo, Plus, Play, Loader2, CheckCircle, XCircle, Clock, AlertTriangle, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

interface Task {
  id: string;
  title: string;
  description?: string;
  status: string;
  priority: number;
  progress: number;
  result?: string;
  error?: string;
  created_at: string;
}

interface TaskListProps {
  tasks: Task[];
  onAdd: (data: any) => void;
  onExecute: (taskId: string) => void;
  isExecuting?: string | null;
  className?: string;
}

const statusConfig: Record<string, { icon: any; color: string }> = {
  pending: { icon: Clock, color: "text-gray-400" },
  planning: { icon: AlertTriangle, color: "text-blue-500" },
  executing: { icon: Loader2, color: "text-purple-500" },
  completed: { icon: CheckCircle, color: "text-green-500" },
  failed: { icon: XCircle, color: "text-red-500" },
  cancelled: { icon: XCircle, color: "text-gray-400" },
};

export function TaskList({ tasks, onAdd, onExecute, isExecuting, className }: TaskListProps) {
  const [showAdd, setShowAdd] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const handleAdd = () => {
    if (!title.trim()) return;
    onAdd({ title: title.trim(), description: description.trim() || undefined });
    setTitle("");
    setDescription("");
    setShowAdd(false);
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex items-center justify-between p-3 border-b border-border">
        <h3 className="text-sm font-medium flex items-center gap-2">
          <ListTodo className="w-4 h-4" />
          Tasks ({tasks.length})
        </h3>
        <Button variant="outline" size="sm" onClick={() => setShowAdd(!showAdd)}>
          <Plus className="w-3.5 h-3.5 mr-1" /> New Task
        </Button>
      </div>

      {showAdd && (
        <div className="p-3 border-b border-border space-y-2 bg-muted/20">
          <input value={title} onChange={(e) => setTitle(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleAdd()} placeholder="Task title" className="w-full px-2 py-1.5 rounded border border-border bg-background text-xs" />
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} placeholder="Description (optional)" className="w-full px-2 py-1.5 rounded border border-border bg-background text-xs resize-y" />
          <div className="flex gap-2">
            <Button size="sm" onClick={handleAdd} disabled={!title.trim()} className="flex-1">Add Task</Button>
            <Button variant="ghost" size="sm" onClick={() => setShowAdd(false)}>Cancel</Button>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {tasks.length === 0 && !showAdd && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground p-4">
            <ListTodo className="w-8 h-8 mb-2 opacity-40" />
            <p className="text-xs">No tasks yet</p>
          </div>
        )}
        {tasks.map((task) => {
          const config = statusConfig[task.status] || { icon: Clock, color: "text-gray-400" };
          const Icon = config.icon;
          return (
            <div key={task.id} className="flex items-start gap-2 p-2.5 rounded-lg border border-border bg-card hover:border-primary/30 transition-colors">
              <Icon className={cn("w-4 h-4 mt-0.5 shrink-0", config.color, task.status === "executing" && "animate-spin")} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium">{task.title}</span>
                  <span className={cn("text-[10px] px-1 py-0.5 rounded", task.status === "completed" ? "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400" : task.status === "failed" ? "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400" : "bg-muted text-muted-foreground")}>
                    {task.status}
                  </span>
                  {task.priority >= 3 && <AlertTriangle className="w-3 h-3 text-amber-500" />}
                </div>
                {task.description && <p className="text-[10px] text-muted-foreground mt-0.5">{task.description}</p>}
                {task.status === "executing" && (
                  <div className="mt-1.5 w-full h-1 rounded-full bg-muted overflow-hidden">
                    <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${task.progress * 100}%` }} />
                  </div>
                )}
                {task.result && <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">{task.result}</p>}
                {task.error && <p className="text-[10px] text-red-500 mt-1">{task.error}</p>}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {task.status === "pending" && (
                  <button onClick={() => onExecute(task.id)} disabled={isExecuting === task.id} className="p-1 rounded hover:bg-primary/10 text-muted-foreground hover:text-primary transition-colors">
                    {isExecuting === task.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
