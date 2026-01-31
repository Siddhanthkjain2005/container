'use client';

import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const API_URL = 'https://diphyodont-zachery-multifamilial.ngrok-free.dev'
const WS_URL = 'wss://diphyodont-zachery-multifamilial.ngrok-free.dev/ws'

// Icon Components
const Icons = {
  Box: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
      <path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>
    </svg>
  ),
  Play: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="6 3 20 12 6 21 6 3"/>
    </svg>
  ),
  Cpu: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/>
      <path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>
    </svg>
  ),
  Memory: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 19v-3"/><path d="M10 19v-3"/><path d="M14 19v-3"/><path d="M18 19v-3"/>
      <path d="M8 11V9"/><path d="M16 11V9"/><path d="M12 11V9"/>
      <path d="M2 15h20"/><path d="M2 7a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v1.1a2 2 0 0 0 0 3.837V17a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-5.1a2 2 0 0 0 0-3.837Z"/>
    </svg>
  ),
  Activity: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>
    </svg>
  ),
  Server: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="20" height="8" x="2" y="2" rx="2" ry="2"/><rect width="20" height="8" x="2" y="14" rx="2" ry="2"/>
      <line x1="6" x2="6.01" y1="6" y2="6"/><line x1="6" x2="6.01" y1="18" y2="18"/>
    </svg>
  ),
  Clock: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
    </svg>
  ),
  Zap: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>
    </svg>
  ),
  Terminal: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>
    </svg>
  ),
  Eye: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
  ),
  Stop: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect width="14" height="14" x="5" y="5" rx="2"/>
    </svg>
  ),
  Trash: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
    </svg>
  ),
  Plus: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14"/><path d="M12 5v14"/>
    </svg>
  ),
  Refresh: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
      <path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
      <path d="M8 16H3v5"/>
    </svg>
  ),
  X: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
    </svg>
  ),
  Download: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>
    </svg>
  ),
  Heart: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
    </svg>
  ),
  AlertTriangle: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>
    </svg>
  ),
  BarChart: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>
    </svg>
  ),
  Brain: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
      <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/>
      <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/>
      <path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M19.938 10.5a4 4 0 0 1 .585.396"/>
      <path d="M6 18a4 4 0 0 1-1.967-.516"/><path d="M19.967 17.484A4 4 0 0 1 18 18"/>
    </svg>
  ),
  Info: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
    </svg>
  ),
  Layers: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/>
      <path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>
    </svg>
  ),
  Hash: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/><line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/>
    </svg>
  ),
  Users: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
      <path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  ),
  Triangle: () => (
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2L2 19h20L12 2z"/>
    </svg>
  ),
  TrendUp: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>
    </svg>
  ),
  TrendDown: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/>
    </svg>
  ),
  Gauge: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>
    </svg>
  ),
  PieChart: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>
    </svg>
  ),
  Sparkles: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
      <path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>
    </svg>
  )
}

// Format bytes to human readable
function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// Format duration to human readable
function formatDuration(seconds) {
  if (!seconds || seconds === 0) return '0s'
  if (seconds < 60) return `${seconds.toFixed(0)}s`
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`
  return `${(seconds / 3600).toFixed(1)}h`
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

// Trend Indicator Component
function TrendIndicator({ trend, size = 'sm' }) {
  if (!trend || trend.direction === 'stable') {
    return <span className={`trend-indicator stable ${size}`}>→ Stable</span>
  }
  
  const isUp = trend.direction === 'increasing'
  return (
    <span className={`trend-indicator ${isUp ? 'up' : 'down'} ${size}`}>
      {isUp ? <Icons.TrendUp /> : <Icons.TrendDown />}
      <span>{trend.description || (isUp ? 'Increasing' : 'Decreasing')}</span>
    </span>
  )
}

// Donut/Pie Chart Component
function DonutChart({ value, max = 100, color = '#06b6d4', size = 80, strokeWidth = 8, label = '' }) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const percent = Math.min(value / max, 1)
  const offset = circumference - (percent * circumference)
  
  return (
    <div className="donut-chart" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size/2} ${size/2})`}
          style={{ transition: 'stroke-dashoffset 0.3s ease' }}
        />
      </svg>
      <div className="donut-center">
        <span className="donut-value">{value.toFixed(0)}</span>
        {label && <span className="donut-label">{label}</span>}
      </div>
    </div>
  )
}

// Histogram Bar Chart Component
function HistogramChart({ data, color = '#f59e0b', height = 100 }) {
  if (!data || !data.counts || data.counts.length === 0) {
    return (
      <div className="chart-placeholder" style={{ height }}>
        <span>No distribution data</span>
      </div>
    )
  }
  
  const maxCount = Math.max(...data.counts, 1)
  const barWidth = 100 / data.counts.length
  
  return (
    <div className="histogram-chart" style={{ height }}>
      <div className="histogram-bars">
        {data.counts.map((count, i) => (
          <div
            key={i}
            className="histogram-bar"
            style={{
              width: `${barWidth}%`,
              height: `${(count / maxCount) * 100}%`,
              backgroundColor: color,
              opacity: 0.7 + (0.3 * (count / maxCount))
            }}
            title={`${data.labels?.[i] || i}: ${count}`}
          />
        ))}
      </div>
      <div className="histogram-labels">
        {data.labels && data.labels.length <= 5 && data.labels.map((label, i) => (
          <span key={i} style={{ width: `${barWidth}%` }}>{label}</span>
        ))}
      </div>
    </div>
  )
}

