'use client'

import React, { forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { ButtonProps } from '@/types'

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', disabled = false, loading = false, children, onClick, className, ...props }, ref) => {
    const baseClasses = 'inline-flex items-center justify-center font-medium focus-ring disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200'
    
    const variants = {
      primary: 'bg-gradient-primary text-white hover:shadow-glow hover:scale-105 active:scale-95 shadow-lg',
      secondary: 'bg-gradient-secondary text-white hover:shadow-glow-blue hover:scale-105 active:scale-95 shadow-lg',
      outline: 'border-2 border-primary-500 text-primary-500 hover:bg-primary-500 hover:text-white hover:shadow-glow active:scale-95 backdrop-blur-sm',
      ghost: 'text-dark-300 hover:text-white hover:bg-dark-700 active:scale-95 backdrop-blur-sm',
      danger: 'bg-gradient-to-r from-red-500 to-red-600 text-white hover:from-red-600 hover:to-red-700 hover:scale-105 active:scale-95 shadow-lg',
    }
    
    const sizes = {
      sm: 'px-3 py-1.5 text-sm rounded-lg',
      md: 'px-4 py-2 text-base rounded-xl',
      lg: 'px-6 py-3 text-lg rounded-xl',
    }

    return (
      <button
        ref={ref}
        className={cn(
          baseClasses,
          variants[variant],
          sizes[size],
          loading && 'cursor-wait',
          className
        )}
        disabled={disabled || loading}
        onClick={onClick}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'

export default Button