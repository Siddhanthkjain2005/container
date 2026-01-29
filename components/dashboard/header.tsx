"use client"

import { Plus, Bell, Search, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

interface HeaderProps {
  isConnected: boolean
  onCreateContainer: () => void
}

export function Header({ isConnected, onCreateContainer }: HeaderProps) {
  return (
    <header className="h-16 bg-card/80 backdrop-blur-xl border-b border-border px-4 lg:px-8 flex items-center justify-between sticky top-0 z-50">
      {/* Left Section */}
      <div className="flex items-center gap-4">
        <button className="lg:hidden p-2 rounded-lg hover:bg-secondary text-muted-foreground">
          <Menu className="w-5 h-5" />
        </button>
        
        <div className="hidden md:flex items-center relative">
          <Search className="w-4 h-4 absolute left-3 text-muted-foreground" />
          <Input 
            placeholder="Search containers, metrics..."
            className="w-72 pl-10 bg-secondary/50 border-border/50 focus:border-primary/50 focus:bg-secondary"
          />
          <kbd className="absolute right-3 pointer-events-none text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
            /
          </kbd>
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-3">
        {/* Connection Status */}
        <div 
          className={cn(
            "hidden sm:flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold uppercase tracking-wide transition-all",
            isConnected 
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" 
              : "bg-red-500/10 text-red-400 border border-red-500/30"
          )}
        >
          <span 
            className={cn(
              "w-2 h-2 rounded-full",
              isConnected 
                ? "bg-emerald-400 animate-pulse-glow" 
                : "bg-red-400"
            )}
          />
          {isConnected ? "Connected" : "Disconnected"}
        </div>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-5 h-5 text-muted-foreground" />
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full text-[10px] font-bold flex items-center justify-center text-white">
            3
          </span>
        </Button>

        {/* Create Container */}
        <Button 
          onClick={onCreateContainer}
          className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white shadow-lg shadow-cyan-500/25 transition-all hover:shadow-cyan-500/40 hover:scale-[1.02]"
        >
          <Plus className="w-4 h-4 mr-2" />
          <span className="hidden sm:inline">New Container</span>
          <span className="sm:hidden">New</span>
        </Button>
      </div>
    </header>
  )
}