// Score Gauge Component
function ScoreGauge({ score, label, color }) {
  const scoreClass = score >= 80 ? 'good' : score >= 50 ? 'warning' : 'critical'
  const gaugeColor = color || (score >= 80 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444')
  
  return (
    <div className={`score-gauge ${scoreClass}`}>
      <DonutChart value={score} max={100} color={gaugeColor} size={70} strokeWidth={6} />
      <span className="score-gauge-label">{label}</span>
    </div>
  )
}

// Mini Sparkline Component  
function Sparkline({ data, color = '#06b6d4', height = 30, width = 100 }) {
  if (!data || data.length < 2) return null
  
  const max = Math.max(...data, 1)
  const min = Math.min(...data, 0)
  const range = max - min || 1
  
  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width
    const y = height - ((val - min) / range) * height
    return `${x},${y}`
  }).join(' ')
  
  return (
    <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

// Modern Area Chart Component
function AreaChart({ data, color, gradientId, height = 120 }) {
  if (!data || data.length < 2) {
    return (
      <div className="chart-placeholder" style={{ height }}>
        <span>Waiting for data...</span>
      </div>
    )
  }

  const width = 400
  const padding = { top: 20, right: 20, bottom: 30, left: 50 }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  const max = Math.max(...data, 1)
  const min = 0

  // Generate smooth path using cardinal spline
  const points = data.map((val, i) => ({
    x: padding.left + (i / (data.length - 1)) * chartWidth,
    y: padding.top + chartHeight - ((val - min) / (max - min)) * chartHeight
  }))

  // Create smooth curve
  const linePath = points.reduce((path, point, i) => {
    if (i === 0) return `M ${point.x} ${point.y}`
    const prev = points[i - 1]
    const cp1x = prev.x + (point.x - prev.x) / 3
    const cp2x = prev.x + 2 * (point.x - prev.x) / 3
    return `${path} C ${cp1x} ${prev.y} ${cp2x} ${point.y} ${point.x} ${point.y}`
  }, '')

  const areaPath = `${linePath} L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${padding.left} ${padding.top + chartHeight} Z`

  // Y-axis labels
  const yLabels = [0, max * 0.5, max].map((val, i) => ({
    value: val.toFixed(1),
    y: padding.top + chartHeight - (i * chartHeight / 2)
  }))

  // X-axis labels (time indicators)
  const xLabels = ['30s ago', '15s ago', 'Now']

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="area-chart-svg" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="50%" stopColor={color} stopOpacity="0.15" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
        <filter id={`glow-${gradientId}`}>
          <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      {/* Grid lines */}
      {[0, 0.5, 1].map((ratio, i) => (
        <line
          key={i}
          x1={padding.left}
          y1={padding.top + chartHeight * (1 - ratio)}
          x2={width - padding.right}
          y2={padding.top + chartHeight * (1 - ratio)}
          stroke="rgba(255,255,255,0.06)"
          strokeDasharray="4 4"
        />
      ))}

      {/* Area fill */}
      <path d={areaPath} fill={`url(#${gradientId})`} />

      {/* Line */}
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter={`url(#glow-${gradientId})`}
      />

      {/* Current value dot */}
      <circle
        cx={points[points.length - 1].x}
        cy={points[points.length - 1].y}
        r="5"
        fill={color}
        filter={`url(#glow-${gradientId})`}
      />
      <circle
        cx={points[points.length - 1].x}
        cy={points[points.length - 1].y}
        r="3"
        fill="#fff"
      />

      {/* Y-axis labels */}
      {yLabels.map((label, i) => (
        <text
          key={i}
          x={padding.left - 8}
          y={label.y + 4}
          textAnchor="end"
          className="chart-label"
        >
          {label.value}
        </text>
      ))}

      {/* X-axis labels */}
      {xLabels.map((label, i) => (
        <text
          key={i}
          x={padding.left + (i * chartWidth / 2)}
          y={height - 8}
          textAnchor="middle"
          className="chart-label"
        >
          {label}
        </text>
      ))}
    </svg>
  )
}

