<<<<<<< HEAD
import type { JSX } from "react";
=======
import type { JSX } from 'react'
>>>>>>> main
import {
  CheckCircleIcon,
  DocumentTextIcon,
  ClockIcon,
  CalendarDaysIcon,
  ExclamationTriangleIcon,
  CogIcon,
<<<<<<< HEAD
} from "@heroicons/react/24/outline";

export const BLOG_STATUS_COLORS: Record<string, string> = {
  published: "bg-green-500/10 text-green-400",
  draft: "bg-gray-500/10 text-gray-400",
  review: "bg-yellow-500/10 text-yellow-400",
  scheduled: "bg-blue-500/10 text-blue-400",
};
=======
} from '@heroicons/react/24/outline'

export const BLOG_STATUS_COLORS: Record<string, string> = {
  published: 'bg-green-500/10 text-green-400',
  draft: 'bg-gray-500/10 text-gray-400',
  review: 'bg-yellow-500/10 text-yellow-400',
  scheduled: 'bg-blue-500/10 text-blue-400',
}
>>>>>>> main

export const BLOG_STATUS_ICONS: Record<string, JSX.Element> = {
  published: <CheckCircleIcon className="h-4 w-4" />,
  draft: <DocumentTextIcon className="h-4 w-4" />,
  review: <ClockIcon className="h-4 w-4" />,
  scheduled: <CalendarDaysIcon className="h-4 w-4" />,
<<<<<<< HEAD
};

export const TICKET_STATUS_COLORS: Record<string, string> = {
  open: "bg-blue-500/10 text-blue-400",
  "in-progress": "bg-yellow-500/10 text-yellow-400",
  "waiting-customer": "bg-purple-500/10 text-purple-400",
  resolved: "bg-green-500/10 text-green-400",
  closed: "bg-gray-500/10 text-gray-400",
};

export const TICKET_STATUS_ICONS: Record<string, JSX.Element> = {
  open: <ClockIcon className="h-4 w-4" />,
  "in-progress": <ExclamationTriangleIcon className="h-4 w-4" />,
  "waiting-customer": <ClockIcon className="h-4 w-4" />,
  resolved: <CheckCircleIcon className="h-4 w-4" />,
  closed: <CheckCircleIcon className="h-4 w-4" />,
};

export const USER_STATUS_COLORS: Record<string, string> = {
  active: "bg-green-500/10 text-green-400",
  inactive: "bg-yellow-500/10 text-yellow-400",
  suspended: "bg-red-500/10 text-red-400",
};
=======
}

export const TICKET_STATUS_COLORS: Record<string, string> = {
  open: 'bg-blue-500/10 text-blue-400',
  'in-progress': 'bg-yellow-500/10 text-yellow-400',
  'waiting-customer': 'bg-purple-500/10 text-purple-400',
  resolved: 'bg-green-500/10 text-green-400',
  closed: 'bg-gray-500/10 text-gray-400',
}

export const TICKET_STATUS_ICONS: Record<string, JSX.Element> = {
  open: <ClockIcon className="h-4 w-4" />,
  'in-progress': <ExclamationTriangleIcon className="h-4 w-4" />,
  'waiting-customer': <ClockIcon className="h-4 w-4" />,
  resolved: <CheckCircleIcon className="h-4 w-4" />,
  closed: <CheckCircleIcon className="h-4 w-4" />,
}

export const USER_STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-500/10 text-green-400',
  inactive: 'bg-yellow-500/10 text-yellow-400',
  suspended: 'bg-red-500/10 text-red-400',
}
>>>>>>> main

export const USER_STATUS_ICONS: Record<string, JSX.Element> = {
  active: <CheckCircleIcon className="h-4 w-4" />,
  inactive: <ClockIcon className="h-4 w-4" />,
  suspended: <ExclamationTriangleIcon className="h-4 w-4" />,
<<<<<<< HEAD
};

export const VIDEO_STATUS_COLORS: Record<string, string> = {
  published: "bg-green-500/10 text-green-400",
  draft: "bg-gray-500/10 text-gray-400",
  processing: "bg-blue-500/10 text-blue-400",
  scheduled: "bg-yellow-500/10 text-yellow-400",
  error: "bg-red-500/10 text-red-400",
};
=======
}

