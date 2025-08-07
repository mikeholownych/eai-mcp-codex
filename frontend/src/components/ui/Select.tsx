'use client'

import React from 'react'
import { cn } from '@/lib/utils'

interface SelectProps {
  label?: string
  value?: string
  onValueChange?: (value: string) => void
  placeholder?: string
  options: Array<{ value: string; label: string }>
  disabled?: boolean
  required?: boolean
  error?: string
  className?: string
}

const Select: React.FC<SelectProps> = ({
  label,
  value,
  onValueChange,
  placeholder,
  options,
  disabled = false,
  required = false,
  error,
  className,
}) => {
  const selectId = label?.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="space-y-1.5">
      {label && (
        <label
          htmlFor={selectId}
          className={cn(
            'block text-sm font-medium text-slate-300',
            required && 'after:content-["*"] after:ml-0.5 after:text-red-400',
          )}
        >
          {label}
        </label>
      )}
      <select
        id={selectId}
        value={value}
        onChange={e => onValueChange?.(e.target.value)}
        disabled={disabled}
        required={required}
        className={cn(
          'w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md',
          'text-slate-100',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          error && 'border-red-500 focus:ring-red-500',
          className,
        )}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
    </div>
  )
}

export default Select
