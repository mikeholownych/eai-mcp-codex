/**
 * Utility functions for status colors and icons
 */

// Blog status utilities
export function getBlogStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'published':
      return 'text-green-500'
    case 'draft':
      return 'text-yellow-500'
    case 'archived':
      return 'text-gray-500'
    default:
      return 'text-gray-400'
  }
}

export function getBlogStatusIcon(status: string): string {
  switch (status.toLowerCase()) {
    case 'published':
      return '✓'
    case 'draft':
      return '✎'
    case 'archived':
      return '📦'
    default:
      return '❓'
  }
}

// Ticket status utilities
export function getTicketStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'open':
      return 'text-red-500'
    case 'in-progress':
    case 'in_progress':
      return 'text-yellow-500'
    case 'waiting-customer':
    case 'waiting_customer':
      return 'text-blue-500'
    case 'resolved':
      return 'text-green-500'
    case 'closed':
      return 'text-gray-500'
    default:
      return 'text-gray-400'
  }
}

export function getStatusIcon(status: string): string {
  switch (status.toLowerCase()) {
    case 'open':
      return '🔴'
    case 'in-progress':
    case 'in_progress':
      return '🟡'
    case 'waiting-customer':
    case 'waiting_customer':
      return '🔵'
    case 'resolved':
      return '🟢'
    case 'closed':
      return '⚫'
    default:
      return '⚪'
  }
}

// Priority utilities
export function getPriorityColor(priority: string): string {
  switch (priority.toLowerCase()) {
    case 'urgent':
      return 'text-red-500'
    case 'high':
      return 'text-orange-500'
    case 'medium':
      return 'text-yellow-500'
    case 'low':
      return 'text-green-500'
    default:
      return 'text-gray-400'
  }
}

export function getPriorityIcon(priority: string): string {
  switch (priority.toLowerCase()) {
    case 'urgent':
      return '🔥'
    case 'high':
      return '⬆️'
    case 'medium':
      return '➡️'
    case 'low':
      return '⬇️'
    default:
      return '❓'
  }
}

// User status utilities
export function getUserStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'active':
      return 'text-green-500'
    case 'inactive':
      return 'text-gray-500'
    case 'suspended':
      return 'text-red-500'
    default:
      return 'text-gray-400'
  }
}

export function getUserStatusIcon(status: string): string {
  switch (status.toLowerCase()) {
    case 'active':
      return '✅'
    case 'inactive':
      return '⏸️'
    case 'suspended':
      return '🚫'
    default:
      return '❓'
  }
}
