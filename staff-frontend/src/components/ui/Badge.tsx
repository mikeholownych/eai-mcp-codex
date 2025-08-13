<<<<<<< HEAD
"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "secondary" | "success" | "warning" | "error";
  size?: "sm" | "md" | "lg";
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  size = "md",
  className,
}) => {
  const variants = {
    default: "bg-slate-700 text-slate-300",
    secondary: "bg-slate-600 text-slate-200",
    success: "bg-green-500/20 text-green-400 border border-green-500/30",
    warning: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
    error: "bg-red-500/20 text-red-400 border border-red-500/30",
  };

  const sizes = {
    sm: "px-2 py-0.5 text-xs rounded-md",
    md: "px-2.5 py-0.5 text-sm rounded-md",
    lg: "px-3 py-1 text-sm rounded-md",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center font-medium",
        variants[variant],
        sizes[size],
        className,
      )}
    >
      {children}
    </span>
  );
};

export default Badge;
=======
'use client'

import React from 'react'
import { cn } from '@/lib/utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'error'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const Badge: React.FC<BadgeProps> = ({ 
  children, 
  variant = 'default', 
  size = 'md', 
  className 
}) => {
  const variants = {
    default: 'bg-slate-700 text-slate-300',
    secondary: 'bg-slate-600 text-slate-200',
    success: 'bg-green-500/20 text-green-400 border border-green-500/30',
    warning: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
    error: 'bg-red-500/20 text-red-400 border border-red-500/30'
  }

  const sizes = {
    sm: 'px-2 py-0.5 text-xs rounded-md',
    md: 'px-2.5 py-0.5 text-sm rounded-md',
    lg: 'px-3 py-1 text-sm rounded-md'
  }

  return (
    <span className={cn(
      'inline-flex items-center font-medium',
      variants[variant],
      sizes[size],
      className
    )}>
      {children}
    </span>
  )
}

export default Badge
>>>>>>> main
