'use client'

import React from 'react'
import { cn } from '@/lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

interface CardHeaderProps {
  children: React.ReactNode
  className?: string
}

interface CardContentProps {
  children: React.ReactNode
  className?: string
}

interface CardFooterProps {
  children: React.ReactNode
  className?: string
}

const Card: React.FC<CardProps> & {
  Header: React.FC<CardHeaderProps>
  Content: React.FC<CardContentProps>
  Footer: React.FC<CardFooterProps>
} = ({ children, className, hover = false, padding = 'md' }) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }

  return (
    <div
      className={cn(
        'bg-dark-800 border border-dark-700 rounded-2xl shadow-lg backdrop-blur-sm',
        'transition-all duration-300 ease-in-out',
        paddingClasses[padding],
        hover && 'card-hover cursor-pointer hover:shadow-glow',
        className
      )}
    >
      {children}
    </div>
  )
}

const CardHeader: React.FC<CardHeaderProps> = ({ children, className }) => (
  <div className={cn('mb-4', className)}>
    {children}
  </div>
)

const CardContent: React.FC<CardContentProps> = ({ children, className }) => (
  <div className={cn('flex-1', className)}>
    {children}
  </div>
)

const CardFooter: React.FC<CardFooterProps> = ({ children, className }) => (
  <div className={cn('mt-4 pt-4 border-t border-dark-700', className)}>
    {children}
  </div>
)

Card.Header = CardHeader
Card.Content = CardContent
Card.Footer = CardFooter

export default Card