export const VIDEO_STATUS_COLORS: Record<string, string> = {
  published: 'bg-green-500/10 text-green-400',
  draft: 'bg-gray-500/10 text-gray-400',
  processing: 'bg-blue-500/10 text-blue-400',
  scheduled: 'bg-yellow-500/10 text-yellow-400',
  error: 'bg-red-500/10 text-red-400',
}
>>>>>>> main

export const VIDEO_STATUS_ICONS: Record<string, JSX.Element> = {
  published: <CheckCircleIcon className="h-4 w-4" />,
  draft: <DocumentTextIcon className="h-4 w-4" />,
  processing: <CogIcon className="h-4 w-4 animate-spin" />,
  scheduled: <CalendarDaysIcon className="h-4 w-4" />,
  error: <ExclamationTriangleIcon className="h-4 w-4" />,
<<<<<<< HEAD
};

export const VISIBILITY_COLORS: Record<string, string> = {
  enterprise: "bg-purple-500/10 text-purple-400",
  professional: "bg-blue-500/10 text-blue-400",
  standard: "bg-green-500/10 text-green-400",
  free: "bg-gray-500/10 text-gray-400",
};

// Helper functions
export const getBlogStatusColor = (status: string): string =>
  BLOG_STATUS_COLORS[status] ?? BLOG_STATUS_COLORS.draft;

export const getBlogStatusIcon = (status: string): JSX.Element =>
  BLOG_STATUS_ICONS[status] ?? BLOG_STATUS_ICONS.draft;

export const getTicketStatusColor = (status: string): string =>
  TICKET_STATUS_COLORS[status] ?? TICKET_STATUS_COLORS.open;

export const getTicketStatusIcon = (status: string): JSX.Element =>
  TICKET_STATUS_ICONS[status] ?? TICKET_STATUS_ICONS.open;

export const getUserStatusColor = (status: string): string =>
  USER_STATUS_COLORS[status] ?? USER_STATUS_COLORS.active;

export const getUserStatusIcon = (status: string): JSX.Element =>
  USER_STATUS_ICONS[status] ?? USER_STATUS_ICONS.active;

export const getVideoStatusColor = (status: string): string =>
  VIDEO_STATUS_COLORS[status] ?? VIDEO_STATUS_COLORS.draft;

export const getVideoStatusIcon = (status: string): JSX.Element =>
  VIDEO_STATUS_ICONS[status] ?? VIDEO_STATUS_ICONS.draft;

export const getVisibilityColor = (visibility: string): string =>
  VISIBILITY_COLORS[visibility] ?? VISIBILITY_COLORS.free;
=======
}

export const VISIBILITY_COLORS: Record<string, string> = {
  enterprise: 'bg-purple-500/10 text-purple-400',
  professional: 'bg-blue-500/10 text-blue-400',
  standard: 'bg-green-500/10 text-green-400',
  free: 'bg-gray-500/10 text-gray-400',
}

// Helper functions
export const getBlogStatusColor = (status: string): string => 
  BLOG_STATUS_COLORS[status] ?? BLOG_STATUS_COLORS.draft

export const getBlogStatusIcon = (status: string): JSX.Element => 
  BLOG_STATUS_ICONS[status] ?? BLOG_STATUS_ICONS.draft

export const getTicketStatusColor = (status: string): string => 
  TICKET_STATUS_COLORS[status] ?? TICKET_STATUS_COLORS.open

export const getTicketStatusIcon = (status: string): JSX.Element => 
  TICKET_STATUS_ICONS[status] ?? TICKET_STATUS_ICONS.open

export const getUserStatusColor = (status: string): string => 
  USER_STATUS_COLORS[status] ?? USER_STATUS_COLORS.active

export const getUserStatusIcon = (status: string): JSX.Element => 
  USER_STATUS_ICONS[status] ?? USER_STATUS_ICONS.active

export const getVideoStatusColor = (status: string): string => 
  VIDEO_STATUS_COLORS[status] ?? VIDEO_STATUS_COLORS.draft

export const getVideoStatusIcon = (status: string): JSX.Element => 
  VIDEO_STATUS_ICONS[status] ?? VIDEO_STATUS_ICONS.draft

export const getVisibilityColor = (visibility: string): string => 
  VISIBILITY_COLORS[visibility] ?? VISIBILITY_COLORS.free
>>>>>>> main
