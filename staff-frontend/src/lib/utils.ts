<<<<<<< HEAD
import { API_CONFIG } from "./config";
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
=======
import { API_CONFIG } from "./config"
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
>>>>>>> main

/**
 * Utility function to merge class names with tailwind-merge
 */
export function cn(...inputs: ClassValue[]) {
<<<<<<< HEAD
  return twMerge(clsx(inputs));
=======
  return twMerge(clsx(inputs))
>>>>>>> main
}

/**
 * Structured debug logging
 */
export function debug(label: string, data: unknown): void {
<<<<<<< HEAD
  if (process.env.NODE_ENV !== "production") {
    console.log(`[DEBUG] ${label}:`, JSON.stringify(data, null, 2));
=======
  if (process.env.NODE_ENV !== 'production') {
    console.log(`[DEBUG] ${label}:`, JSON.stringify(data, null, 2))
>>>>>>> main
  }
}

/**
 * Format bytes to human readable string
 */
export function formatBytes(bytes: number, decimals = 2): string {
<<<<<<< HEAD
  if (!+bytes) return "0 Bytes";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
=======
  if (!+bytes) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
>>>>>>> main
}

/**
 * Format date to relative time string
 */
export function formatRelativeTime(date: Date): string {
<<<<<<< HEAD
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;

  return date.toLocaleDateString();
=======
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 60) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  
  return date.toLocaleDateString()
>>>>>>> main
}

/**
 * Debounce function for search and input handling
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
<<<<<<< HEAD
  wait: number,
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
=======
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout
  return (...args: Parameters<T>) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
>>>>>>> main
}

/**
 * Generate a random ID
 */
export function generateId(): string {
<<<<<<< HEAD
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
=======
  return Math.random().toString(36).substring(2) + Date.now().toString(36)
>>>>>>> main
}

/**
 * Check if user has permission based on role and plan
 */
export interface PermissionOptions {
<<<<<<< HEAD
  userRole: string;
  userPlan: string;
  requiredRole: string[];
  requiredPlan?: string[];
=======
  userRole: string
  userPlan: string
  requiredRole: string[]
  requiredPlan?: string[]
>>>>>>> main
}

export function hasPermission({
  userRole,
  userPlan,
  requiredRole,
  requiredPlan = [],
}: PermissionOptions): boolean {
  const roleHierarchy = {
<<<<<<< HEAD
    superadmin: 10,
    admin: 9,
    manager: 8,
    staff: 7,
    enterprise: 6,
    pro: 5,
    standard: 4,
    free: 3,
  };

  const hasRolePermission =
    requiredRole.length === 0 ||
    requiredRole.some(
      (role) =>
        (roleHierarchy[userRole as keyof typeof roleHierarchy] || 0) >=
        (roleHierarchy[role as keyof typeof roleHierarchy] || 0),
    );

  const hasPlanPermission =
    requiredPlan.length === 0 ||
    requiredPlan.some(
      (plan) =>
        (roleHierarchy[userPlan as keyof typeof roleHierarchy] || 0) >=
        (roleHierarchy[plan as keyof typeof roleHierarchy] || 0),
    );

  return hasRolePermission && hasPlanPermission;
=======
    'superadmin': 10,
    'admin': 9,
    'manager': 8,
    'staff': 7,
    'enterprise': 6,
    'pro': 5,
    'standard': 4,
    'free': 3,
  }

  const hasRolePermission = requiredRole.length === 0 || 
    requiredRole.some(role => (roleHierarchy[userRole as keyof typeof roleHierarchy] || 0) >= 
                             (roleHierarchy[role as keyof typeof roleHierarchy] || 0))

  const hasPlanPermission = requiredPlan.length === 0 || 
    requiredPlan.some(plan => (roleHierarchy[userPlan as keyof typeof roleHierarchy] || 0) >= 
                             (roleHierarchy[plan as keyof typeof roleHierarchy] || 0))

  return hasRolePermission && hasPlanPermission
>>>>>>> main
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
<<<<<<< HEAD
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
=======
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
>>>>>>> main
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
<<<<<<< HEAD
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error("Failed to copy text: ", err);
    return false;
=======
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    console.error('Failed to copy text: ', err)
    return false
>>>>>>> main
  }
}

/**
 * Download text as file
 */
export function downloadTextFile(content: string, filename: string): void {
<<<<<<< HEAD
  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
=======
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
>>>>>>> main
}

/**
 * Format currency amount
 */
<<<<<<< HEAD
export function formatCurrency(amount: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(amount);
=======
export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount)
>>>>>>> main
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
<<<<<<< HEAD
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
=======
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
>>>>>>> main
}

/**
 * Generate color based on string (for avatars, etc.)
 */
export function stringToColor(str: string): string {
<<<<<<< HEAD
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = hash % 360;
  return `hsl(${hue}, 70%, 50%)`;
=======
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = hash % 360
  return `hsl(${hue}, 70%, 50%)`
>>>>>>> main
}

/**
 * Format code for display
 */
export function formatCode(code: string): string {
  // This would typically use a syntax highlighter
  // For now, just return the code as-is
<<<<<<< HEAD
  return code;
=======
  return code
>>>>>>> main
}

/**
 * Escape HTML to prevent XSS
 */
export function escapeHtml(text: string): string {
<<<<<<< HEAD
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
=======
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
>>>>>>> main
}

/**
 * Parse query string to object
 */
export function parseQueryString(queryString: string): Record<string, string> {
<<<<<<< HEAD
  const params = new URLSearchParams(queryString);
  const result: Record<string, string> = {};
  for (const [key, value] of params.entries()) {
    result[key] = value;
  }
  return result;
=======
  const params = new URLSearchParams(queryString)
  const result: Record<string, string> = {}
  for (const [key, value] of params.entries()) {
    result[key] = value
  }
  return result
>>>>>>> main
}

/**
 * Build query string from object
 */
export function buildQueryString(params: Record<string, string>): string {
<<<<<<< HEAD
  const urlParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) urlParams.append(key, value);
  });
  return urlParams.toString();
=======
  const urlParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value) urlParams.append(key, value)
  })
  return urlParams.toString()
>>>>>>> main
}

/**
 * Fetch wrapper with timeout
 */
export async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
<<<<<<< HEAD
  timeout = API_CONFIG.timeoutMs,
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(id);
=======
  timeout = API_CONFIG.timeoutMs
): Promise<Response> {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)
  try {
    return await fetch(url, { ...options, signal: controller.signal })
  } finally {
    clearTimeout(id)
>>>>>>> main
  }
}
