"use client"

import { useState } from "react"
import { Header } from "./dashboard/header"
import { StatsBar } from "./dashboard/stats-bar"
import { LiveCharts } from "./dashboard/live-charts"
import { ContainerGrid } from "./dashboard/container-grid"
import { Sidebar } from "./dashboard/sidebar"
import { CreateContainerModal } from "./dashboard/create-container-modal"

// Mock data for demonstration
const mockContainers = [
  { id: "mc-a7b3c9d1", name: "web-server", state: "running", pid: 12345, cpu: 23.4, memory: 45.2, memoryBytes: 120586240, memoryLimit: 268435456, pids: 12 },
  { id: "mc-e4f5g6h7", name: "api-gateway", state: "running", pid: 12346, cpu: 67.8, memory: 78.3, memoryBytes: 210108416, memoryLimit: 268435456, pids: 8 },
  { id: "mc-i8j9k0l1", name: "database", state: "running", pid: 12347, cpu: 34.1, memory: 52.6, memoryBytes: 141289472, memoryLimit: 268435456, pids: 15 },
  { id: "mc-m2n3o4p5", name: "cache-redis", state: "created", pid: 0, cpu: 0, memory: 0, memoryBytes: 0, memoryLimit: 268435456, pids: 0 },
  { id: "mc-q6r7s8t9", name: "worker-node", state: "stopped", pid: 0, cpu: 0, memory: 0, memoryBytes: 0, memoryLimit: 268435456, pids: 0 },
  { id: "mc-u0v1w2x3", name: "load-balancer", state: "running", pid: 12348, cpu: 12.5, memory: 28.9, memoryBytes: 77593395, memoryLimit: 268435456, pids: 4 },
]

const mockMetricsHistory = Array.from({ length: 30 }, (_, i) => ({
  timestamp: Date.now() - (29 - i) * 1000,
  cpu: Math.random() * 40 + 20,
  memory: Math.random() * 30 + 35,
}))

export function Dashboard() {
  const [containers, setContainers] = useState(mockContainers)
  const [isConnected, setIsConnected] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [activeNav, setActiveNav] = useState("overview")

  const runningCount = containers.filter(c => c.state === "running").length
  const totalCpu = containers.reduce((sum, c) => sum + c.cpu, 0) / Math.max(runningCount, 1)
  const totalMemory = containers.reduce((sum, c) => sum + c.memory, 0) / Math.max(runningCount, 1)
  const totalPids = containers.reduce((sum, c) => sum + c.pids, 0)

  const handleCreateContainer = (name: string) => {
    const newContainer = {
      id: `mc-${Math.random().toString(36).substring(2, 10)}`,
      name,
      state: "created" as const,
      pid: 0,
      cpu: 0,
      memory: 0,
      memoryBytes: 0,
      memoryLimit: 268435456,
      pids: 0,
    }
    setContainers([...containers, newContainer])
    setShowCreateModal(false)
  }

  const handleStartContainer = (id: string) => {
    setContainers(containers.map(c => 
      c.id === id ? { ...c, state: "running", pid: Math.floor(Math.random() * 10000) + 10000, cpu: Math.random() * 30, memory: Math.random() * 40 + 20, pids: Math.floor(Math.random() * 10) + 1 } : c
    ))
  }

  const handleStopContainer = (id: string) => {
    setContainers(containers.map(c => 
      c.id === id ? { ...c, state: "stopped", pid: 0, cpu: 0, memory: 0, pids: 0 } : c
    ))
  }

  const handleDeleteContainer = (id: string) => {
    setContainers(containers.filter(c => c.id !== id))
  }

  return (
    <div className="min-h-screen flex">
      <Sidebar activeNav={activeNav} onNavChange={setActiveNav} />
      
      <div className="flex-1 flex flex-col">
        <Header 
          isConnected={isConnected} 
          onCreateContainer={() => setShowCreateModal(true)} 
        />
        
        <main className="flex-1 p-6 lg:p-8 max-w-[1800px] mx-auto w-full">
          <StatsBar 
            containerCount={containers.length}
            runningCount={runningCount}
            avgCpu={totalCpu}
            totalPids={totalPids}
          />
          
          <LiveCharts 
            metricsHistory={mockMetricsHistory}
            currentCpu={totalCpu}
            currentMemory={totalMemory}
          />
          
          <ContainerGrid 
            containers={containers}
            onStart={handleStartContainer}
            onStop={handleStopContainer}
            onDelete={handleDeleteContainer}
            onCreateNew={() => setShowCreateModal(true)}
          />
        </main>
      </div>

      {showCreateModal && (
        <CreateContainerModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateContainer}
        />
      )}
    </div>
  )
}
