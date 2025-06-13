import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Combines multiple class values into a single class string,
 * handling Tailwind CSS class conflicts properly.
 * 
 * @param inputs - Class values to be merged
 * @returns Merged class string
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Formats a number as currency
 * 
 * @param value - Number to format
 * @param currency - Currency code (default: USD)
 * @returns Formatted currency string
 */
export function formatCurrency(value: number, currency: string = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

/**
 * Formats a number as percentage
 * 
 * @param value - Number to format (0.1 = 10%)
 * @param includeSign - Whether to include + sign for positive values
 * @returns Formatted percentage string
 */
export function formatPercent(value: number, includeSign: boolean = true): string {
  const prefix = includeSign && value > 0 ? "+" : ""
  return `${prefix}${(value * 100).toFixed(2)}%`
}

/**
 * Truncates a string to a specified length and adds ellipsis
 * 
 * @param str - String to truncate
 * @param length - Maximum length
 * @returns Truncated string
 */
export function truncateString(str: string, length: number = 30): string {
  if (!str) return ""
  return str.length > length ? `${str.substring(0, length)}...` : str
}
