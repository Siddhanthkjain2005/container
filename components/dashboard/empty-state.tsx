"use client"

import { Box, Plus, Rocket } from "lucide-react"
import { Button } from "@/components/ui/button"

interface EmptyStateProps {
  onCreateNew: () => void
}

export function EmptyState({ onCreateNew }: EmptyStateProps) {
  return (
    <div className="bg-card rounded-2xl border-2 border-dashed border-border/50 p-12 text-center">
      <div className="mx-auto w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center mb-6 animate-float">
        <Box className="w-10 h-10 text-cyan-400" />
      </div>
      
      <h3 className="text-2xl font-bold text-foreground mb-2">No Containers Yet</h3>
      <p className="text-muted-foreground mb-8 max-w-md mx-auto">
        Get started by creating your first container. Deploy applications in isolated environments with resource limits.
      </p>
      
      <div className="flex items-center justify-center gap-4">
        <Button 
          onClick={onCreateNew}
          className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white shadow-lg shadow-cyan-500/25"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Container
        </Button>
        
        <Button variant="outline" className="border-border/50">
          <Rocket className="w-4 h-4 mr-2" />
          Quick Start
        </Button>
      </div>
    </div>
  )
}
