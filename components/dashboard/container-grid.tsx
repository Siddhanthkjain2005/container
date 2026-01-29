"use client"

import { ContainerCard } from "./container-card"
import { EmptyState } from "./empty-state"
import { Filter, LayoutGrid, List, ArrowUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { cn } from "@/lib/utils"

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

interface ContainerGridProps {
  containers: Container[]
  onStart: (id: string) => void
  onStop: (id: string) => void
  onDelete: (id: string) => void
  onCreateNew: () => void
}

type ViewMode = "grid" | "list"
type SortBy = "name" | "cpu" | "memory" | "state"

export function ContainerGrid({ containers, onStart, onStop, onDelete, onCreateNew }: ContainerGridProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("grid")
  const [sortBy, setSortBy] = useState<SortBy>("state")
  const [filterState, setFilterState] = useState<string>("all")

  const filteredContainers = containers.filter(c => 
    filterState === "all" || c.state === filterState
  )

  const sortedContainers = [...filteredContainers].sort((a, b) => {
    switch (sortBy) {
      case "name":
        return a.name.localeCompare(b.name)
      case "cpu":
        return b.cpu - a.cpu
      case "memory":
        return b.memory - a.memory
      case "state":
        const stateOrder = { running: 0, created: 1, stopped: 2 }
        return (stateOrder[a.state as keyof typeof stateOrder] ?? 3) - (stateOrder[b.state as keyof typeof stateOrder] ?? 3)
      default:
        return 0
    }
  })

  if (containers.length === 0) {
    return <EmptyState onCreateNew={onCreateNew} />
  }

  return (
    <section>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-foreground">Containers</h2>
          <p className="text-sm text-muted-foreground">{containers.length} containers, {containers.filter(c => c.state === "running").length} running</p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Filter */}
          <div className="flex items-center bg-secondary rounded-lg p-1">
            {["all", "running", "created", "stopped"].map((state) => (
              <button
                key={state}
                onClick={() => setFilterState(state)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium rounded-md capitalize transition-all",
                  filterState === state 
                    ? "bg-card text-foreground shadow-sm" 
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {state}
              </button>
            ))}
          </div>

          {/* Sort */}
          <Button 
            variant="ghost" 
            size="sm" 
            className="gap-2 text-muted-foreground"
            onClick={() => {
              const sorts: SortBy[] = ["state", "name", "cpu", "memory"]
              const currentIndex = sorts.indexOf(sortBy)
              setSortBy(sorts[(currentIndex + 1) % sorts.length])
            }}
          >
            <ArrowUpDown className="w-4 h-4" />
            <span className="hidden sm:inline capitalize">{sortBy}</span>
          </Button>
          
          {/* View Toggle */}
          <div className="flex items-center bg-secondary rounded-lg p-1">
            <button
              onClick={() => setViewMode("grid")}
              className={cn(
                "p-2 rounded-md transition-all",
                viewMode === "grid" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={cn(
                "p-2 rounded-md transition-all",
                viewMode === "list" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              )}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Container Grid/List */}
      <div className={cn(
        viewMode === "grid" 
          ? "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" 
          : "flex flex-col gap-3"
      )}>
        {sortedContainers.map((container) => (
          <ContainerCard
            key={container.id}
            container={container}
            viewMode={viewMode}
            onStart={() => onStart(container.id)}
            onStop={() => onStop(container.id)}
            onDelete={() => onDelete(container.id)}
          />
        ))}
      </div>
    </section>
  )
}
