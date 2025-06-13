import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline:
          "text-foreground",
        success:
          "border-transparent bg-green-600 text-white hover:bg-green-600/80 dark:bg-green-700 dark:hover:bg-green-700/80",
        warning:
          "border-transparent bg-yellow-500 text-white hover:bg-yellow-500/80 dark:bg-yellow-600 dark:hover:bg-yellow-600/80",
        stock:
          "border-blue-200 bg-blue-100 text-blue-800 hover:bg-blue-200 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
        neutral:
          "border-gray-200 bg-gray-100 text-gray-800 hover:bg-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300",
      },
      size: {
        default: "h-6",
        sm: "h-5 text-[10px]",
        lg: "h-7 px-3",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  clickable?: boolean;
}

function Badge(
  { className, variant, size, clickable, ...props }: BadgeProps,
  ref: React.ForwardedRef<HTMLDivElement>
) {
  return (
    <div
      ref={ref}
      className={cn(
        badgeVariants({ variant, size }), 
        clickable && "cursor-pointer active:scale-95",
        className
      )}
      {...props}
    />
  )
}

const ForwardedBadge = React.forwardRef<HTMLDivElement, BadgeProps>(Badge)
ForwardedBadge.displayName = "Badge"

export { ForwardedBadge as Badge, badgeVariants }
