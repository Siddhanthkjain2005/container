"use client"

import { Play, Square, Trash2, Activity, Cpu, MemoryStick, Terminal, MoreVertical } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface Container {
  id: string
  name: string
  state: string
  pid: number
  cpu: number
  memory: number
  memoryBytes: number
  memoryLimit: number
  pids: number
}

interface ContainerCardProps {
  container: Container
  viewMode: "grid" | "list"
  onStart: () => void
  onStop: () => void
  onDelete: () => void
}

const stateConfig = {
  running: {
    color: "text-emerald-400",
    bg: "bg-emerald-500/15",
    border: "border-emerald-500/30",
    gradient: "from-emerald-500 to-teal-500",
    shadow: "shadow-emerald-500/20",
  },
  created: {
    color: "text-cyan-400",
    bg: "bg-cyan-500/15",
    border: "border-cyan-500/30",
    gradient: "from-cyan-500 to-blue-500",
    shadow: "shadow-cyan-500/20",
  },
  stopped: {
    color: "text-zinc-400",
    bg: "bg-zinc-500/15",
    border: "border-zinc-500/30",
    gradient: "from-zinc-500 to-zinc-600",
    shadow: "shadow-zinc-500/20",
  },
}

export function ContainerCard({ container, viewMode, onStart, onStop, onDelete }: ContainerCardProps) {
  const config = stateConfig[container.state as keyof typeof stateConfig] || stateConfig.stopped
  const isRunning = container.state === "running"

  if (viewMode === "list") {
    return (
      <div className={cn(
        "bg-card rounded-xl border border-border/50 p-4 flex items-center gap-4 hover:border-border transition-all group",
        isRunning && "hover:shadow-lg hover:shadow-emerald-500/5"
      )}>
        {/* Status Dot */}
        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", config.bg)}>
          <Activity className={cn("w-5 h-5", config.color)} />
        </div>
        
        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-foreground truncate">{container.name}</h3>
            <span className={cn(
              "px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide",
              config.bg, config.color, config.border, "border"
            )}>
              {container.state}
            </span>
          </div>
          <p className="text-xs text-muted-foreground font-mono">{container.id}</p>
        </div>

        {/* Metrics */}
        <div className="hidden md:flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-orange-400" />
            <span className="text-sm font-mono font-semibold text-foreground">{container.cpu.toFixed(1)}%</span>
          </div>
          <div className="flex items-center gap-2">
            <MemoryStick className="w-4 h-4 text-cyan-400" />
            <span className="text-sm font-mono font-semibold text-foreground">{container.memory.toFixed(1)}%</span>
          </div>
          <div className="text-sm font-mono text-muted-foreground">
            {container.pids} PIDs
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {isRunning ? (
            <Button variant="ghost" size="sm" className="text-red-400 hover:text-red-300 hover:bg-red-500/10" onClick={onStop}>
              <Square className="w-4 h-4 mr-1" />
              Stop
            </Button>
          ) : (
            <Button variant="ghost" size="sm" className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10" onClick={onStart}>
              <Play className="w-4 h-4 mr-1" />
              Start
            </Button>
          )}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Terminal className="w-4 h-4 mr-2" />
                Open Terminal
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Activity className="w-4 h-4 mr-2" />
                View Logs
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-400 focus:text-red-400" onClick={onDelete}>
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    )
  }

  return (
    <div className={cn(
      "bg-card rounded-2xl border border-border/50 overflow-hidden transition-all duration-300 hover:-translate-y-1 group",
      isRunning && "hover:shadow-xl hover:shadow-emerald-500/10 hover:border-emerald-500/20"
    )}>
      {/* Top Gradient */}
      <div className={cn("h-1 bg-gradient-to-r", config.gradient)} />
      
      {/* Header */}
      <div className="p-5 border-b border-border/50">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-bold text-lg text-foreground truncate">{container.name}</h3>
            </div>
            <p className="text-xs text-muted-foreground font-mono bg-secondary/50 px-2 py-1 rounded inline-block">
              {container.id}
            </p>
          </div>
          
          <span className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wide border shrink-0",
            config.bg, config.color, config.border
          )}>
            <span className={cn(
              "w-1.5 h-1.5 rounded-full",
              config.color.replace("text-", "bg-"),
              isRunning && "animate-pulse-glow"
            )} />
            {container.state}
          </span>
        </div>
      </div>

      {/* Metrics */}
      <div className="p-5 space-y-4">
        {/* CPU */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-orange-400" />
              <span className="text-sm font-medium text-muted-foreground">CPU</span>
            </div>
            <span className="text-sm font-bold font-mono text-foreground">
              {container.cpu.toFixed(1)}%
            </span>
          </div>
          <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-orange-500 to-amber-500 rounded-full transition-all duration-500 relative"
              style={{ width: `${Math.min(container.cpu, 100)}%` }}
            >
              {isRunning && <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />}
            </div>
          </div>
        </div>

        {/* Memory */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MemoryStick className="w-4 h-4 text-cyan-400" />
              <span className="text-sm font-medium text-muted-foreground">Memory</span>
            </div>
            <span className="text-sm font-bold font-mono text-foreground">
              {container.memory.toFixed(1)}%
            </span>
          </div>
          <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500 relative"
              style={{ width: `${Math.min(container.memory, 100)}%` }}
            >
              {isRunning && <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />}
            </div>
          </div>
        </div>

        {/* PID Count */}
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-muted-foreground">Processes</span>
          <span className="text-sm font-bold font-mono text-purple-400">{container.pids}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="px-5 py-4 bg-secondary/30 border-t border-border/50 flex items-center gap-2">
        <Button
          variant="ghost"
          className={cn(
            "flex-1 gap-2",
            isRunning 
              ? "text-purple-400 hover:text-purple-300 hover:bg-purple-500/10"
              : "text-muted-foreground"
          )}
          disabled={!isRunning}
        >
          <Terminal className="w-4 h-4" />
          Terminal
        </Button>
        
        {isRunning ? (
          <Button
            variant="ghost"
            className="flex-1 gap-2 text-red-400 hover:text-red-300 hover:bg-red-500/10"
            onClick={onStop}
          >
            <Square className="w-4 h-4" />
            Stop
          </Button>
        ) : (
          <Button
            variant="ghost"
            className="flex-1 gap-2 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
            onClick={onStart}
          >
            <Play className="w-4 h-4" />
            Start
          </Button>
        )}
        
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-red-400 hover:bg-red-500/10"
          onClick={onDelete}
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}
