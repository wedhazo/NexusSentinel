import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  TooltipProps,
} from "recharts";
import { cn } from "@/lib/utils";

export interface DataItem {
  /**
   * Label to display for the bar
   */
  label: string;
  
  /**
   * Value to determine bar length
   */
  value: number;
  
  /**
   * Optional color override for this specific bar
   */
  color?: string;
  
  /**
   * Optional secondary value to display (e.g., previous value)
   */
  secondaryValue?: number;
  
  /**
   * Optional metadata to include in tooltip
   */
  metadata?: Record<string, any>;
}

export interface HorizontalBarChartProps {
  /**
   * Data items to display in the chart
   */
  data: DataItem[];
  
  /**
   * Optional function to format values in tooltips and labels
   */
  valueFormatter?: (value: number) => string;
  
  /**
   * Height of the chart in pixels
   * @default 400
   */
  height?: number;
  
  /**
   * Optional className for additional styling
   */
  className?: string;
  
  /**
   * Optional title for the chart
   */
  title?: string;
  
  /**
   * Bar color for positive values
   * @default "hsl(var(--success, 142.1 76.2% 36.3%))" - Green
   */
  positiveColor?: string;
  
  /**
   * Bar color for negative values
   * @default "hsl(var(--destructive))" - Red
   */
  negativeColor?: string;
  
  /**
   * Show grid lines
   * @default true
   */
  showGrid?: boolean;
  
  /**
   * Label for the value axis
   */
  valueLabel?: string;
  
  /**
   * Maximum number of bars to display
   * @default 20
   */
  maxBars?: number;
}

/**
 * Horizontal bar chart component for displaying comparative data like top/bottom movers
 */
export function HorizontalBarChart({
  data,
  valueFormatter = (value) => value.toFixed(2),
  height = 400,
  className,
  title,
  positiveColor = "hsl(var(--success, 142.1 76.2% 36.3%))",
  negativeColor = "hsl(var(--destructive))",
  showGrid = true,
  valueLabel,
  maxBars = 20,
}: HorizontalBarChartProps) {
  // Limit the number of bars to maxBars
  const limitedData = data.slice(0, maxBars);
  
  // Calculate the maximum absolute value for proper scaling
  const maxAbsValue = Math.max(
    ...limitedData.map((item) => Math.abs(item.value))
  );
  
  // Custom tooltip component
  const CustomTooltip = ({ active, payload }: TooltipProps<number, string>) => {
    if (!active || !payload || !payload.length) {
      return null;
    }
    
    const data = payload[0].payload as DataItem;
    const value = data.value;
    const formattedValue = valueFormatter(value);
    const isPositive = value >= 0;
    
    return (
      <div className="bg-popover text-popover-foreground shadow-md rounded-lg p-3 border border-border">
        <p className="font-medium mb-1">{data.label}</p>
        <p className={cn(
          "text-sm font-semibold",
          isPositive ? "text-success" : "text-destructive"
        )}>
          {isPositive ? "+" : ""}{formattedValue}
        </p>
        
        {data.secondaryValue !== undefined && (
          <p className="text-xs text-muted-foreground mt-1">
            Previous: {valueFormatter(data.secondaryValue)}
          </p>
        )}
        
        {data.metadata && Object.entries(data.metadata).map(([key, value]) => (
          <p key={key} className="text-xs text-muted-foreground mt-1">
            {key}: {typeof value === 'number' ? valueFormatter(value) : value}
          </p>
        ))}
      </div>
    );
  };

  return (
    <div className={cn("w-full", className)}>
      {title && (
        <h3 className="text-lg font-medium mb-4">{title}</h3>
      )}
      
      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={limitedData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
          >
            {showGrid && (
              <CartesianGrid 
                strokeDasharray="3 3" 
                horizontal={true} 
                vertical={false} 
                stroke="hsl(var(--muted))" 
                opacity={0.4}
              />
            )}
            
            <XAxis
              type="number"
              domain={[-maxAbsValue, maxAbsValue]}
              tickFormatter={valueFormatter}
              label={valueLabel ? { value: valueLabel, position: 'insideBottom', offset: -5 } : undefined}
              tick={{ fill: "hsl(var(--foreground))" }}
              axisLine={{ stroke: "hsl(var(--border))" }}
            />
            
            <YAxis
              type="category"
              dataKey="label"
              tick={{ fill: "hsl(var(--foreground))" }}
              axisLine={{ stroke: "hsl(var(--border))" }}
              width={75}
              tickFormatter={(value) => 
                value.length > 10 ? `${value.substring(0, 10)}...` : value
              }
            />
            
            <Tooltip content={<CustomTooltip />} />
            
            <Bar dataKey="value" radius={[4, 4, 4, 4]} barSize={20}>
              {limitedData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`}
                  fill={entry.color || (entry.value >= 0 ? positiveColor : negativeColor)}
                  opacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
