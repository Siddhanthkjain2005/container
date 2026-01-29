"use client"

import { 
  LayoutDashboard, 
  Box, 
  Activity, 
  BarChart3, 
  Settings, 
  HelpCircle,
  Layers,
  Terminal,
  Bell,
  ChevronLeft
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useState } from "react"

interface SidebarProps {
  activeNav: string
  onNavChange: (nav: string) => void
}

const navItems = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "containers", label: "Containers", icon: Box },
  { id: "monitoring", label: "Monitoring", icon: Activity },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "logs", label: "Logs", icon: Terminal },
  { id: "network", label: "Network", icon: Layers },
]

const bottomItems = [
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "settings", label: "Settings", icon: Settings },
  { id: "help", label: "Help", icon: HelpCircle },
]

export function Sidebar({ activeNav, onNavChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside 
      className={cn(
        "hidden lg:flex flex-col bg-card border-r border-border transition-all duration-300 relative",
        collapsed ? "w-20" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Box className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-foreground text-lg tracking-tight">MiniContainer</span>
              <span className="text-xs text-muted-foreground">Enterprise Edition</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 py-6 px-3 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavChange(item.id)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
              activeNav === item.id 
                ? "bg-primary/10 text-primary" 
                : "text-muted-foreground hover:text-foreground hover:bg-secondary"
            )}
          >
            <item.icon className={cn(
              "w-5 h-5 flex-shrink-0",
              activeNav === item.id && "text-primary"
            )} />
            {!collapsed && (
              <span className="font-medium text-sm">{item.label}</span>
            )}
            {activeNav === item.id && !collapsed && (
              <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />
            )}
          </button>
        ))}
      </nav>

      {/* Divider */}
      <div className="px-4">
        <div className="h-px bg-border" />
      </div>

      {/* Bottom Navigation */}
      <nav className="py-4 px-3 space-y-1">
        {bottomItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavChange(item.id)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
              activeNav === item.id 
                ? "bg-primary/10 text-primary" 
                : "text-muted-foreground hover:text-foreground hover:bg-secondary"
            )}
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {!collapsed && (
              <span className="font-medium text-sm">{item.label}</span>
            )}
          </button>
        ))}
      </nav>

      {/* Collapse Button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-card border border-border flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
      >
        <ChevronLeft className={cn(
          "w-4 h-4 transition-transform",
          collapsed && "rotate-180"
        )} />
      </button>

      {/* User Info */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold text-sm">
            A
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">Admin</p>
              <p className="text-xs text-muted-foreground truncate">admin@system</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
