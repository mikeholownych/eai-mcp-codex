'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
<<<<<<< HEAD
import {
  BellIcon,
  MagnifyingGlassIcon,
=======
import { 
  BellIcon, 
  MagnifyingGlassIcon, 
>>>>>>> main
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline'
import { Menu } from '@headlessui/react'
import { cn } from '@/lib/utils'
import Button from '@/components/ui/Button'

interface HeaderProps {
  title?: string
  subtitle?: string
  user?: {
    name: string
    email: string
    avatar?: string
    role: string
  }
}

const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  user = { name: 'John Doe', email: 'john@example.com', role: 'customer' },
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [notifications] = useState([
    { id: 1, title: 'New feature: Advanced Code Analysis', time: '2m ago', unread: true },
    { id: 2, title: 'Your monthly usage report is ready', time: '1h ago', unread: true },
    { id: 3, title: 'System maintenance scheduled', time: '3h ago', unread: false },
  ])
  const router = useRouter()

  const handleLogout = () => {
    // Handle logout logic
    localStorage.removeItem('auth_token')
    router.push('/login')
  }

  const unreadCount = notifications.filter(n => n.unread).length

  return (
    <header className="bg-dark-800 border-b border-dark-700 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left side - Title and search */}
        <div className="flex items-center space-x-6">
          {/* Page title */}
          {title && (
            <div>
              <h1 className="text-2xl font-semibold text-white">{title}</h1>
              {subtitle && <p className="text-sm text-gray-400 mt-1">{subtitle}</p>}
            </div>
          )}

          {/* Search bar */}
          <div className="hidden md:block">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 w-80 bg-dark-700 border border-dark-600 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Right side - Notifications and user menu */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <Menu as="div" className="relative">
            <Menu.Button className="relative p-2 text-gray-400 hover:text-white hover:bg-dark-700 rounded-lg transition-colors">
              <BellIcon className="w-6 h-6" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-primary-500 text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </Menu.Button>

            <Menu.Items className="absolute right-0 mt-2 w-80 bg-dark-800 border border-dark-600 rounded-xl shadow-xl z-50">
              <div className="p-4 border-b border-dark-600">
                <h3 className="text-lg font-semibold text-white">Notifications</h3>
              </div>
              <div className="max-h-96 overflow-y-auto custom-scrollbar">
                {notifications.map(notification => (
                  <Menu.Item key={notification.id}>
                    {({ active }) => (
                      <div
                        className={cn(
                          'flex items-start space-x-3 p-4 cursor-pointer transition-colors',
                          active && 'bg-dark-700',
                          notification.unread && 'bg-dark-750',
                        )}
                      >
                        <div
                          className={cn(
                            'w-2 h-2 rounded-full mt-2 flex-shrink-0',
                            notification.unread ? 'bg-primary-500' : 'bg-gray-600',
                          )}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-white">{notification.title}</p>
                          <p className="text-xs text-gray-400 mt-1">{notification.time}</p>
                        </div>
                      </div>
                    )}
                  </Menu.Item>
                ))}
              </div>
              <div className="p-3 border-t border-dark-600">
                <Button variant="ghost" size="sm" className="w-full">
                  View all notifications
                </Button>
              </div>
            </Menu.Items>
          </Menu>

          {/* User menu */}
          <Menu as="div" className="relative">
            <Menu.Button className="flex items-center space-x-2 p-2 text-gray-400 hover:text-white hover:bg-dark-700 rounded-lg transition-colors">
              {user.avatar ? (
<<<<<<< HEAD
                <Image
                  src={user.avatar}
=======
                <Image 
                  src={user.avatar} 
>>>>>>> main
                  alt={user.name}
                  width={32}
                  height={32}
                  className="w-8 h-8 rounded-full"
                />
              ) : (
                <UserCircleIcon className="w-8 h-8" />
              )}
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-white">{user.name}</p>
                <p className="text-xs text-gray-400 capitalize">{user.role}</p>
              </div>
            </Menu.Button>

            <Menu.Items className="absolute right-0 mt-2 w-48 bg-dark-800 border border-dark-600 rounded-xl shadow-xl z-50">
              <div className="p-1">
                <Menu.Item>
                  {({ active }) => (
                    <button
                      className={cn(
                        'flex items-center w-full px-3 py-2 text-sm text-left rounded-lg transition-colors',
                        active ? 'bg-dark-700 text-white' : 'text-gray-300',
                      )}
                      onClick={() => router.push('/profile')}
                    >
                      <UserCircleIcon className="w-4 h-4 mr-2" />
                      Profile
                    </button>
                  )}
                </Menu.Item>
                <Menu.Item>
                  {({ active }) => (
                    <button
                      className={cn(
                        'flex items-center w-full px-3 py-2 text-sm text-left rounded-lg transition-colors',
                        active ? 'bg-dark-700 text-white' : 'text-gray-300',
                      )}
                      onClick={() => router.push('/settings')}
                    >
                      <Cog6ToothIcon className="w-4 h-4 mr-2" />
                      Settings
                    </button>
                  )}
                </Menu.Item>
                <hr className="my-1 border-dark-600" />
                <Menu.Item>
                  {({ active }) => (
                    <button
                      className={cn(
                        'flex items-center w-full px-3 py-2 text-sm text-left rounded-lg transition-colors',
                        active ? 'bg-dark-700 text-error-400' : 'text-error-500',
                      )}
                      onClick={handleLogout}
                    >
                      <ArrowRightOnRectangleIcon className="w-4 h-4 mr-2" />
                      Logout
                    </button>
                  )}
                </Menu.Item>
              </div>
            </Menu.Items>
          </Menu>
        </div>
      </div>
    </header>
  )
}

export default Header
