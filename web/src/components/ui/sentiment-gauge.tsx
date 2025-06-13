import React from "react";
import { cn } from "@/lib/utils";

export interface SentimentGaugeProps {
  /**
   * Sentiment value from -1 (negative) to 1 (positive)
   */
  value: number;
  /**
   * Size of the gauge in pixels
   * @default 200
   */
  size?: number;
  /**
   * Optional label to display below the gauge
   */
  label?: string;
  /**
   * Optional className for styling
   */
  className?: string;
  /**
   * Show value label inside the gauge
   * @default true
   */
  showValue?: boolean;
  /**
   * Show labels for negative, neutral, positive
   * @default true
   */
  showLabels?: boolean;
}

/**
 * A radial gauge component for displaying sentiment values
 * from -1 (negative) to 1 (positive)
 */
export function SentimentGauge({
  value,
  size = 200,
  label,
  className,
  showValue = true,
  showLabels = true,
}: SentimentGaugeProps) {
  // Clamp the value between -1 and 1
  const clampedValue = Math.max(-1, Math.min(1, value));
  
  // Calculate the angle for the needle (from -90 to 90 degrees)
  // -1 maps to -90 degrees, 0 maps to 0 degrees, 1 maps to 90 degrees
  const angle = clampedValue * 90;
  
  // Calculate the center point of the gauge
  const center = size / 2;
  const radius = (size / 2) * 0.8; // 80% of half size
  
  // Calculate needle endpoint using trigonometry
  const needleLength = radius * 0.9; // 90% of radius
  const needleX = center + needleLength * Math.sin((angle * Math.PI) / 180);
  const needleY = center - needleLength * Math.cos((angle * Math.PI) / 180);
  
  // Format the sentiment value for display
  const formattedValue = (clampedValue * 100).toFixed(0);
  const sentimentText = getSentimentText(clampedValue);
  
  // Determine the color based on the sentiment value
  const gaugeColor = getSentimentColor(clampedValue);
  
  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        {/* Gauge background with gradient */}
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Gauge background (semi-circle) */}
          <defs>
            <linearGradient id="sentimentGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" /> {/* Red for negative */}
              <stop offset="50%" stopColor="#eab308" /> {/* Yellow for neutral */}
              <stop offset="100%" stopColor="#22c55e" /> {/* Green for positive */}
            </linearGradient>
          </defs>
          
          {/* Gauge track (gray background) */}
          <path
            d={`M ${size * 0.1} ${center} 
                A ${radius} ${radius} 0 0 1 ${size * 0.9} ${center}`}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth={size * 0.05}
            strokeLinecap="round"
          />
          
          {/* Colored gauge arc based on sentiment value */}
          <path
            d={`M ${center} ${center} 
                L ${size * 0.1} ${center} 
                A ${radius} ${radius} 0 0 1 ${center + radius * Math.sin((angle * Math.PI) / 180)} ${center - radius * Math.cos((angle * Math.PI) / 180)}`}
            fill="url(#sentimentGradient)"
            opacity="0.3"
          />
          
          {/* Tick marks */}
          {[-0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75].map((tick) => {
            const tickAngle = tick * 90;
            const tickX = center + radius * Math.sin((tickAngle * Math.PI) / 180);
            const tickY = center - radius * Math.cos((tickAngle * Math.PI) / 180);
            const outerX = center + (radius + 10) * Math.sin((tickAngle * Math.PI) / 180);
            const outerY = center - (radius + 10) * Math.cos((tickAngle * Math.PI) / 180);
            
            return (
              <line
                key={tick}
                x1={tickX}
                y1={tickY}
                x2={outerX}
                y2={outerY}
                stroke="hsl(var(--muted-foreground))"
                strokeWidth={tick === 0 ? 2 : 1}
              />
            );
          })}
          
          {/* Labels */}
          {showLabels && (
            <>
              <text
                x={size * 0.1}
                y={center + 25}
                textAnchor="middle"
                fontSize={size * 0.06}
                fill="hsl(var(--destructive))"
                className="font-medium"
              >
                Negative
              </text>
              <text
                x={center}
                y={center + 25}
                textAnchor="middle"
                fontSize={size * 0.06}
                fill="hsl(var(--muted-foreground))"
                className="font-medium"
              >
                Neutral
              </text>
              <text
                x={size * 0.9}
                y={center + 25}
                textAnchor="middle"
                fontSize={size * 0.06}
                fill="hsl(var(--success, var(--primary)))"
                className="font-medium"
              >
                Positive
              </text>
            </>
          )}
          
          {/* Needle */}
          <line
            x1={center}
            y1={center}
            x2={needleX}
            y2={needleY}
            stroke={gaugeColor}
            strokeWidth={size * 0.02}
            strokeLinecap="round"
          />
          
          {/* Center circle */}
          <circle
            cx={center}
            cy={center}
            r={size * 0.06}
            fill={gaugeColor}
          />
        </svg>
        
        {/* Value display */}
        {showValue && (
          <div 
            className="absolute bottom-12 left-0 right-0 text-center"
            style={{ fontSize: size * 0.12 }}
          >
            <div className="font-bold" style={{ color: gaugeColor }}>
              {formattedValue}%
            </div>
            <div className="text-sm font-medium text-muted-foreground">
              {sentimentText}
            </div>
          </div>
        )}
      </div>
      
      {/* Optional label */}
      {label && (
        <div className="mt-2 text-center text-sm text-muted-foreground">
          {label}
        </div>
      )}
    </div>
  );
}

/**
 * Get a descriptive text based on sentiment value
 */
function getSentimentText(value: number): string {
  if (value >= 0.7) return "Very Positive";
  if (value >= 0.3) return "Positive";
  if (value >= -0.3) return "Neutral";
  if (value >= -0.7) return "Negative";
  return "Very Negative";
}

/**
 * Get color based on sentiment value
 */
function getSentimentColor(value: number): string {
  if (value >= 0.3) return "hsl(var(--success, 142.1 76.2% 36.3%))"; // Green
  if (value >= -0.3) return "hsl(var(--warning, 48 96% 53%))"; // Yellow
  return "hsl(var(--destructive))"; // Red
}