// Running Container Section with Dual Live Charts
function RunningContainersSection({ containers, metrics, history }) {
  const runningContainers = containers.filter(c => c.state === 'running')

  if (runningContainers.length === 0) return null

  return (
    <div className="live-section">
      <div className="section-header">
        <div className="section-title">
          <span className="live-indicator"></span>
          <h2>Live Monitoring</h2>
          <span className="badge">{runningContainers.length} active</span>
        </div>
      </div>

      <div className="live-grid">
        {runningContainers.map(container => {
          const m = metrics[container.id] || {}
          const h = history[container.id] || { cpu: [], mem: [] }
          const memPercent = m.memory_bytes && m.memory_limit_bytes > 0
            ? (m.memory_bytes / m.memory_limit_bytes * 100) : 0

          return (
            <div key={container.id} className="live-card">
              <div className="live-card-header">
                <div className="live-card-title">
                  <span className="icon-wrapper blue"><Icons.Box /></span>
                  <span>{container.name}</span>
                </div>
                <StatusBadge status={container.state} />
              </div>

              <div className="live-stats-row">
                <div className="live-stat">
                  <span className="live-stat-label">CPU</span>
                  <span className="live-stat-value amber">{(m.cpu_percent || 0).toFixed(1)}%</span>
                </div>
                <div className="live-stat">
                  <span className="live-stat-label">Memory</span>
                  <span className="live-stat-value cyan">{formatBytes(m.memory_bytes || 0)}</span>
                </div>
                <div className="live-stat">
                  <span className="live-stat-label">Mem %</span>
                  <span className="live-stat-value">{memPercent.toFixed(0)}%</span>
                </div>
                <div className="live-stat">
                  <span className="live-stat-label">Processes</span>
                  <span className="live-stat-value">{m.pids || 0}</span>
                </div>
              </div>

              <div className="charts-row">
                <div className="chart-box">
                  <div className="chart-box-header">
                    <div className="chart-legend">
                      <span className="legend-dot amber"></span>
                      <span>CPU Usage</span>
                    </div>
                    <span className="chart-value amber">{(m.cpu_percent || 0).toFixed(1)}%</span>
                  </div>
                  <AreaChart data={h.cpu} color="#f59e0b" gradientId={`cpu-${container.id}`} height={100} />
                </div>

                <div className="chart-box">
                  <div className="chart-box-header">
                    <div className="chart-legend">
                      <span className="legend-dot cyan"></span>
                      <span>Memory Usage</span>
                    </div>
                    <span className="chart-value cyan">{formatBytes(m.memory_bytes || 0)}</span>
                  </div>
                  <AreaChart data={h.mem.map(v => v / 1048576)} color="#06b6d4" gradientId={`mem-${container.id}`} height={100} />
                </div>
              </div>
            </div>
          )
        })}
      </div>
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
      <div className="card-header">
        <div className="card-info">
          <div className="card-title-row">
            <span className="icon-wrapper subtle"><Icons.Box /></span>
            <h3>{container.name}</h3>
          </div>
          <code className="container-id">{container.id}</code>
        </div>
        <StatusBadge status={container.state} />
      </div>

      <div className="card-metrics">
        <div className="metric-item">
          <div className="metric-left">
            <span className="icon-sm amber"><Icons.Cpu /></span>
            <span className="metric-name">CPU</span>
          </div>
          <div className="metric-bar-wrapper">
            <div className="metric-bar">
              <div className="metric-fill amber" style={{ width: `${Math.min(m.cpu_percent || 0, 100)}%` }}></div>
            </div>
          </div>
          <span className="metric-value">{(m.cpu_percent || 0).toFixed(1)}%</span>
        </div>

        <div className="metric-item">
          <div className="metric-left">
            <span className="icon-sm cyan"><Icons.Memory /></span>
            <span className="metric-name">Memory</span>
          </div>
          <div className="metric-bar-wrapper">
            <div className="metric-bar">
              <div className="metric-fill cyan" style={{ width: `${Math.min(memPercent, 100)}%` }}></div>
            </div>
          </div>
          <span className="metric-value">{formatBytes(m.memory_bytes || 0)}</span>
        </div>

        <div className="metric-item">
          <div className="metric-left">
            <span className="icon-sm purple"><Icons.Users /></span>
            <span className="metric-name">PIDs</span>
          </div>
          <span className="metric-value" style={{ marginLeft: 'auto' }}>{m.pids || 0}</span>
        </div>
      </div>

      <div className="card-actions">
        <button className="btn btn-secondary btn-icon-text" onClick={() => onMonitor(container)}>
          <Icons.Eye /> Details
        </button>

        {container.state === 'running' ? (
          <button
            className="btn btn-danger btn-icon-text"
            onClick={() => onAction('stop', container.id)}
            disabled={actionLoading}
          >
            <Icons.Stop /> Stop
          </button>
        ) : (
          <button
            className="btn btn-success btn-icon-text"
            onClick={() => onExec(container)}
            disabled={actionLoading}
          >
            <Icons.Play /> Start
          </button>
        )}

        <button
          className="btn btn-ghost btn-icon-only"
          onClick={() => onAction('delete', container.id)}
          disabled={actionLoading}
          title="Delete container"
        >
          <Icons.Trash />
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
      setProcesses(data.processes || [])
    } catch (e) {
      console.error('Failed to fetch processes:', e)
      setProcesses([])
    }
    setLoadingProcesses(false)
  }

  // Get a clean display version of the running command
  const getCleanCommand = () => {
    if (processes.length === 0) return null
    const cmd = processes[0].command || ''
    // Extract the label from our commands like "[Variable CPU]", "[Spike Demo]", etc.
    const labelMatch = cmd.match(/\[([^\]]+)\]/)
    if (labelMatch) {
      return labelMatch[1]
    }
    // If it's a shell script, show description
    if (cmd.includes('while') || cmd.includes('for')) {
      return 'Stress Test Running'
    }
    if (cmd.includes('dd if=/dev/zero')) {
      return 'Memory Allocation Test'
    }
    if (cmd.includes('sleep')) {
      return 'Sleep/Idle Process'
    }
    // Truncate long commands
    return cmd.length > 50 ? cmd.substring(0, 50) + '...' : cmd
  }
  
  const runningCommand = getCleanCommand()
  const fullCommand = processes.length > 0 ? processes[0].command : null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <span className="icon-wrapper blue"><Icons.Box /></span>
            <h2>{container.name}</h2>
          </div>
          <button className="btn btn-ghost btn-icon-only" onClick={onClose}>
            <Icons.X />
          </button>
        </div>

        <div className="modal-body">
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Container ID</span>
              <code className="info-value">{container.id}</code>
            </div>
            <div className="info-item">
              <span className="info-label">Init PID</span>
              <span className="info-value mono">{m.init_pid || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">State</span>
              <StatusBadge status={container.state} />
            </div>
          </div>

          {runningCommand && (
            <div className="command-banner" title={fullCommand}>
              <span className="command-label">Running</span>
              <code className="command-code">{runningCommand}</code>
            </div>
          )}

          <div className="stats-grid">
            <div className="stat-box">
              <div className="stat-box-header">
                <span className="icon-sm amber"><Icons.Cpu /></span>
                <span>CPU Usage</span>
              </div>
              <div className="stat-box-value">{(m.cpu_percent || 0).toFixed(1)}%</div>
              <div className="stat-box-bar">
                <div className="stat-fill amber" style={{ width: `${Math.min(m.cpu_percent || 0, 100)}%` }}></div>
              </div>
            </div>

            <div className="stat-box">
              <div className="stat-box-header">
                <span className="icon-sm cyan"><Icons.Memory /></span>
                <span>Memory</span>
              </div>
              <div className="stat-box-value">{formatBytes(m.memory_bytes || 0)}</div>
              <div className="stat-box-detail">of {formatBytes(m.memory_limit_bytes || 0)} ({memPercent.toFixed(1)}%)</div>
              <div className="stat-box-bar">
                <div className="stat-fill cyan" style={{ width: `${Math.min(memPercent, 100)}%` }}></div>
              </div>
            </div>

            <div className="stat-box">
              <div className="stat-box-header">
                <span className="icon-sm purple"><Icons.Users /></span>
                <span>Processes</span>
              </div>
              <div className="stat-box-value">{m.pids || 0}</div>
              <button className="btn btn-sm btn-secondary" onClick={fetchProcesses} disabled={loadingProcesses}>
                {loadingProcesses ? 'Loading...' : 'View Processes'}
              </button>
            </div>

            <div className="stat-box">
              <div className="stat-box-header">
                <span className="icon-sm green"><Icons.Activity /></span>
                <span>Status</span>
              </div>
              <div className="stat-box-status">
                <StatusBadge status={container.state} />
              </div>
            </div>
          </div>

          {showProcesses && (
            <div className="process-panel">
              <div className="process-header">
                <h4>Running Processes</h4>
                <button className="btn btn-sm btn-ghost" onClick={() => setShowProcesses(false)}>
                  <Icons.X />
                </button>
              </div>
              {loadingProcesses ? (
                <div className="process-loading">
                  <div className="spinner"></div>
                  <span>Loading processes...</span>
                </div>
              ) : processes.length === 0 ? (
                <div className="process-empty">
                  <span className="icon-lg muted"><Icons.Server /></span>
                  <div className="empty-title">No Running Processes</div>
                  <div className="empty-desc">
                    Container is stopped or idle. Start a command to see processes.
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
                          <td className="mono">{p.pid}</td>
                          <td className="mono">{p.ppid}</td>
                          <td>{p.name}</td>
                          <td><span className={`state-badge ${p.state_code}`}>{p.state}</span></td>
                          <td className="mono">{p.memory_human}</td>
                          <td className="desc" title={p.command}>{p.description || 'User process'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {(h.cpu.length > 1 || h.mem.length > 1) && (
            <div className="charts-section">
              <h4>Resource History</h4>
              <div className="charts-grid-2">
                {h.cpu.length > 1 && (
                  <div className="chart-panel">
                    <div className="chart-panel-title">CPU History</div>
                    <AreaChart data={h.cpu} color="#f59e0b" gradientId="modal-cpu" height={120} />
                  </div>
                )}
                {h.mem.length > 1 && (
                  <div className="chart-panel">
                    <div className="chart-panel-title">Memory History (MB)</div>
                    <AreaChart data={h.mem.map(b => b / (1024 * 1024))} color="#06b6d4" gradientId="modal-mem" height={120} />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Execute Command Modal
function ExecuteCommandModal({ container, isOpen, onClose, onExecute }) {
  const [selectedCmd, setSelectedCmd] = useState('1')
  const [duration, setDuration] = useState(60)
  const [memorySize, setMemorySize] = useState(50)
  const [customCmd, setCustomCmd] = useState('echo Hello from container')
  const [executing, setExecuting] = useState(false)

  if (!isOpen || !container) return null

  const commands = [
    { id: '1', icon: Icons.Cpu, name: 'Variable CPU Load', desc: 'Alternating CPU patterns - triggers anomaly detection', color: 'amber' },
    { id: '2', icon: Icons.Memory, name: 'Memory Allocation', desc: 'Allocate memory - shows memory limits', color: 'cyan' },
    { id: '3', icon: Icons.Zap, name: 'CPU Spike Pattern', desc: 'Bursts & idle - best for anomaly demos', color: 'pink' },
    { id: '4', icon: Icons.Activity, name: 'Gradual Increase', desc: 'Slowly increasing load - shows trend detection', color: 'green' },
    { id: '5', icon: Icons.Clock, name: 'Normal Workload', desc: 'Stable load - baseline for health scores', color: 'blue' },
    { id: '6', icon: Icons.Terminal, name: 'Custom Command', desc: 'Enter your own shell command', color: 'purple' },
  ]

  const handleExecute = async () => {
    setExecuting(true)
    await onExecute(container.id, selectedCmd, { duration, memorySize, customCmd })
    setExecuting(false)
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <span className="icon-wrapper green"><Icons.Terminal /></span>
            <h2>Execute Command</h2>
          </div>
          <button className="btn btn-ghost btn-icon-only" onClick={onClose}>
            <Icons.X />
          </button>
        </div>

        <div className="modal-body">
          <div className="exec-info">
            <span className="exec-label">Container</span>
            <span className="exec-name">{container.name}</span>
          </div>

          <div className="command-grid">
            {commands.map(cmd => (
              <div
                key={cmd.id}
                className={`command-option ${selectedCmd === cmd.id ? 'selected' : ''}`}
                onClick={() => setSelectedCmd(cmd.id)}
              >
                <span className={`icon-wrapper ${cmd.color}`}><cmd.icon /></span>
                <div className="command-option-info">
                  <span className="command-option-name">{cmd.name}</span>
                  <span className="command-option-desc">{cmd.desc}</span>
                </div>
                <span className="radio-dot">{selectedCmd === cmd.id ? '●' : '○'}</span>
              </div>
            ))}
          </div>

          {['1', '2', '3', '4', '5'].includes(selectedCmd) && (
            <div className="form-group">
              <label>Duration: <strong>{duration}s</strong></label>
              <input
                type="range"
                min="10"
                max="300"
                value={duration}
                onChange={e => setDuration(parseInt(e.target.value))}
              />
            </div>
          )}

          {['2', '3'].includes(selectedCmd) && (
            <div className="form-group">
              <label>Memory Size: <strong>{memorySize} MB</strong></label>
              <input
                type="range"
                min="10"
                max="200"
                value={memorySize}
                onChange={e => setMemorySize(parseInt(e.target.value))}
              />
            </div>
          )}

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
          <button className="btn btn-primary" onClick={handleExecute} disabled={executing}>
            {executing ? 'Executing...' : 'Execute'}
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
          <div className="modal-title">
            <span className="icon-wrapper blue"><Icons.Plus /></span>
            <h2>Create Container</h2>
          </div>
          <button className="btn btn-ghost btn-icon-only" onClick={onClose}>
            <Icons.X />
          </button>
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
              <label>Memory Limit: <strong>{memory} MB</strong></label>
              <input
                type="range"
                min="64"
                max="2048"
                value={memory}
                onChange={e => setMemory(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>CPU Limit: <strong>{cpus}%</strong></label>
              <input
                type="range"
                min="5"
                max="100"
                value={cpus}
                onChange={e => setCpus(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Max Processes: <strong>{pids}</strong></label>
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
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [healthScores, setHealthScores] = useState({})
  const [stabilityScores, setStabilityScores] = useState({})
  const [efficiencyScores, setEfficiencyScores] = useState({})
  const [containerAnalytics, setContainerAnalytics] = useState({})
  const [systemStats, setSystemStats] = useState({})
  const [anomalies, setAnomalies] = useState([])
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

            if (data.health_scores) {
              setHealthScores(data.health_scores)
            }
            if (data.stability_scores) {
              setStabilityScores(data.stability_scores)
            }
            if (data.efficiency_scores) {
              setEfficiencyScores(data.efficiency_scores)
            }
            if (data.container_analytics) {
              setContainerAnalytics(data.container_analytics)
            }
            if (data.system_stats) {
              setSystemStats(data.system_stats)
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
        showNotification(`Container ${action}ed successfully`, 'success')
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
        showNotification('Container created successfully', 'success')
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

  const executeCommand = async (containerId, cmdType, options) => {
    const { duration, memorySize, customCmd } = options
    let command = ''

    switch (cmdType) {
      case '1':
        // Variable CPU Load - alternates between high, medium, low - good for showing ML adaptation
        command = `echo '[Variable CPU] Running for ${duration}s'; END=$(($(date +%s) + ${duration})); while [ $(date +%s) -lt $END ]; do echo 'HIGH'; i=0; while [ $i -lt 800000 ]; do i=$((i+1)); done; echo 'LOW'; sleep 0.5; i=0; while [ $i -lt 200000 ]; do i=$((i+1)); done; sleep 0.3; done; echo '[Complete]'`
        break
      case '2':
        // Memory Allocation - allocate and hold memory to show memory limits
        command = `echo '[Memory Test] Allocating ${memorySize}MB'; dd if=/dev/zero of=/dev/shm/memtest bs=1M count=${memorySize} 2>/dev/null && echo '[Holding memory for ${duration}s]' && sleep ${duration} && rm -f /dev/shm/memtest && echo '[Memory Released]'`
        break
      case '3':
        // CPU Spike Pattern - dramatic spikes for anomaly detection demos
        command = `echo '[Spike Demo] Running for ${duration}s'; END=$(($(date +%s) + ${duration})); while [ $(date +%s) -lt $END ]; do echo 'SPIKE!'; i=0; while [ $i -lt 1500000 ]; do i=$((i+1)); done; echo 'idle'; sleep 2; done; echo '[Complete]'`
        break
      case '4':
        // Gradual Increase - slowly ramp up CPU for trend detection
        command = `echo '[Gradual Increase] Running for ${duration}s'; intensity=100000; END=$(($(date +%s) + ${duration})); while [ $(date +%s) -lt $END ]; do echo "Load: $intensity"; i=0; while [ $i -lt $intensity ]; do i=$((i+1)); done; intensity=$((intensity + 50000)); sleep 0.5; done; echo '[Complete]'`
        break
      case '5':
        // Normal Workload - stable moderate load for baseline
        command = `echo '[Normal Workload] Running for ${duration}s'; END=$(($(date +%s) + ${duration})); while [ $(date +%s) -lt $END ]; do i=0; while [ $i -lt 300000 ]; do i=$((i+1)); done; sleep 0.2; done; echo '[Complete]'`
        break
      case '6':
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
        showNotification('Command started successfully', 'success')
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
          <span className="logo-icon"><Icons.Triangle /></span>
          <h1>Mini<span>Container</span></h1>
        </div>

        <nav className="nav">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: Icons.Layers },
            { id: 'stats', label: 'Stats', icon: Icons.BarChart },
            { id: 'analytics', label: 'ML Analytics', icon: Icons.Brain },
            { id: 'about', label: 'About', icon: Icons.Info },
          ].map(tab => (
            <button
              key={tab.id}
              className={`nav-item ${currentPage === tab.id ? 'active' : ''}`}
              onClick={() => setCurrentPage(tab.id)}
            >
              <tab.icon />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>

        <div className="header-actions">
          <div className={`status-indicator ${wsStatus}`}>
            <span className="status-dot"></span>
            <span>{wsStatus === 'connected' ? 'Live' : 'Offline'}</span>
          </div>
        </div>
      </header>

      <main className="main">
        {/* Stats Overview */}
        <div className="stats-row">
          <div className="stat-card blue">
            <span className="stat-icon"><Icons.Box /></span>
            <div className="stat-content">
              <span className="stat-value">{containers.length}</span>
              <span className="stat-label">Total Containers</span>
            </div>
          </div>
          <div className="stat-card green">
            <span className="stat-icon"><Icons.Play /></span>
            <div className="stat-content">
              <span className="stat-value">{runningCount}</span>
              <span className="stat-label">Running</span>
            </div>
          </div>
          <div className="stat-card amber">
            <span className="stat-icon"><Icons.Cpu /></span>
            <div className="stat-content">
              <span className="stat-value">{totalCpu.toFixed(1)}%</span>
              <span className="stat-label">Total CPU</span>
            </div>
          </div>
          <div className="stat-card pink">
            <span className="stat-icon"><Icons.Memory /></span>
            <div className="stat-content">
              <span className="stat-value">{formatBytes(totalMem)}</span>
              <span className="stat-label">Total Memory</span>
            </div>
          </div>
        </div>

        {currentPage === 'dashboard' && (
          <>
            <RunningContainersSection
              containers={containers}
              metrics={metrics}
              history={history}
            />

            <div className="section-header">
              <h2>All Containers</h2>
              <div className="section-actions">
                <button className="btn btn-secondary btn-icon-text" onClick={fetchContainers}>
                  <Icons.Refresh /> Refresh
                </button>
                <button className="btn btn-primary btn-icon-text" onClick={() => setShowCreateModal(true)}>
                  <Icons.Plus /> Create
                </button>
              </div>
            </div>

            {loading ? (
              <div className="loading-state">
                <div className="spinner"></div>
                <span>Loading containers...</span>
              </div>
            ) : containers.length === 0 ? (
              <div className="empty-state">
                <span className="icon-lg muted"><Icons.Box /></span>
                <h3>No Containers Yet</h3>
                <p>Create your first container to get started</p>
                <button className="btn btn-primary btn-icon-text" onClick={() => setShowCreateModal(true)}>
                  <Icons.Plus /> Create Container
                </button>
              </div>
            ) : (
              <div className="container-grid">
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

        {currentPage === 'stats' && (
          <div className="page-content">
            <div className="page-header">
              <h2>Container Statistics</h2>
              <a
                className="btn btn-secondary btn-icon-text"
                href={`${API_URL}/api/export/csv`}
                download="minicontainer_metrics.csv"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Icons.Download /> Export CSV
              </a>
            </div>

            <div className="section">
              <h3>System Overview</h3>
              <div className="overview-grid">
                <div className="overview-card">
                  <span className="overview-icon blue"><Icons.Box /></span>
                  <span className="overview-value">{containers.length}</span>
                  <span className="overview-label">Total Containers</span>
                </div>
                <div className="overview-card">
                  <span className="overview-icon green"><Icons.Play /></span>
                  <span className="overview-value">{containers.filter(c => c.state === 'running').length}</span>
                  <span className="overview-label">Running</span>
                </div>
                <div className="overview-card">
                  <span className="overview-icon amber"><Icons.Cpu /></span>
                  <span className="overview-value">{totalCpu.toFixed(1)}%</span>
                  <span className="overview-label">Total CPU</span>
                </div>
                <div className="overview-card">
                  <span className="overview-icon cyan"><Icons.Memory /></span>
                  <span className="overview-value">{formatBytes(totalMem)}</span>
                  <span className="overview-label">Total Memory</span>
                </div>
              </div>
            </div>

            <div className="section">
              <h3>Container Details</h3>
              <div className="details-grid">
                {containers.map(container => {
                  const m = metrics[container.id] || {}
                  return (
                    <div key={container.id} className="detail-card">
                      <div className="detail-header">
                        <span className="detail-name">{container.name}</span>
                        <StatusBadge status={container.state} />
                      </div>
                      <div className="detail-grid">
                        <div className="detail-item">
                          <span className="detail-key">Container ID</span>
                          <code className="detail-value">{container.id}</code>
                        </div>
                        <div className="detail-item">
                          <span className="detail-key">Init PID</span>
                          <span className="detail-value mono">{m.init_pid || 'N/A'}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-key">CPU Usage</span>
                          <span className="detail-value">{(m.cpu_percent || 0).toFixed(1)}%</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-key">Memory Used</span>
                          <span className="detail-value">{formatBytes(m.memory_bytes || 0)}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-key">Memory Limit</span>
                          <span className="detail-value">{formatBytes(m.memory_limit_bytes || 0)}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-key">Processes</span>
                          <span className="detail-value">{m.pids || 0}</span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-key">CPU Time</span>
                          <span className="detail-value amber">
                            {m.cpu_usec ? (
                              m.cpu_usec >= 1000000
                                ? `${(m.cpu_usec / 1000000).toFixed(2)}s`
                                : m.cpu_usec >= 1000
                                  ? `${(m.cpu_usec / 1000).toFixed(2)}ms`
                                  : `${m.cpu_usec}us`
                            ) : '0us'}
                          </span>
                        </div>
                        <div className="detail-item">
                          <span className="detail-key">Health Score</span>
                          <span className={`detail-value ${(healthScores[container.id] || 100) >= 80 ? 'green' : 'amber'}`}>
                            {(healthScores[container.id] || 100).toFixed(0)}/100
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })}
                {containers.length === 0 && (
                  <div className="empty-section">No containers available. Create one to see stats.</div>
                )}
              </div>
            </div>

            <div className="section">
              <h3>Resource Graphs</h3>
              <div className="graph-grid">
                {containers.map(container => {
                  const m = metrics[container.id] || {}
                  const h = history[container.id] || { cpu: [], mem: [] }
                  const cpuTimeSeconds = m.cpu_usec ? (m.cpu_usec / 1000000) : 0
                  const memPercent = m.memory_bytes && m.memory_limit_bytes > 0
                    ? (m.memory_bytes / m.memory_limit_bytes * 100) : 0

                  return (
                    <div key={container.id} className="graph-card">
                      <div className="graph-header">
                        <span className="graph-name">{container.name}</span>
                        <StatusBadge status={container.state} />
                      </div>

                      <div className="graph-stats">
                        <div className="graph-stat">
                          <span className="icon-sm amber"><Icons.Clock /></span>
                          <div className="graph-stat-info">
                            <span className="graph-stat-label">CPU Time</span>
                            <span className="graph-stat-value">
                              {cpuTimeSeconds >= 3600
                                ? `${(cpuTimeSeconds / 3600).toFixed(2)}h`
                                : cpuTimeSeconds >= 60
                                  ? `${(cpuTimeSeconds / 60).toFixed(2)}m`
                                  : `${cpuTimeSeconds.toFixed(2)}s`
                              }
                            </span>
                          </div>
                        </div>
                        <div className="graph-stat">
                          <span className="icon-sm cyan"><Icons.Users /></span>
                          <div className="graph-stat-info">
                            <span className="graph-stat-label">Processes</span>
                            <span className="graph-stat-value">{m.pids || 0}</span>
                          </div>
                        </div>
                        <div className="graph-stat">
                          <span className="icon-sm green"><Icons.Heart /></span>
                          <div className="graph-stat-info">
                            <span className="graph-stat-label">Health</span>
                            <span className="graph-stat-value">{(healthScores[container.id] || 100).toFixed(0)}/100</span>
                          </div>
                        </div>
                      </div>

                      <div className="graph-charts">
                        <div className="mini-chart">
                          <div className="mini-chart-header">
                            <span className="mini-chart-label">CPU Usage</span>
                            <span className="mini-chart-value amber">{(m.cpu_percent || 0).toFixed(1)}%</span>
                          </div>
                          <AreaChart data={h.cpu} color="#f59e0b" gradientId={`stats-cpu-${container.id}`} height={80} />
                        </div>
                        <div className="mini-chart">
                          <div className="mini-chart-header">
                            <span className="mini-chart-label">Memory</span>
                            <span className="mini-chart-value cyan">{memPercent.toFixed(1)}%</span>
                          </div>
                          <AreaChart data={h.mem.map(v => v / 1048576)} color="#06b6d4" gradientId={`stats-mem-${container.id}`} height={80} />
                        </div>
                      </div>

                      <div className="bar-chart">
                        <div className="bar-row">
                          <span className="bar-label">CPU</span>
                          <div className="bar-track">
                            <div className="bar-fill amber" style={{ width: `${Math.min(m.cpu_percent || 0, 100)}%` }}></div>
                          </div>
                          <span className="bar-value">{(m.cpu_percent || 0).toFixed(1)}%</span>
                        </div>
                        <div className="bar-row">
                          <span className="bar-label">Memory</span>
                          <div className="bar-track">
                            <div className="bar-fill cyan" style={{ width: `${Math.min(memPercent, 100)}%` }}></div>
                          </div>
                          <span className="bar-value">{memPercent.toFixed(1)}%</span>
                        </div>
                        <div className="bar-row">
                          <span className="bar-label">Health</span>
                          <div className="bar-track">
                            <div className="bar-fill green" style={{ width: `${healthScores[container.id] || 100}%` }}></div>
                          </div>
                          <span className="bar-value">{(healthScores[container.id] || 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
                {containers.length === 0 && (
                  <div className="empty-section">No containers available. Create one to see graphs.</div>
                )}
              </div>
            </div>
          </div>
        )}

        {currentPage === 'analytics' && (
          <div className="page-content">
            <div className="page-header">
              <h2>ML Analytics & Anomaly Detection</h2>
              <div className="header-actions-group">
                <a
                  className="btn btn-secondary btn-icon-text"
                  href={`${API_URL}/api/export/csv`}
                  download="minicontainer_metrics.csv"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Icons.Download /> Metrics CSV
                </a>
                <a
                  className="btn btn-secondary btn-icon-text"
                  href={`${API_URL}/api/export/anomalies`}
                  download="minicontainer_anomalies.csv"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Icons.Download /> Anomalies CSV
                </a>
              </div>
            </div>

            {/* System Overview Stats */}
            <div className="section">
              <h3><Icons.PieChart /> System Overview</h3>
              <div className="system-overview-grid">
                <div className="overview-stat-card">
                  <span className="overview-stat-icon blue"><Icons.Box /></span>
                  <div className="overview-stat-content">
                    <span className="overview-stat-value">{containers.length}</span>
                    <span className="overview-stat-label">Containers</span>
                  </div>
                </div>
                <div className="overview-stat-card">
                  <span className="overview-stat-icon green"><Icons.Heart /></span>
                  <div className="overview-stat-content">
                    <span className="overview-stat-value">{(systemStats.average_health_score || 100).toFixed(0)}</span>
                    <span className="overview-stat-label">Avg Health</span>
                  </div>
                </div>
                <div className="overview-stat-card">
                  <span className="overview-stat-icon amber"><Icons.Cpu /></span>
                  <div className="overview-stat-content">
                    <span className="overview-stat-value">{(systemStats.total_cpu_percent || 0).toFixed(1)}%</span>
                    <span className="overview-stat-label">Total CPU</span>
                  </div>
                </div>
                <div className="overview-stat-card">
                  <span className="overview-stat-icon cyan"><Icons.Memory /></span>
                  <div className="overview-stat-content">
                    <span className="overview-stat-value">{(systemStats.total_memory_mb || 0).toFixed(0)} MB</span>
                    <span className="overview-stat-label">Total Memory</span>
                  </div>
                </div>
                <div className="overview-stat-card">
                  <span className="overview-stat-icon pink"><Icons.AlertTriangle /></span>
                  <div className="overview-stat-content">
                    <span className="overview-stat-value">{anomalies.length}</span>
                    <span className="overview-stat-label">Anomalies</span>
                  </div>
                </div>
                <div className="overview-stat-card">
                  <span className="overview-stat-icon purple"><Icons.Sparkles /></span>
                  <div className="overview-stat-content">
                    <span className="overview-stat-value">{(systemStats.average_efficiency_score || 100).toFixed(0)}</span>
                    <span className="overview-stat-label">Efficiency</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Container Health with Multiple Scores */}
            <div className="section">
              <h3><Icons.Gauge /> Container Scores</h3>
              <div className="scores-grid">
                {containers.map(container => {
                  const health = healthScores[container.id] || 100
                  const stability = stabilityScores[container.id] || 100
                  const efficiency = efficiencyScores[container.id] || 100
                  const analytics = containerAnalytics[container.id] || {}
                  const m = metrics[container.id] || {}
                  const h = history[container.id] || { cpu: [], mem: [] }
                  
                  return (
                    <div key={container.id} className="container-scores-card">
                      <div className="scores-card-header">
                        <div className="scores-card-title">
                          <span className="icon-wrapper subtle"><Icons.Box /></span>
                          <span>{container.name}</span>
                        </div>
                        <StatusBadge status={container.state} />
                      </div>
                      
                      <div className="scores-gauges">
                        <ScoreGauge score={health} label="Health" />
                        <ScoreGauge score={stability} label="Stability" />
                        <ScoreGauge score={efficiency} label="Efficiency" />
                      </div>
                      
                      {/* Resource History Charts */}
                      <div className="scores-charts">
                        <div className="scores-chart-panel">
                          <div className="scores-chart-header">
                            <span className="scores-chart-title amber">CPU History</span>
                            <span className="scores-chart-value">{(m.cpu_percent || 0).toFixed(1)}%</span>
                          </div>
                          <AreaChart data={h.cpu} color="#f59e0b" gradientId={`ml-cpu-${container.id}`} height={80} />
                        </div>
                        <div className="scores-chart-panel">
                          <div className="scores-chart-header">
                            <span className="scores-chart-title cyan">Memory History</span>
                            <span className="scores-chart-value">{formatBytes(m.memory_bytes || 0)}</span>
                          </div>
                          <AreaChart data={h.mem.map(v => v / 1048576)} color="#06b6d4" gradientId={`ml-mem-${container.id}`} height={80} />
                        </div>
                      </div>
                      
                      <div className="scores-trends">
                        <div className="trend-row">
                          <span className="trend-label">CPU Trend</span>
                          <TrendIndicator trend={analytics.trend} />
                        </div>
                        <div className="trend-row">
                          <span className="trend-label">Prediction</span>
                          <span className="prediction-value">
                            {analytics.prediction?.value?.toFixed(1) || '--'}% 
                            <span className="prediction-confidence">
                              ({((analytics.prediction?.confidence || 0) * 100).toFixed(0)}% conf)
                            </span>
                          </span>
                        </div>
                      </div>
                      
                      {analytics.is_stressed && (
                        <div className="stress-warning">
                          <Icons.AlertTriangle />
                          <span>Container under stress</span>
                        </div>
                      )}
                    </div>
                  )
                })}
                {containers.length === 0 && (
                  <div className="empty-section">No containers to analyze</div>
                )}
              </div>
            </div>

            {/* Anomaly Timeline and Distribution */}
            <div className="section">
              <h3><Icons.AlertTriangle /> Anomaly Analysis</h3>
              <div className="anomaly-analysis-grid">
                <div className="anomaly-stats-panel">
                  <h4>Anomaly Summary</h4>
                  <div className="anomaly-stats">
                    <div className="anomaly-stat">
                      <span className="anomaly-stat-value high">{anomalies.filter(a => a.severity === 'high').length}</span>
                      <span className="anomaly-stat-label">High Severity</span>
                    </div>
                    <div className="anomaly-stat">
                      <span className="anomaly-stat-value medium">{anomalies.filter(a => a.severity === 'medium').length}</span>
                      <span className="anomaly-stat-label">Medium Severity</span>
                    </div>
                    <div className="anomaly-stat">
                      <span className="anomaly-stat-value low">{anomalies.filter(a => a.severity === 'low').length}</span>
                      <span className="anomaly-stat-label">Low Severity</span>
                    </div>
                  </div>
                  
                  <h4>By Type</h4>
                  <div className="anomaly-types">
                    {Object.entries(
                      anomalies.reduce((acc, a) => {
                        acc[a.type] = (acc[a.type] || 0) + 1
                        return acc
                      }, {})
                    ).slice(0, 5).map(([type, count]) => (
                      <div key={type} className="anomaly-type-row">
                        <span className="anomaly-type-name">{type.replace(/_/g, ' ')}</span>
                        <span className="anomaly-type-count">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="anomaly-timeline-panel">
                  <h4>Recent Anomalies</h4>
                  <div className="anomaly-list">
                    {anomalies.length === 0 ? (
                      <div className="no-anomalies">
                        <span className="icon-sm green"><Icons.Heart /></span>
                        <span>No anomalies detected - all systems normal</span>
                      </div>
                    ) : (
                      anomalies.slice(-15).reverse().map((anomaly, i) => (
                        <div key={i} className="anomaly-item">
                          <span className="anomaly-time">
                            {new Date(anomaly.timestamp * 1000).toLocaleTimeString()}
                          </span>
                          <span className={`anomaly-badge ${anomaly.severity}`}>
                            {anomaly.severity?.toUpperCase()}
                          </span>
                          <span className="anomaly-type">{anomaly.type?.replace(/_/g, ' ')}</span>
                          <span className="anomaly-msg">{anomaly.message}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* ML Algorithm Explanation */}
            <div className="section">
              <h3><Icons.Brain /> ML Algorithms</h3>
              <div className="info-cards">
                <div className="info-card">
                  <span className="icon-wrapper blue"><Icons.Activity /></span>
                  <h4>Adaptive Z-Score</h4>
                  <p>Uses exponential moving averages with adaptive thresholds that adjust based on container volatility patterns.</p>
                </div>
                <div className="info-card">
                  <span className="icon-wrapper green"><Icons.Heart /></span>
                  <h4>Multi-Score Health</h4>
                  <p>Three distinct scores: Health (current state), Stability (variance), and Efficiency (optimal resource usage).</p>
                </div>
                <div className="info-card">
                  <span className="icon-wrapper amber"><Icons.TrendUp /></span>
                  <h4>Trend Prediction</h4>
                  <p>Linear regression on historical data predicts future CPU and memory usage 30 seconds ahead.</p>
                </div>
                <div className="info-card">
                  <span className="icon-wrapper pink"><Icons.AlertTriangle /></span>
                  <h4>Exhaustion Detection</h4>
                  <p>Predicts when resources will hit limits based on current consumption rate and available capacity.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentPage === 'about' && (
          <div className="page-content">
            <div className="page-header">
              <h2>About MiniContainer</h2>
            </div>

            <div className="section">
              <h3>What is MiniContainer?</h3>
              <p className="section-text">
                MiniContainer is a lightweight Linux container runtime built from scratch using
                Linux namespaces, cgroups v2, and a custom filesystem layer. It demonstrates
                core containerization concepts similar to Docker.
              </p>
            </div>

            <div className="section">
              <h3>Architecture</h3>
              <div className="arch-grid">
                <div className="arch-card">
                  <span className="icon-wrapper amber"><Icons.Terminal /></span>
                  <h4>C Runtime</h4>
                  <p>Low-level container operations: namespace creation, cgroup management, process isolation</p>
                </div>
                <div className="arch-card">
                  <span className="icon-wrapper blue"><Icons.Server /></span>
                  <h4>Python Backend</h4>
                  <p>FastAPI server with WebSocket support for real-time metrics and container management</p>
                </div>
                <div className="arch-card">
                  <span className="icon-wrapper pink"><Icons.Layers /></span>
                  <h4>React Dashboard</h4>
                  <p>Modern UI with live monitoring, container management, and ML analytics</p>
                </div>
              </div>
            </div>

            <div className="section">
              <h3>Key Technologies</h3>
              <div className="tech-tags">
                {['Linux Namespaces', 'Cgroups v2', 'setns()', 'FastAPI', 'WebSocket', 'React', 'Z-Score ML', 'Alpine Linux'].map(tech => (
                  <span key={tech} className="tech-tag">{tech}</span>
                ))}
              </div>
            </div>

            <div className="section">
              <h3>Features</h3>
              <ul className="feature-list">
                <li><Icons.Box /> Create, start, stop, and delete containers</li>
                <li><Icons.Activity /> Real-time CPU, memory, and process monitoring</li>
                <li><Icons.Terminal /> Execute commands inside containers with namespace isolation</li>
                <li><Icons.Brain /> ML-based anomaly detection and health scoring</li>
                <li><Icons.Cpu /> Resource limits (CPU, memory, PIDs)</li>
                <li><Icons.Zap /> Live WebSocket updates</li>
              </ul>
            </div>
          </div>
        )}
      </main>

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

      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.type === 'success' ? <Icons.Heart /> : <Icons.AlertTriangle />}
          <span>{notification.message}</span>
        </div>
      )}
    </div>
  )
}

export default App
