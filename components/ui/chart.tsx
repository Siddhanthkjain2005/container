"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export type ChartConfig = Record<
  string,
  {
    label?: React.ReactNode
    icon?: React.ComponentType
    color?: string
  }
>

type ChartContextProps = {
  config: ChartConfig
}

const ChartContext = React.createContext<ChartContextProps | null>(null)

function useChart() {
  const context = React.useContext(ChartContext)
  if (!context) {
    throw new Error("useChart must be used within a <ChartContainer />")
  }
  return context
}

interface ChartContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  config: ChartConfig
  children: React.ReactNode
}

export function ChartContainer({
  config,
  children,
  className,
  ...props
}: ChartContainerProps) {
  return (
    <ChartContext.Provider value={{ config }}>
      <div
        className={cn(
          "[&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-none [&_.recharts-polar-grid_[stroke='#ccc']]:stroke-border [&_.recharts-radial-bar-background-sector]:fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border [&_.recharts-sector[stroke='#fff']]:stroke-transparent [&_.recharts-sector]:outline-none [&_.recharts-surface]:outline-none",
          className
        )}
        {...props}
      >
        {children}
      </div>
    </ChartContext.Provider>
  )
}

interface ChartTooltipContentProps
  extends React.HTMLAttributes<HTMLDivElement> {
  active?: boolean
  payload?: Array<{
    name?: string
    value?: number
    dataKey?: string
    payload?: Record<string, unknown>
    color?: string
  }>
  label?: string
  labelFormatter?: (value: string, payload: unknown[]) => React.ReactNode
  formatter?: (
    value: number,
    name: string,
    item: unknown,
    index: number,
    payload: unknown[]
  ) => React.ReactNode
  hideLabel?: boolean
  hideIndicator?: boolean
  indicator?: "line" | "dot" | "dashed"
  nameKey?: string
  labelKey?: string
}

export function ChartTooltipContent({
  active,
  payload,
  label,
  labelFormatter,
  formatter,
  hideLabel = false,
  hideIndicator = false,
  indicator = "dot",
  className,
}: ChartTooltipContentProps) {
  const { config } = useChart()

  if (!active || !payload?.length) {
    return null
  }

  const tooltipLabel = labelFormatter
    ? labelFormatter(label ?? "", payload)
    : label

  return (
    <div
      className={cn(
        "rounded-lg border border-border/50 bg-card px-3 py-2 text-xs shadow-xl",
        className
      )}
    >
      {!hideLabel && tooltipLabel && (
        <div className="mb-1.5 font-medium text-foreground">{tooltipLabel}</div>
      )}
      <div className="flex flex-col gap-1">
        {payload.map((item, index) => {
          const dataKey = item.dataKey as string
          const itemConfig = config[dataKey]
          const color = item.color || itemConfig?.color
          const name = itemConfig?.label ?? item.name ?? dataKey

          return (
            <div key={index} className="flex items-center gap-2">
              {!hideIndicator && (
                <div
                  className={cn(
                    "shrink-0",
                    indicator === "dot" && "h-2 w-2 rounded-full",
                    indicator === "line" && "h-1 w-4 rounded-full",
                    indicator === "dashed" && "h-1 w-4 border-t-2 border-dashed"
                  )}
                  style={{ backgroundColor: color, borderColor: color }}
                />
              )}
              <span className="text-muted-foreground">{name}:</span>
              <span className="font-mono font-medium text-foreground">
                {formatter
                  ? formatter(item.value ?? 0, name as string, item, index, payload)
                  : typeof item.value === "number"
                    ? item.value.toFixed(1)
                    : item.value}
                %
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function ChartTooltip(props: React.ComponentProps<typeof ChartTooltipContent> & {
  content?: React.ComponentType<ChartTooltipContentProps>
  cursor?: React.SVGProps<SVGElement>
}) {
  return props as unknown as React.ReactElement
}
