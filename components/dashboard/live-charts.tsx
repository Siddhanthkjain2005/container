"use client"

import { Area, AreaChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts"
import { ChartContainer, ChartTooltipContent } from "@/components/ui/chart"
import { Cpu, MemoryStick, ArrowRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface LiveChartsProps {
  metricsHistory: Array<{ timestamp: number; cpu: number; memory: number }>
  currentCpu: number
  currentMemory: number
}

const chartConfig = {
  cpu: {
    label: "CPU",
    color: "hsl(35 100% 50%)",
  },
  memory: {
    label: "Memory",
    color: "hsl(196 100% 50%)",
  },
}

export function LiveCharts({ metricsHistory, currentCpu, currentMemory }: LiveChartsProps) {
  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-400 animate-pulse-glow" />
          <h2 className="text-xl font-bold text-foreground">Live Metrics</h2>
        </div>
        <button className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors">
          View Details
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Main Chart */}
      <div className="bg-card rounded-2xl border border-border/50 p-6 mb-4 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-cyan-500 to-blue-500" />
        
        {/* Chart Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-lg font-bold text-foreground">Resource Utilization</h3>
            <p className="text-sm text-muted-foreground">Real-time system metrics across all containers</p>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-400 shadow-lg shadow-orange-400/40" />
              <span className="text-sm text-muted-foreground">CPU</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-cyan-400 shadow-lg shadow-cyan-400/40" />
              <span className="text-sm text-muted-foreground">Memory</span>
            </div>
          </div>
        </div>

        {/* Current Values */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <div className="flex flex-col">
            <span className="text-3xl font-black font-mono text-orange-400">
              {currentCpu.toFixed(1)}%
            </span>
            <span className="text-xs text-muted-foreground uppercase tracking-wide mt-1">CPU Usage</span>
          </div>
          <div className="flex flex-col">
            <span className="text-3xl font-black font-mono text-cyan-400">
              {currentMemory.toFixed(1)}%
            </span>
            <span className="text-xs text-muted-foreground uppercase tracking-wide mt-1">Memory Usage</span>
          </div>
          <div className="flex flex-col">
            <span className="text-3xl font-black font-mono text-purple-400">
              1.2 GB
            </span>
            <span className="text-xs text-muted-foreground uppercase tracking-wide mt-1">Total Allocated</span>
          </div>
        </div>

        {/* Chart */}
        <div className="h-48">
          <ChartContainer config={chartConfig}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metricsHistory} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
                <defs>
                  <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(35 100% 50%)" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="hsl(35 100% 50%)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="memGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(196 100% 50%)" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="hsl(196 100% 50%)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 13% 15%)" vertical={false} />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(val) => new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  stroke="hsl(215 20% 40%)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis 
                  domain={[0, 100]} 
                  stroke="hsl(215 20% 40%)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(val) => `${val}%`}
                />
                <Tooltip 
                  content={<ChartTooltipContent />}
                  cursor={{ stroke: 'hsl(215 20% 30%)', strokeDasharray: '4 4' }}
                />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stroke="hsl(35 100% 50%)"
                  strokeWidth={2}
                  fill="url(#cpuGradient)"
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stroke="hsl(196 100% 50%)"
                  strokeWidth={2}
                  fill="url(#memGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>
      </div>

      {/* Dual Chart Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* CPU Panel */}
        <div className="bg-card rounded-xl border border-border/50 p-5 relative overflow-hidden group hover:border-orange-500/30 transition-colors">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-orange-500 to-amber-500" />
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-orange-400" />
              <span className="text-sm font-semibold text-muted-foreground">CPU</span>
            </div>
            <span className="text-xl font-black font-mono text-orange-400">
              {currentCpu.toFixed(1)}%
            </span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-orange-500 to-amber-500 rounded-full transition-all duration-500 relative"
              style={{ width: `${Math.min(currentCpu, 100)}%` }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer" />
            </div>
          </div>
        </div>

        {/* Memory Panel */}
        <div className="bg-card rounded-xl border border-border/50 p-5 relative overflow-hidden group hover:border-cyan-500/30 transition-colors">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-cyan-500 to-blue-500" />
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <MemoryStick className="w-4 h-4 text-cyan-400" />
              <span className="text-sm font-semibold text-muted-foreground">Memory</span>
            </div>
            <span className="text-xl font-black font-mono text-cyan-400">
              {currentMemory.toFixed(1)}%
            </span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500 relative"
              style={{ width: `${Math.min(currentMemory, 100)}%` }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer" />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
