import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges Tailwind CSS class names, resolving conflicts via tailwind-merge.
 * Accepts any value accepted by clsx (strings, arrays, conditionals, objects).
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Returns a value clamped within [min, max].
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Formats a byte count as a human-readable string (e.g. "1.2 MB").
 */
export function formatBytes(bytes: number, decimals = 1): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

/**
 * Truncates a string to a maximum length, appending an ellipsis when truncated.
 */
export function truncate(str: string, maxLength: number, ellipsis = "…"): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - ellipsis.length) + ellipsis;
}

/**
 * Returns true if a value is not null and not undefined.
 */
export function isDefined<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined;
}

/**
 * Generates a simple deterministic ID from a prefix and an index.
 * Not a UUID — use only for predictable, non-sensitive identifiers.
 */
export function makeId(prefix: string, index: number): string {
  return `${prefix}-${index}`;
}

/**
 * Debounces a function, delaying its execution until after `delayMs` ms
 * have elapsed since the last invocation.
 */
export function debounce<T extends (...args: Parameters<T>) => ReturnType<T>>(
  fn: T,
  delayMs: number
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delayMs);
  };
}
