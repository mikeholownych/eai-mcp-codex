'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  HomeIcon,
  CodeBracketIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  CreditCardIcon,
  LifebuoyIcon,
  UserIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
  PlayIcon,
  ChartBarIcon,
  UsersIcon,
  CogIcon,
} from '@heroicons/react/24/outline'

interface SidebarItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
  children?: SidebarItem[]
}

interface SidebarProps {
  role?: string
  plan?: string
}

const Sidebar: React.FC<SidebarProps> = ({ role = 'customer', plan = 'standard' }) => {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()

  const customerItems: SidebarItem[] = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Code Editor', href: '/editor', icon: CodeBracketIcon },
    { name: 'AI Assistant', href: '/chat', icon: ChatBubbleLeftRightIcon },
    { name: 'Video Library', href: '/videos', icon: PlayIcon },
    { name: 'Documentation', href: '/docs', icon: DocumentTextIcon },
    { name: 'Billing', href: '/billing', icon: CreditCardIcon },
    { name: 'Support', href: '/support', icon: LifebuoyIcon },
    { name: 'Profile', href: '/profile', icon: UserIcon },
  ]

  const staffItems: SidebarItem[] = [
    { name: 'Overview', href: '/staff', icon: HomeIcon },
    { name: 'Analytics', href: '/staff/analytics', icon: ChartBarIcon },
    { name: 'Customers', href: '/staff/customers', icon: UsersIcon },
    { name: 'Support', href: '/staff/support', icon: LifebuoyIcon },
    { name: 'Content', href: '/staff/content', icon: DocumentTextIcon, children: [
      { name: 'Blog Posts', href: '/staff/content/blog', icon: DocumentTextIcon },
      { name: 'Videos', href: '/staff/content/videos', icon: PlayIcon },
    ]},
    { name: 'Billing', href: '/staff/billing', icon: CreditCardIcon },
    { name: 'Settings', href: '/staff/settings', icon: CogIcon },
  ]

  const items = role === 'customer' ? customerItems : staffItems

  const isActive = (href: string) => {
    if (href === '/dashboard' || href === '/staff') {
      return pathname === href
    }
    return pathname.startsWith(href)
  }

  return (
    <div className={cn(
      'h-screen bg-dark-900 border-r border-dark-700 flex flex-col transition-all duration-300',
      collapsed ? 'w-16' : 'w-64'
    )}>
      {/* Header */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <div>
                <h1 className="text-white font-semibold text-sm">Ethical AI</h1>
                <p className="text-gray-400 text-xs">MCP Network</p>
              </div>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-lg hover:bg-dark-700 text-gray-400 hover:text-white transition-colors"
          >
            {collapsed ? (
              <ChevronDoubleRightIcon className="w-5 h-5" />
            ) : (
              <ChevronDoubleLeftIcon className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto custom-scrollbar">
        {items.map((item) => (
          <div key={item.name}>
            <Link
              href={item.href}
              className={cn(
                'flex items-center px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 group',
                isActive(item.href)
                  ? 'bg-primary-500 text-white shadow-glow'
                  : 'text-gray-300 hover:text-white hover:bg-dark-700'
              )}
            >
              <item.icon className={cn(
                'flex-shrink-0 w-5 h-5',
                collapsed ? 'mx-auto' : 'mr-3'
              )} />
              {!collapsed && (
                <>
                  <span className="flex-1">{item.name}</span>
                  {item.badge && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </Link>

            {/* Sub-items */}
            {item.children && !collapsed && isActive(item.href) && (
              <div className="mt-2 ml-4 space-y-1">
                {item.children.map((child) => (
                  <Link
                    key={child.name}
                    href={child.href}
                    className={cn(
                      'flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                      isActive(child.href)
                        ? 'text-primary-400 bg-dark-700'
                        : 'text-gray-400 hover:text-white hover:bg-dark-700'
                    )}
                  >
                    <child.icon className="w-4 h-4 mr-2" />
                    {child.name}
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-dark-700">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-primary rounded-full flex items-center justify-center">
              <UserIcon className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">John Doe</p>
              <p className="text-xs text-gray-400 capitalize">{plan} Plan</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Sidebar