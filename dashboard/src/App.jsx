import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const API_URL = 'https://diphyodont-zachery-multifamilial.ngrok-free.dev'
const WS_URL = 'wss://diphyodont-zachery-multifamilial.ngrok-free.dev/ws'

// Format bytes to human readable
function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// Status Badge Component
function StatusBadge({ status }) {
  const labels = {
    running: 'Running',
    created: 'Created',
    stopped: 'Stopped',
    unknown: 'Unknown'
  }

  return (
    <span className={`status-badge ${status}`}>
      <span className="status-dot"></span>
      {labels[status] || status}
    </span>
  )
}

// Live Chart Component
function LiveChart({ data, color, label }) {
  if (!data || data.length < 2) return null

  const width = 100
  const height = 100
  const max = Math.max(...data, 1)

  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width
    const y = height - (val / max) * height * 0.9
    return `${x},${y}`
  }).join(' ')

  const areaPoints = `0,${height} ${points} ${width},${height}`

  return (
    <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="chart-svg">
      <defs>
        <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon fill={`url(#gradient-${color})`} points={areaPoints} />
      <polyline fill="none" stroke={color} strokeWidth="2" points={points} />
    </svg>
  )
}

// Running Container Section with Dual Live Charts
function RunningContainersSection({ containers, metrics, history }) {
  const runningContainers = containers.filter(c => c.state === 'running')

  if (runningContainers.length === 0) return null

  return (
    <div className="live-chart-section">
      <h2>
        <span className="pulse"></span>
        Live Monitoring ({runningContainers.length} running)
      </h2>

      {runningContainers.map(container => {
        const m = metrics[container.id] || {}
        const h = history[container.id] || { cpu: [], mem: [] }
        const memPercent = m.memory_bytes && m.memory_limit_bytes > 0
          ? (m.memory_bytes / m.memory_limit_bytes * 100) : 0

        return (
          <div key={container.id} className="live-chart-container">
            <div className="chart-header">
              <span className="chart-title">🐳 {container.name}</span>
              <span className="chart-status">● Live</span>
            </div>

            {/* Stats Row */}
            <div className="chart-stats">
              <div className="chart-stat">
                <span className="chart-stat-value cpu-value">{(m.cpu_percent || 0).toFixed(1)}%</span>
                <span className="chart-stat-label">CPU Usage</span>
              </div>
              <div className="chart-stat">
                <span className="chart-stat-value mem-value">{formatBytes(m.memory_bytes || 0)}</span>
                <span className="chart-stat-label">Memory Used</span>
              </div>
              <div className="chart-stat">
                <span className="chart-stat-value">{memPercent.toFixed(0)}%</span>
                <span className="chart-stat-label">Mem %</span>
              </div>
              <div className="chart-stat">
                <span className="chart-stat-value">{m.pids || 0}</span>
                <span className="chart-stat-label">Processes</span>
              </div>
            </div>

            {/* Dual Graph Section */}
            <div className="dual-charts">
              {/* CPU Graph */}
              <div className="chart-panel cpu-panel">
                <div className="chart-panel-header">
                  <span className="chart-panel-label">
                    <span className="legend-dot cpu"></span>
                    CPU Usage
                  </span>
                  <span className="chart-panel-value">{(m.cpu_percent || 0).toFixed(1)}%</span>
                </div>
                <LiveChart data={h.cpu} color="#ff9f00" label="CPU" />
              </div>

              {/* Memory Graph */}
              <div className="chart-panel mem-panel">
                <div className="chart-panel-header">
                  <span className="chart-panel-label">
                    <span className="legend-dot mem"></span>
                    Memory Usage
                  </span>
                  <span className="chart-panel-value">{formatBytes(m.memory_bytes || 0)}</span>
                </div>
                <LiveChart data={h.mem.map(v => v / 1048576)} color="#00d4ff" label="Memory" />
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// Container Card Component
function ContainerCard({ container, metrics, onAction, actionLoading, onMonitor, onExec }) {
  const m = metrics || {}
  const memPercent = m.memory_bytes && m.memory_limit_bytes > 0
    ? (m.memory_bytes / m.memory_limit_bytes * 100) : 0

  return (
    <div className={`container-card ${container.state}`}>
      <div className="container-card-header">
        <div className="container-info">
          <h3>🐳 {container.name}</h3>
          <div className="container-id">{container.id}</div>
        </div>
        <StatusBadge status={container.state} />
      </div>

      <div className="container-metrics">
        <div className="metric-row">
          <span className="metric-icon">⚡</span>
          <span className="metric-label">CPU</span>
          <div className="metric-bar">
            <div className="metric-fill cpu" style={{ width: `${Math.min(m.cpu_percent || 0, 100)}%` }}></div>
          </div>
          <span className="metric-value">{(m.cpu_percent || 0).toFixed(1)}%</span>
        </div>

        <div className="metric-row">
          <span className="metric-icon">💾</span>
          <span className="metric-label">Memory</span>
          <div className="metric-bar">
            <div className="metric-fill mem" style={{ width: `${Math.min(memPercent, 100)}%` }}></div>
          </div>
          <span className="metric-value">{formatBytes(m.memory_bytes || 0)}</span>
        </div>

        <div className="metric-row">
          <span className="metric-icon">🔢</span>
          <span className="metric-label">Processes</span>
          <span className="metric-value" style={{ marginLeft: 'auto' }}>{m.pids || 0}</span>
        </div>
      </div>

      <div className="container-actions">
        <button className="btn btn-monitor" onClick={() => onMonitor(container)}>
          📊 Details
        </button>

        {container.state === 'running' ? (
          <button
            className="btn btn-stop"
            onClick={() => onAction('stop', container.id)}
            disabled={actionLoading}
          >
            ⏹ Stop
          </button>
        ) : (
          <button
            className="btn btn-start"
            onClick={() => onExec(container)}
            disabled={actionLoading}
          >
            ▶ Start
          </button>
        )}

        <button
          className="btn btn-delete btn-icon"
          onClick={() => onAction('delete', container.id)}
          disabled={actionLoading}
          title="Delete container"
        >
          🗑
        </button>
      </div>
    </div>
  )
}

// Monitor Modal with Process List
function MonitorModal({ container, metrics, history, onClose }) {
  const [processes, setProcesses] = useState([])
  const [loadingProcesses, setLoadingProcesses] = useState(false)
  const [showProcesses, setShowProcesses] = useState(false)

  if (!container) return null
  const m = metrics || {}
  const h = history || { cpu: [], mem: [] }
  const memPercent = m.memory_bytes && m.memory_limit_bytes > 0
    ? (m.memory_bytes / m.memory_limit_bytes * 100) : 0

  const fetchProcesses = async () => {
    setLoadingProcesses(true)
    setShowProcesses(true)
    try {
      const res = await fetch(`${API_URL}/api/containers/${container.id}/processes`, {
        headers: {
          'ngrok-skip-browser-warning': 'true',
          'Accept': 'application/json'
        }
      })
      if (!res.ok) {
        console.error('Process fetch failed:', res.status, res.statusText)
        setProcesses([])
        return
      }
      const data = await res.json()
      console.log('Fetched processes:', data)
      setProcesses(data.processes || [])
    } catch (e) {
      console.error('Failed to fetch processes:', e)
      setProcesses([])
    }
    setLoadingProcesses(false)
  }

  // Calculate memory sum from processes
  const processMemSum = processes.reduce((sum, p) => sum + (p.memory_bytes || 0), 0)

  // Get running command from first process (init)
  const runningCommand = processes.length > 0 ? processes[0].command : null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal monitor-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📊 {container.name}</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {/* PID Info Banner */}
          <div className="pid-banner">
            <div className="pid-item">
              <span className="pid-label">Container ID:</span>
              <span className="pid-value">{container.id}</span>
            </div>
            <div className="pid-item">
              <span className="pid-label">Init PID:</span>
              <span className="pid-value">{m.init_pid || 'N/A'}</span>
            </div>
            <div className="pid-item">
              <span className="pid-label">State:</span>
              <StatusBadge status={container.state} />
            </div>
          </div>

          {/* Running Command Display */}
          {runningCommand && (
            <div className="command-banner">
              <div className="command-label">▶ Running Command:</div>
              <code className="command-code">{runningCommand}</code>
            </div>
          )}

          <div className="monitor-stats">
            <div className="monitor-stat-card">
              <div className="stat-header">
                <span className="stat-icon">⚡</span>
                <span>CPU Usage</span>
              </div>
              <div className="stat-value-large">{(m.cpu_percent || 0).toFixed(1)}%</div>
              <div className="stat-bar">
                <div className="stat-bar-fill cpu" style={{ width: `${Math.min(m.cpu_percent || 0, 100)}%` }}></div>
              </div>
            </div>

            <div className="monitor-stat-card">
              <div className="stat-header">
                <span className="stat-icon">💾</span>
                <span>Memory</span>
              </div>
              <div className="stat-value-large">{formatBytes(m.memory_bytes || 0)}</div>
              <div className="stat-detail">of {formatBytes(m.memory_limit_bytes || 0)} ({memPercent.toFixed(1)}%)</div>
              <div className="stat-bar">
                <div className="stat-bar-fill mem" style={{ width: `${Math.min(memPercent, 100)}%` }}></div>
              </div>
            </div>

            <div className="monitor-stat-card">
              <div className="stat-header">
                <span className="stat-icon">🔢</span>
                <span>Process Count</span>
              </div>
              <div className="stat-value-large">{m.pids || 0}</div>
              <button className="btn btn-sm" onClick={fetchProcesses} disabled={loadingProcesses}>
                {loadingProcesses ? '...' : '👁 View Processes'}
              </button>
            </div>

            <div className="monitor-stat-card">
              <div className="stat-header">
                <span className="stat-icon">🏷</span>
                <span>Uptime</span>
              </div>
              <div className="stat-value-large" style={{ fontSize: '1rem' }}>
                <StatusBadge status={container.state} />
              </div>
            </div>
          </div>

          {/* Process List Panel */}
          {showProcesses && (
            <div className="process-panel">
              <div className="process-header">
                <h4>🔍 Running Processes</h4>
                <button className="btn btn-sm" onClick={() => setShowProcesses(false)}>✕ Close</button>
              </div>
              {loadingProcesses ? (
                <div className="process-loading">Loading processes...</div>
              ) : processes.length === 0 ? (
                <div className="process-empty">
                  <div className="empty-icon">📭</div>
                  <div className="empty-title">No Running Processes</div>
                  <div className="empty-desc">
                    Container is stopped or idle. To see processes:
                    <ol>
                      <li>Click "▶ Start" on the container card</li>
                      <li>Choose a command (CPU Stress, Sleep, etc.)</li>
                      <li>Come back here to see running processes</li>
                    </ol>
                  </div>
                </div>
              ) : (
                <div className="process-table-wrapper">
                  <table className="process-table">
                    <thead>
                      <tr>
                        <th>PID</th>
                        <th>PPID</th>
                        <th>Name</th>
                        <th>State</th>
                        <th>Memory</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {processes.map(p => (
                        <tr key={p.pid} className={p.pid === m.init_pid ? 'init-process' : ''}>
                          <td className="pid-col">{p.pid}</td>
                          <td className="ppid-col">{p.ppid}</td>
                          <td className="name-col">{p.name}</td>
                          <td className="state-col">
                            <span className={`state-badge ${p.state_code}`}>{p.state}</span>
                          </td>
                          <td className="mem-col">{p.memory_human}</td>
                          <td className="desc-col" title={p.command}>{p.description || 'User process'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <div className="process-legend">
                <span><b>PID</b>: Process ID (unique number for each process)</span>
                <span><b>PPID</b>: Parent Process ID (who spawned this process)</span>
                <span className="init-highlight">Highlighted row = Container's init process (PID 1 inside)</span>
              </div>
            </div>
          )}

          {/* Charts */}
          <div className="charts-grid">
            {h.cpu.length > 1 && (
              <div className="chart-container">
                <div className="chart-title">📈 CPU History</div>
                <LiveChart data={h.cpu} color="#eab308" label="CPU" />
              </div>
            )}
            {h.mem.length > 1 && (
              <div className="chart-container">
                <div className="chart-title">📊 Memory History</div>
                <LiveChart data={h.mem.map(b => b / (1024 * 1024))} color="#22d3ee" label="Memory (MB)" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Execute Command Modal - Shows when clicking Start
function ExecuteCommandModal({ container, isOpen, onClose, onExecute }) {
  const [selectedCmd, setSelectedCmd] = useState('1')
  const [duration, setDuration] = useState(60)
  const [memorySize, setMemorySize] = useState(50)
  const [customCmd, setCustomCmd] = useState('echo Hello from container')
  const [executing, setExecuting] = useState(false)

  if (!isOpen || !container) return null

  const commands = [
    { id: '1', icon: '🔥', name: 'CPU Stress', desc: 'Intensive counting loop - high CPU usage' },
    { id: '2', icon: '💾', name: 'Memory Stress', desc: 'Allocate and hold memory' },
    { id: '3', icon: '🔄', name: 'Combined Stress', desc: 'CPU + Memory together' },
    { id: '4', icon: '⏱️', name: 'Sleep Process', desc: 'Keep container running for monitoring' },
    { id: '5', icon: '📊', name: 'Math Calculations', desc: 'Heavy math operations' },
    { id: '6', icon: '✏️', name: 'Custom Command', desc: 'Enter your own shell command' },
  ]

  const handleExecute = async () => {
    setExecuting(true)
    await onExecute(container.id, selectedCmd, { duration, memorySize, customCmd })
    setExecuting(false)
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal exec-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>⚡ Execute Command</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="exec-container-info">
            <span className="exec-label">Container:</span>
            <span className="exec-name">🐳 {container.name}</span>
          </div>

          <div className="command-list">
            {commands.map(cmd => (
              <div
                key={cmd.id}
                className={`command-item ${selectedCmd === cmd.id ? 'selected' : ''}`}
                onClick={() => setSelectedCmd(cmd.id)}
              >
                <span className="cmd-icon">{cmd.icon}</span>
                <div className="cmd-info">
                  <span className="cmd-name">{cmd.name}</span>
                  <span className="cmd-desc">{cmd.desc}</span>
                </div>
                <span className="cmd-radio">{selectedCmd === cmd.id ? '●' : '○'}</span>
              </div>
            ))}
          </div>

          {/* Duration input for most commands */}
          {['1', '2', '3', '4', '5'].includes(selectedCmd) && (
            <div className="form-group">
              <label>Duration: {duration} seconds</label>
              <input
                type="range"
                min="10"
                max="300"
                value={duration}
                onChange={e => setDuration(parseInt(e.target.value))}
              />
            </div>
          )}

          {/* Memory size for memory-related commands */}
          {['2', '3'].includes(selectedCmd) && (
            <div className="form-group">
              <label>Memory Size: {memorySize} MB</label>
              <input
                type="range"
                min="10"
                max="200"
                value={memorySize}
                onChange={e => setMemorySize(parseInt(e.target.value))}
              />
            </div>
          )}

          {/* Custom command input */}
          {selectedCmd === '6' && (
            <div className="form-group">
              <label>Custom Command</label>
              <input
                type="text"
                value={customCmd}
                onChange={e => setCustomCmd(e.target.value)}
                placeholder="Enter shell command..."
              />
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button
            className="btn btn-primary"
            onClick={handleExecute}
            disabled={executing}
          >
            {executing ? '⏳ Executing...' : '▶ Execute'}
          </button>
        </div>
      </div>
    </div>
  )
}

// Create Container Modal
function CreateContainerModal({ isOpen, onClose, onCreate }) {
  const [name, setName] = useState('')
  const [rootfs, setRootfs] = useState('/tmp/alpine-rootfs')
  const [memory, setMemory] = useState('256')
  const [cpus, setCpus] = useState('50')
  const [pids, setPids] = useState('100')

  if (!isOpen) return null

  const handleSubmit = (e) => {
    e.preventDefault()
    onCreate({
      name: name || `container-${Date.now()}`,
      rootfs: rootfs,
      memory_limit: parseInt(memory) * 1024 * 1024,
      cpu_percent: parseInt(cpus),
      pids_max: parseInt(pids)
    })
    onClose()
    setName('')
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>🐳 Create Container</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label>Container Name</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="my-container"
              />
            </div>

            <div className="form-group">
              <label>Rootfs Path <span className="hint">(filesystem directory)</span></label>
              <input
                type="text"
                value={rootfs}
                onChange={e => setRootfs(e.target.value)}
                placeholder="/tmp/alpine-rootfs"
              />
            </div>

            <div className="form-group">
              <label>Memory Limit: {memory} MB</label>
              <input
                type="range"
                min="64"
                max="2048"
                value={memory}
                onChange={e => setMemory(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>CPU Limit: {cpus}%</label>
              <input
                type="range"
                min="5"
                max="100"
                value={cpus}
                onChange={e => setCpus(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Max Processes: {pids}</label>
              <input
                type="range"
                min="10"
                max="500"
                value={pids}
                onChange={e => setPids(e.target.value)}
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary">Create Container</button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Main App Component
function App() {
  const [containers, setContainers] = useState([])
  const [metrics, setMetrics] = useState({})
  const [history, setHistory] = useState({})
  const [loading, setLoading] = useState(true)
  const [wsStatus, setWsStatus] = useState('disconnected')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [monitorContainer, setMonitorContainer] = useState(null)
  const [execContainer, setExecContainer] = useState(null)
  const [notification, setNotification] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState('dashboard') // dashboard, analytics, about
  const [healthScores, setHealthScores] = useState({})
  const [anomalies, setAnomalies] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const wsRef = useRef(null)

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }

  const fetchContainers = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/containers`, {
        headers: { 'ngrok-skip-browser-warning': 'true' }
      })
      if (res.ok) {
        const data = await res.json()
        setContainers(data)
      }
    } catch (e) {
      console.error('Failed to fetch containers:', e)
    }
    setLoading(false)
  }, [])

  // WebSocket connection
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => setWsStatus('connected')
      ws.onclose = () => {
        setWsStatus('disconnected')
        setTimeout(connect, 3000)
      }
      ws.onerror = () => setWsStatus('error')

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'metrics') {
            setContainers(data.containers || [])
            setMetrics(data.metrics || {})

            // Update history
            setHistory(prev => {
              const newHistory = { ...prev }
              for (const [id, m] of Object.entries(data.metrics || {})) {
                if (!newHistory[id]) {
                  newHistory[id] = { cpu: [], mem: [] }
                }
                newHistory[id].cpu = [...(newHistory[id].cpu || []).slice(-30), m.cpu_percent || 0]
                newHistory[id].mem = [...(newHistory[id].mem || []).slice(-30), m.memory_bytes || 0]
              }
              return newHistory
            })

            // Update health scores and anomalies from ML
            if (data.health_scores) {
              setHealthScores(data.health_scores)
            }
            if (data.anomalies) {
              setAnomalies(prev => [...prev.slice(-50), ...data.anomalies])
            }
          }
        } catch (e) {
          console.error('WS parse error:', e)
        }
      }
    }

    connect()
    fetchContainers()

    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [fetchContainers])

  const handleContainerAction = async (action, containerId) => {
    setActionLoading(true)
    try {
      let endpoint = `${API_URL}/api/containers/${containerId}`
      let method = 'POST'

      if (action === 'delete') {
        method = 'DELETE'
      } else {
        endpoint = `${endpoint}/${action}`
      }

      const res = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        }
      })
      if (res.ok) {
        showNotification(`Container ${action}ed!`, 'success')
      } else {
        showNotification(`Failed to ${action} container`, 'error')
      }
      await fetchContainers()
    } catch (e) {
      console.error(`Failed to ${action} container:`, e)
      showNotification(`Failed to ${action} container`, 'error')
    }
    setActionLoading(false)
  }

  const createContainer = async (config) => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/containers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify(config)
      })
      if (res.ok) {
        showNotification('Container created!', 'success')
      } else {
        showNotification('Failed to create container', 'error')
      }
      await fetchContainers()
    } catch (e) {
      console.error('Failed to create container:', e)
      showNotification('Failed to create container', 'error')
    }
    setLoading(false)
  }

  // Execute command in container
  const executeCommand = async (containerId, cmdType, options) => {
    const { duration, memorySize, customCmd } = options
    let command = ''

    switch (cmdType) {
      case '1': // CPU Stress - TIME BASED
        command = `echo 'Starting CPU stress for ${duration}s...'; END=$(($(date +%s) + ${duration})); i=0; while [ $(date +%s) -lt $END ]; do i=$((i+1)); done; echo 'CPU stress complete after ${duration}s'`
        break
      case '2': // Memory Stress
        command = `dd if=/dev/zero of=/dev/shm/memtest bs=1M count=${memorySize} 2>/dev/null && echo 'Allocated ${memorySize}MB' && sleep ${duration} && rm -f /dev/shm/memtest && echo 'Memory released after ${duration}s'`
        break
      case '3': // Combined Stress - TIME BASED
        command = `dd if=/dev/zero of=/dev/shm/memtest bs=1M count=${memorySize} 2>/dev/null; echo 'Allocated ${memorySize}MB, running CPU stress...'; END=$(($(date +%s) + ${duration})); i=0; while [ $(date +%s) -lt $END ]; do i=$((i+1)); done; rm -f /dev/shm/memtest; echo 'Combined test complete after ${duration}s'`
        break
      case '4': // Sleep
        command = `echo 'Container running for ${duration}s...'; sleep ${duration}; echo 'Done after ${duration}s'`
        break
      case '5': // Math - TIME BASED
        command = `echo 'Starting math calculations for ${duration}s...'; END=$(($(date +%s) + ${duration})); i=0; j=0; while [ $(date +%s) -lt $END ]; do j=$((j+i*i)); i=$((i+1)); done; echo 'Math complete after ${duration}s'`
        break
      case '6': // Custom
        command = customCmd
        break
      default:
        command = 'echo Hello'
    }

    try {
      const res = await fetch(`${API_URL}/api/containers/${containerId}/exec`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify({ command })
      })
      if (res.ok) {
        showNotification('Command started!', 'success')
      } else {
        showNotification('Failed to execute command', 'error')
      }
      await fetchContainers()
    } catch (e) {
      console.error('Failed to exec:', e)
      showNotification('Failed to execute command', 'error')
    }
  }

  const runningCount = containers.filter(c => c.state === 'running').length
  const totalCpu = Object.values(metrics).reduce((sum, m) => sum + (m.cpu_percent || 0), 0)
  const totalMem = Object.values(metrics).reduce((sum, m) => sum + (m.memory_bytes || 0), 0)

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <span className="logo-icon">🐳</span>
          <h1>Mini<span>Container</span></h1>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${currentPage === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentPage('dashboard')}
          >
            📊 Dashboard
          </button>
          <button
            className={`nav-tab ${currentPage === 'stats' ? 'active' : ''}`}
            onClick={() => setCurrentPage('stats')}
          >
            📈 Stats
          </button>
          <button
            className={`nav-tab ${currentPage === 'analytics' ? 'active' : ''}`}
            onClick={() => setCurrentPage('analytics')}
          >
            🤖 ML Analytics
          </button>
          <button
            className={`nav-tab ${currentPage === 'about' ? 'active' : ''}`}
            onClick={() => setCurrentPage('about')}
          >
            ℹ️ About
          </button>
        </nav>

        <div className="header-right">
          <div className={`ws-status ${wsStatus}`}>
            <span className="dot"></span>
            {wsStatus === 'connected' ? 'Live' : 'Offline'}
          </div>
        </div>
      </header>

      <main className="main">
        {/* Stats Overview */}
        <div className="stats-bar">
          <div className="stat-card">
            <div className="stat-icon total">📦</div>
            <div className="stat-content">
              <div className="stat-value">{containers.length}</div>
              <div className="stat-label">Total Containers</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon running">▶️</div>
            <div className="stat-content">
              <div className="stat-value">{runningCount}</div>
              <div className="stat-label">Running</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon cpu">⚡</div>
            <div className="stat-content">
              <div className="stat-value">{totalCpu.toFixed(1)}%</div>
              <div className="stat-label">Total CPU</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon mem">💾</div>
            <div className="stat-content">
              <div className="stat-value">{formatBytes(totalMem)}</div>
              <div className="stat-label">Total Memory</div>
            </div>
          </div>
        </div>

        {/* Page Content */}
        {currentPage === 'dashboard' && (
          <>
            {/* Live Monitoring Section for Running Containers */}
            <RunningContainersSection
              containers={containers}
              metrics={metrics}
              history={history}
            />

            {/* Action Bar */}
            <div className="action-bar">
              <h2>All Containers</h2>
              <div className="action-buttons">
                <button className="btn btn-secondary" onClick={fetchContainers}>
                  🔄 Refresh
                </button>
                <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                  ➕ Create Container
                </button>
              </div>
            </div>

            {/* Container Grid */}
            {loading ? (
              <div className="loading">
                <div className="loader"></div>
                <p>Loading containers...</p>
              </div>
            ) : containers.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📦</div>
                <div className="empty-title">No Containers Yet</div>
                <div className="empty-subtitle">Create your first container to get started</div>
                <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                  ➕ Create Container
                </button>
              </div>
            ) : (
              <div className="containers">
                {containers.map(container => (
                  <ContainerCard
                    key={container.id}
                    container={container}
                    metrics={metrics[container.id]}
                    history={history[container.id]}
                    onAction={handleContainerAction}
                    onMonitor={setMonitorContainer}
                    onExec={setExecContainer}
                    actionLoading={actionLoading}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {/* Stats Page - New Analytics with CPU Time and Graphs */}
        {currentPage === 'stats' && (
          <div className="stats-page">
            <div className="analytics-header">
              <h2 className="page-title">📈 Container Statistics & Graphs</h2>
              <a
                className="btn btn-secondary export-btn"
                href={`${API_URL}/api/export/csv`}
                download="minicontainer_metrics.csv"
                target="_blank"
                rel="noopener noreferrer"
              >
                📥 Export CSV
              </a>
            </div>

            {/* Overview Stats */}
            <div className="analytics-section">
              <h3>📊 System Overview</h3>
              <div className="stats-overview-grid">
                <div className="overview-card">
                  <div className="overview-icon">📦</div>
                  <div className="overview-value">{containers.length}</div>
                  <div className="overview-label">Total Containers</div>
                </div>
                <div className="overview-card">
                  <div className="overview-icon">▶️</div>
                  <div className="overview-value">{containers.filter(c => c.state === 'running').length}</div>
                  <div className="overview-label">Running</div>
                </div>
                <div className="overview-card">
                  <div className="overview-icon">⚡</div>
                  <div className="overview-value">{totalCpu.toFixed(1)}%</div>
                  <div className="overview-label">Total CPU Usage</div>
                </div>
                <div className="overview-card">
                  <div className="overview-icon">💾</div>
                  <div className="overview-value">{formatBytes(totalMem)}</div>
                  <div className="overview-label">Total Memory Used</div>
                </div>
              </div>
            </div>

            {/* Per-Container Detailed Stats */}
            <div className="analytics-section">
              <h3>🔬 Container Details with CPU Time</h3>
              <div className="container-details-grid">
                {containers.map(container => {
                  const m = metrics[container.id] || {}
                  const h = history[container.id] || { cpu: [], mem: [] }
                  const totalPids = h.cpu.length // Use as proxy for data samples

                  return (
                    <div key={container.id} className="container-detail-card">
                      <div className="detail-header">
                        <span className="detail-name">{container.name}</span>
                        <StatusBadge status={container.state} />
                      </div>

                      <div className="detail-stats">
                        <div className="detail-stat">
                          <span className="stat-icon">🆔</span>
                          <span className="stat-key">Container ID</span>
                          <span className="stat-val">{container.id}</span>
                        </div>
                        <div className="detail-stat">
                          <span className="stat-icon">🔢</span>
                          <span className="stat-key">Init PID</span>
                          <span className="stat-val">{m.init_pid || 'N/A'}</span>
                        </div>
                        <div className="detail-stat">
                          <span className="stat-icon">⚡</span>
                          <span className="stat-key">CPU Usage</span>
                          <span className="stat-val">{(m.cpu_percent || 0).toFixed(1)}%</span>
                        </div>
                        <div className="detail-stat">
                          <span className="stat-icon">💾</span>
                          <span className="stat-key">Memory Used</span>
                          <span className="stat-val">{formatBytes(m.memory_bytes || 0)}</span>
                        </div>
                        <div className="detail-stat">
                          <span className="stat-icon">📊</span>
                          <span className="stat-key">Memory Limit</span>
                          <span className="stat-val">{formatBytes(m.memory_limit_bytes || 0)}</span>
                        </div>
                        <div className="detail-stat">
                          <span className="stat-icon">👥</span>
                          <span className="stat-key">Process Count</span>
                          <span className="stat-val">{m.pids || 0}</span>
                        </div>
                        <div className="detail-stat">
                          <span className="stat-icon">📈</span>
                          <span className="stat-key">Data Samples</span>
                          <span className="stat-val">{totalPids}</span>
                        </div>
                        <div className="detail-stat">
                          <span className="stat-icon">❤️</span>
                          <span className="stat-key">Health Score</span>
                          <span className="stat-val" style={{ color: (healthScores[container.id] || 100) >= 80 ? 'var(--neon-green)' : 'var(--neon-orange)' }}>
                            {(healthScores[container.id] || 100).toFixed(0)}/100
                          </span>
                        </div>
                      </div>

                      {/* Mini Charts */}
                      <div className="detail-charts">
                        <div className="mini-chart-box">
                          <div className="mini-chart-title">CPU Over Time</div>
                          {h.cpu.length > 1 ? (
                            <LiveChart data={h.cpu} color="#eab308" label="CPU" />
                          ) : (
                            <div className="no-chart-data">Waiting for data...</div>
                          )}
                        </div>
                        <div className="mini-chart-box">
                          <div className="mini-chart-title">Memory Over Time</div>
                          {h.mem.length > 1 ? (
                            <LiveChart data={h.mem.map(b => b / (1024 * 1024))} color="#22d3ee" label="MB" />
                          ) : (
                            <div className="no-chart-data">Waiting for data...</div>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
                {containers.length === 0 && (
                  <div className="empty-analytics">No containers available. Create one to see stats.</div>
                )}
              </div>
            </div>

            {/* Combined Charts Section */}
            <div className="analytics-section">
              <h3>📉 Combined Resource Trends</h3>
              <div className="combined-charts">
                <div className="combined-chart-card">
                  <div className="combined-chart-title">🔥 All Container CPU Usage</div>
                  <div className="combined-chart-legend">
                    {containers.map((c, i) => (
                      <span key={c.id} className="legend-item" style={{ color: ['#eab308', '#22d3ee', '#a855f7', '#22c55e'][i % 4] }}>
                        ● {c.name}
                      </span>
                    ))}
                  </div>
                  <div className="stacked-bars">
                    {containers.map((c, i) => {
                      const cpuVal = metrics[c.id]?.cpu_percent || 0
                      return (
                        <div key={c.id} className="stacked-bar-row">
                          <span className="bar-label">{c.name}</span>
                          <div className="bar-track">
                            <div
                              className="bar-fill"
                              style={{
                                width: `${Math.min(cpuVal, 100)}%`,
                                background: ['#eab308', '#22d3ee', '#a855f7', '#22c55e'][i % 4]
                              }}
                            ></div>
                          </div>
                          <span className="bar-value">{cpuVal.toFixed(1)}%</span>
                        </div>
                      )
                    })}
                  </div>
                </div>

                <div className="combined-chart-card">
                  <div className="combined-chart-title">💿 All Container Memory Usage</div>
                  <div className="stacked-bars">
                    {containers.map((c, i) => {
                      const memVal = metrics[c.id]?.memory_bytes || 0
                      const memLimit = metrics[c.id]?.memory_limit_bytes || 268435456
                      const memPct = (memVal / memLimit) * 100
                      return (
                        <div key={c.id} className="stacked-bar-row">
                          <span className="bar-label">{c.name}</span>
                          <div className="bar-track">
                            <div
                              className="bar-fill"
                              style={{
                                width: `${Math.min(memPct, 100)}%`,
                                background: ['#22d3ee', '#a855f7', '#22c55e', '#eab308'][i % 4]
                              }}
                            ></div>
                          </div>
                          <span className="bar-value">{formatBytes(memVal)}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            </div>

            {/* Process Count Info */}
            <div className="analytics-section">
              <h3>👥 Process Information</h3>
              <div className="process-info-cards">
                {containers.map(container => (
                  <div key={container.id} className="process-info-card">
                    <div className="process-info-header">
                      <span>{container.name}</span>
                      <span className="process-count-badge">{metrics[container.id]?.pids || 0} processes</span>
                    </div>
                    <div className="process-info-details">
                      <div>State: <StatusBadge status={container.state} /></div>
                      <div>Init PID: <code>{metrics[container.id]?.init_pid || 'N/A'}</code></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Analytics Page */}
        {currentPage === 'analytics' && (
          <div className="analytics-page">
            <div className="analytics-header">
              <h2 className="page-title">🤖 ML Analytics & Anomaly Detection</h2>
              <a
                className="btn btn-secondary export-btn"
                href={`${API_URL}/api/export/csv`}
                download="minicontainer_metrics.csv"
                target="_blank"
                rel="noopener noreferrer"
              >
                📥 Export CSV
              </a>
            </div>

            {/* Health Scores Grid */}
            <div className="analytics-section">
              <h3>Container Health Scores</h3>
              <div className="health-grid">
                {containers.map(container => {
                  const score = healthScores[container.id] || 100
                  const scoreClass = score >= 80 ? 'good' : score >= 50 ? 'warning' : 'critical'
                  return (
                    <div key={container.id} className={`health-card ${scoreClass}`}>
                      <div className="health-name">{container.name}</div>
                      <div className="health-score">{score.toFixed(0)}</div>
                      <div className="health-label">Health Score</div>
                      <div className={`health-bar`}>
                        <div className="health-fill" style={{ width: `${score}%` }}></div>
                      </div>
                    </div>
                  )
                })}
                {containers.length === 0 && (
                  <div className="empty-analytics">No containers to analyze</div>
                )}
              </div>
            </div>

            {/* Resource Usage Graphs */}
            <div className="analytics-section">
              <h3>📈 Resource Usage Over Time</h3>
              <div className="resource-graphs-grid">
                {containers.map(container => {
                  const h = history[container.id] || { cpu: [], mem: [] }
                  return (
                    <div key={container.id} className="resource-graph-card">
                      <div className="resource-graph-header">
                        <span className="resource-container-name">{container.name}</span>
                        <StatusBadge status={container.state} />
                      </div>
                      <div className="resource-charts">
                        <div className="mini-chart-container">
                          <div className="mini-chart-label">CPU %</div>
                          {h.cpu.length > 1 ? (
                            <LiveChart data={h.cpu} color="#eab308" label="CPU" />
                          ) : (
                            <div className="no-data">No data yet</div>
                          )}
                        </div>
                        <div className="mini-chart-container">
                          <div className="mini-chart-label">Memory (MB)</div>
                          {h.mem.length > 1 ? (
                            <LiveChart data={h.mem.map(b => b / (1024 * 1024))} color="#22d3ee" label="Mem" />
                          ) : (
                            <div className="no-data">No data yet</div>
                          )}
                        </div>
                      </div>
                      <div className="resource-current">
                        <span>Current: {(metrics[container.id]?.cpu_percent || 0).toFixed(1)}% CPU</span>
                        <span>{formatBytes(metrics[container.id]?.memory_bytes || 0)} RAM</span>
                      </div>
                    </div>
                  )
                })}
                {containers.length === 0 && (
                  <div className="empty-analytics">No containers to display graphs for</div>
                )}
              </div>
            </div>

            {/* Anomaly Log */}
            <div className="analytics-section">
              <h3>🚨 Detected Anomalies</h3>
              <div className="anomaly-list">
                {anomalies.length === 0 ? (
                  <div className="no-anomalies">
                    ✅ No anomalies detected - all systems normal
                  </div>
                ) : (
                  anomalies.slice(-20).reverse().map((anomaly, i) => (
                    <div key={i} className={`anomaly-item ${anomaly.severity}`}>
                      <span className="anomaly-time">
                        {new Date(anomaly.timestamp * 1000).toLocaleTimeString()}
                      </span>
                      <span className={`anomaly-badge ${anomaly.severity}`}>
                        {anomaly.severity?.toUpperCase()}
                      </span>
                      <span className="anomaly-type">{anomaly.type}</span>
                      <span className="anomaly-msg">{anomaly.message}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* ML Info */}
            <div className="analytics-section">
              <h3>📊 How It Works</h3>
              <div className="ml-info">
                <div className="ml-card">
                  <h4>Z-Score Detection</h4>
                  <p>Uses statistical Z-score analysis to detect when CPU or memory usage deviates significantly from normal patterns.</p>
                </div>
                <div className="ml-card">
                  <h4>Health Scoring</h4>
                  <p>Combines resource usage, stability metrics, and recent anomalies into a 0-100 health score.</p>
                </div>
                <div className="ml-card">
                  <h4>Trend Analysis</h4>
                  <p>Monitors usage patterns over time to identify increasing/decreasing resource consumption trends.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* About Page */}
        {currentPage === 'about' && (
          <div className="about-page">
            <h2 className="page-title">ℹ️ About MiniContainer</h2>

            <div className="about-section">
              <h3>🐳 What is MiniContainer?</h3>
              <p>
                MiniContainer is a lightweight Linux container runtime built from scratch using
                Linux namespaces, cgroups v2, and a custom filesystem layer. It demonstrates
                core containerization concepts similar to Docker.
              </p>
            </div>

            <div className="about-section">
              <h3>🏗️ Architecture</h3>
              <div className="arch-cards">
                <div className="arch-card">
                  <h4>C Runtime</h4>
                  <p>Low-level container operations: namespace creation, cgroup management, process isolation</p>
                </div>
                <div className="arch-card">
                  <h4>Python Backend</h4>
                  <p>FastAPI server with WebSocket support for real-time metrics and container management</p>
                </div>
                <div className="arch-card">
                  <h4>React Dashboard</h4>
                  <p>Modern UI with live monitoring, container management, and ML analytics</p>
                </div>
              </div>
            </div>

            <div className="about-section">
              <h3>🔧 Key Technologies</h3>
              <div className="tech-grid">
                <span className="tech-tag">Linux Namespaces</span>
                <span className="tech-tag">Cgroups v2</span>
                <span className="tech-tag">setns()</span>
                <span className="tech-tag">FastAPI</span>
                <span className="tech-tag">WebSocket</span>
                <span className="tech-tag">React</span>
                <span className="tech-tag">Z-Score ML</span>
                <span className="tech-tag">Alpine Linux</span>
              </div>
            </div>

            <div className="about-section">
              <h3>📈 Features</h3>
              <ul className="feature-list">
                <li>✅ Create, start, stop, and delete containers</li>
                <li>✅ Real-time CPU, memory, and process monitoring</li>
                <li>✅ Execute commands inside containers with namespace isolation</li>
                <li>✅ ML-based anomaly detection and health scoring</li>
                <li>✅ Resource limits (CPU, memory, PIDs)</li>
                <li>✅ Live WebSocket updates</li>
              </ul>
            </div>
          </div>
        )}
      </main>

      {/* Modals */}
      <CreateContainerModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={createContainer}
      />

      {monitorContainer && (
        <MonitorModal
          container={monitorContainer}
          metrics={metrics[monitorContainer.id]}
          history={history[monitorContainer.id]}
          onClose={() => setMonitorContainer(null)}
        />
      )}

      <ExecuteCommandModal
        container={execContainer}
        isOpen={!!execContainer}
        onClose={() => setExecContainer(null)}
        onExecute={executeCommand}
      />

      {/* Notification */}
      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.type === 'success' ? '✓' : '✗'} {notification.message}
        </div>
      )}
    </div>
  )
}

export default App
