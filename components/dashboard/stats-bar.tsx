"use client"

import { Box, Cpu, HardDrive, Activity, TrendingUp, TrendingDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface StatsBarProps {
  containerCount: number
  runningCount: number
  avgCpu: number
  totalPids: number
}

const stats = [
  {
    id: "containers",
    label: "Total Containers",
    icon: Box,
    color: "cyan",
    gradient: "from-cyan-500 to-blue-500",
    bgGlow: "shadow-cyan-500/20",
    trend: "+2 this week",
    trendUp: true,
  },
  {
    id: "running",
    label: "Running",
    icon: Activity,
    color: "emerald",
    gradient: "from-emerald-500 to-teal-500",
    bgGlow: "shadow-emerald-500/20",
    trend: "98% uptime",
    trendUp: true,
  },
  {
    id: "cpu",
    label: "Avg CPU Usage",
    icon: Cpu,
    color: "orange",
    gradient: "from-orange-500 to-amber-500",
    bgGlow: "shadow-orange-500/20",
    trend: "-5% vs last hour",
    trendUp: false,
  },
  {
    id: "pids",
    label: "Total Processes",
    icon: HardDrive,
    color: "purple",
    gradient: "from-purple-500 to-violet-500",
    bgGlow: "shadow-purple-500/20",
    trend: "+12 active",
    trendUp: true,
  },
]

const colorMap: Record<string, { text: string; bg: string; shadow: string }> = {
  cyan: { text: "text-cyan-400", bg: "bg-cyan-500/15", shadow: "shadow-cyan-500/40" },
  emerald: { text: "text-emerald-400", bg: "bg-emerald-500/15", shadow: "shadow-emerald-500/40" },
  orange: { text: "text-orange-400", bg: "bg-orange-500/15", shadow: "shadow-orange-500/40" },
  purple: { text: "text-purple-400", bg: "bg-purple-500/15", shadow: "shadow-purple-500/40" },
}

export function StatsBar({ containerCount, runningCount, avgCpu, totalPids }: StatsBarProps) {
  const values: Record<string, string | number> = {
    containers: containerCount,
    running: runningCount,
    cpu: `${avgCpu.toFixed(1)}%`,
    pids: totalPids,
  }

  return (
    <section className="mb-8">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        {stats.map((stat) => {
          const colors = colorMap[stat.color]
          
          return (
            <div
              key={stat.id}
              className="group relative bg-card rounded-2xl p-5 border border-border/50 hover:border-border transition-all duration-300 hover:-translate-y-1 overflow-hidden"
            >
              {/* Top gradient line */}
              <div className={cn("absolute top-0 left-0 right-0 h-1 bg-gradient-to-r", stat.gradient)} />
              
              {/* Background glow on hover */}
              <div className={cn(
                "absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl",
                colors.bg
              )} />
              
              <div className="relative flex items-start justify-between">
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                    {stat.label}
                  </span>
                  <span className={cn(
                    "text-3xl lg:text-4xl font-black font-mono tracking-tight",
                    colors.text
                  )}>
                    {values[stat.id]}
                  </span>
                  <div className="flex items-center gap-1 mt-2">
                    {stat.trendUp ? (
                      <TrendingUp className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <TrendingDown className="w-3 h-3 text-orange-400" />
                    )}
                    <span className="text-xs text-muted-foreground">{stat.trend}</span>
                  </div>
                </div>
                
                <div className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300",
                  colors.bg,
                  "group-hover:scale-110"
                )}>
                  <stat.icon className={cn("w-6 h-6", colors.text)} />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
