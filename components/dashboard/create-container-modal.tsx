"use client"

import { useState } from "react"
import { X, Box, HardDrive, Cpu, Users, Folder, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"

interface CreateContainerModalProps {
  onClose: () => void
  onCreate: (name: string) => void
}

export function CreateContainerModal({ onClose, onCreate }: CreateContainerModalProps) {
  const [name, setName] = useState("")
  const [rootfs, setRootfs] = useState("/tmp/alpine-rootfs")
  const [memoryLimit, setMemoryLimit] = useState("256")
  const [cpuPercent, setCpuPercent] = useState("50")
  const [pidsMax, setPidsMax] = useState("100")
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (name.trim()) {
      onCreate(name.trim())
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-background/90 backdrop-blur-xl"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-card border border-border/50 rounded-2xl w-full max-w-xl max-h-[90vh] overflow-hidden shadow-2xl shadow-black/50 animate-in fade-in-0 zoom-in-95 duration-200">
        {/* Top Gradient */}
        <div className="h-1 bg-gradient-to-r from-purple-500 via-cyan-500 to-blue-500" />
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Box className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-foreground">Create Container</h2>
              <p className="text-sm text-muted-foreground">Configure your new container</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-secondary/80 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Container Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className="text-sm font-medium text-foreground">
              Container Name <span className="text-red-400">*</span>
            </Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my-container"
              className="bg-secondary/50 border-border/50 focus:border-primary/50"
              required
            />
            <p className="text-xs text-muted-foreground">
              Use lowercase letters, numbers, and hyphens only
            </p>
          </div>

          {/* Root Filesystem */}
          <div className="space-y-2">
            <Label htmlFor="rootfs" className="text-sm font-medium text-foreground flex items-center gap-2">
              <Folder className="w-4 h-4 text-muted-foreground" />
              Root Filesystem
            </Label>
            <Input
              id="rootfs"
              value={rootfs}
              onChange={(e) => setRootfs(e.target.value)}
              placeholder="/tmp/alpine-rootfs"
              className="bg-secondary/50 border-border/50 focus:border-primary/50 font-mono text-sm"
            />
          </div>

          {/* Advanced Options Toggle */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronDown className={cn(
              "w-4 h-4 transition-transform",
              showAdvanced && "rotate-180"
            )} />
            Advanced Options
          </button>

          {/* Advanced Options */}
          {showAdvanced && (
            <div className="space-y-4 pt-2 border-t border-border/50">
              {/* Resource Limits Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Memory */}
                <div className="space-y-2">
                  <Label htmlFor="memory" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <HardDrive className="w-4 h-4 text-cyan-400" />
                    Memory (MB)
                  </Label>
                  <Input
                    id="memory"
                    type="number"
                    value={memoryLimit}
                    onChange={(e) => setMemoryLimit(e.target.value)}
                    className="bg-secondary/50 border-border/50 focus:border-primary/50 font-mono"
                  />
                </div>

                {/* CPU */}
                <div className="space-y-2">
                  <Label htmlFor="cpu" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-orange-400" />
                    CPU (%)
                  </Label>
                  <Input
                    id="cpu"
                    type="number"
                    value={cpuPercent}
                    onChange={(e) => setCpuPercent(e.target.value)}
                    className="bg-secondary/50 border-border/50 focus:border-primary/50 font-mono"
                  />
                </div>

                {/* PIDs */}
                <div className="space-y-2">
                  <Label htmlFor="pids" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <Users className="w-4 h-4 text-purple-400" />
                    Max PIDs
                  </Label>
                  <Input
                    id="pids"
                    type="number"
                    value={pidsMax}
                    onChange={(e) => setPidsMax(e.target.value)}
                    className="bg-secondary/50 border-border/50 focus:border-primary/50 font-mono"
                  />
                </div>
              </div>

              {/* Info Box */}
              <div className="bg-secondary/30 rounded-lg p-4 border border-border/30">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Resource limits help prevent containers from consuming excessive system resources. 
                  The defaults are suitable for most lightweight workloads.
                </p>
              </div>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="p-6 border-t border-border/50 bg-secondary/20 flex items-center justify-end gap-3">
          <Button 
            type="button" 
            variant="ghost" 
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            Cancel
          </Button>
          <Button 
            type="submit"
            onClick={handleSubmit}
            disabled={!name.trim()}
            className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white shadow-lg shadow-cyan-500/25"
          >
            Create Container
          </Button>
        </div>
      </div>
    </div>
  )
}
