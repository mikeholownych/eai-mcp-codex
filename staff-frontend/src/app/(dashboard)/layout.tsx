<<<<<<< HEAD
"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
=======
'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
>>>>>>> main
import {
  HomeIcon,
  CodeBracketIcon,
  ChatBubbleBottomCenterTextIcon,
  DocumentTextIcon,
  CreditCardIcon,
  LifebuoyIcon,
  CogIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  Bars3Icon,
  XMarkIcon,
  BellIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
<<<<<<< HEAD
} from "@heroicons/react/24/outline";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: HomeIcon },
  {
    name: "Code Editor",
    href: "/dashboard/code-editor",
    icon: CodeBracketIcon,
  },
  {
    name: "AI Assistant",
    href: "/dashboard/chat",
    icon: ChatBubbleBottomCenterTextIcon,
  },
  { name: "Projects", href: "/dashboard/projects", icon: DocumentTextIcon },
  { name: "Billing", href: "/dashboard/billing", icon: CreditCardIcon },
  { name: "Support", href: "/dashboard/support", icon: LifebuoyIcon },
  { name: "Settings", href: "/dashboard/settings", icon: CogIcon },
];

function DashboardContent({ children }: { children: React.ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };
=======
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Code Editor', href: '/dashboard/code-editor', icon: CodeBracketIcon },
  { name: 'AI Assistant', href: '/dashboard/chat', icon: ChatBubbleBottomCenterTextIcon },
  { name: 'Projects', href: '/dashboard/projects', icon: DocumentTextIcon },
  { name: 'Billing', href: '/dashboard/billing', icon: CreditCardIcon },
  { name: 'Support', href: '/dashboard/support', icon: LifebuoyIcon },
  { name: 'Settings', href: '/dashboard/settings', icon: CogIcon },
]

function DashboardContent({ children }: { children: React.ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { user, logout } = useAuth()
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = async () => {
    await logout()
    router.push('/')
  }
>>>>>>> main

  return (
    <div className="min-h-screen bg-slate-900 flex">
      {/* Desktop Sidebar */}
      <div
        className={`hidden lg:fixed lg:inset-y-0 lg:flex lg:flex-col transition-all duration-300 ${
<<<<<<< HEAD
          sidebarCollapsed ? "lg:w-20" : "lg:w-64"
=======
          sidebarCollapsed ? 'lg:w-20' : 'lg:w-64'
>>>>>>> main
        }`}
      >
        <div className="flex flex-col flex-grow pt-5 bg-slate-800 overflow-y-auto border-r border-slate-700">
          {/* Logo */}
          <div className="flex items-center flex-shrink-0 px-4">
            <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AI</span>
            </div>
            {!sidebarCollapsed && (
              <div className="ml-3">
                <h1 className="text-lg font-semibold text-white">Ethical AI</h1>
                <p className="text-xs text-gray-400">Insider</p>
              </div>
            )}
          </div>

          {/* Collapse Toggle */}
          <div className="px-4 mt-4">
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="w-full flex items-center justify-center p-2 text-gray-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            >
              {sidebarCollapsed ? (
                <ChevronRightIcon className="w-5 h-5" />
              ) : (
                <ChevronLeftIcon className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Navigation */}
          <nav className="mt-8 flex-1 px-2 pb-4 space-y-1">
            {navigation.map((item) => {
<<<<<<< HEAD
              const Icon = item.icon;
              const isActive = pathname === item.href;

=======
              const Icon = item.icon
              const isActive = pathname === item.href
              
>>>>>>> main
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
<<<<<<< HEAD
                      ? "bg-orange-500/10 text-orange-400 border-r-2 border-orange-500"
                      : "text-gray-300 hover:bg-slate-700 hover:text-white"
=======
                      ? 'bg-orange-500/10 text-orange-400 border-r-2 border-orange-500'
                      : 'text-gray-300 hover:bg-slate-700 hover:text-white'
>>>>>>> main
                  }`}
                >
                  <Icon
                    className={`flex-shrink-0 w-6 h-6 ${
<<<<<<< HEAD
                      isActive
                        ? "text-orange-400"
                        : "text-gray-400 group-hover:text-gray-300"
                    }`}
                  />
                  {!sidebarCollapsed && (
                    <span className="ml-3">{item.name}</span>
                  )}
                </Link>
              );
=======
                      isActive ? 'text-orange-400' : 'text-gray-400 group-hover:text-gray-300'
                    }`}
                  />
                  {!sidebarCollapsed && <span className="ml-3">{item.name}</span>}
                </Link>
              )
>>>>>>> main
            })}
          </nav>

          {/* User Profile */}
          <div className="flex-shrink-0 p-4 border-t border-slate-700">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <UserCircleIcon className="w-8 h-8 text-gray-400" />
              </div>
              {!sidebarCollapsed && (
                <div className="ml-3 flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
<<<<<<< HEAD
                    {user?.name || "User"}
=======
                    {user?.name || 'User'}
>>>>>>> main
                  </p>
                  <p className="text-xs text-gray-400 truncate">
                    {user?.email}
                  </p>
                </div>
              )}
            </div>
            {!sidebarCollapsed && (
              <button
                onClick={handleLogout}
                className="mt-2 w-full flex items-center px-2 py-2 text-sm text-gray-300 hover:bg-slate-700 hover:text-white rounded-md transition-colors"
              >
                <ArrowRightOnRectangleIcon className="w-4 h-4 mr-2" />
                Sign out
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Mobile menu */}
<<<<<<< HEAD
      <div className={`lg:hidden ${mobileMenuOpen ? "block" : "hidden"}`}>
        <div className="fixed inset-0 flex z-40">
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-75"
            onClick={() => setMobileMenuOpen(false)}
          />
=======
      <div className={`lg:hidden ${mobileMenuOpen ? 'block' : 'hidden'}`}>
        <div className="fixed inset-0 flex z-40">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setMobileMenuOpen(false)} />
>>>>>>> main
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-slate-800">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              >
                <XMarkIcon className="h-6 w-6 text-white" />
              </button>
            </div>
            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <div className="flex-shrink-0 flex items-center px-4">
                <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">AI</span>
                </div>
                <div className="ml-3">
<<<<<<< HEAD
                  <h1 className="text-lg font-semibold text-white">
                    Ethical AI
                  </h1>
=======
                  <h1 className="text-lg font-semibold text-white">Ethical AI</h1>
>>>>>>> main
                  <p className="text-xs text-gray-400">Insider</p>
                </div>
              </div>
              <nav className="mt-5 px-2 space-y-1">
                {navigation.map((item) => {
<<<<<<< HEAD
                  const Icon = item.icon;
                  const isActive = pathname === item.href;

=======
                  const Icon = item.icon
                  const isActive = pathname === item.href
                  
>>>>>>> main
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`group flex items-center px-2 py-2 text-base font-medium rounded-md transition-colors ${
                        isActive
<<<<<<< HEAD
                          ? "bg-orange-500/10 text-orange-400"
                          : "text-gray-300 hover:bg-slate-700 hover:text-white"
=======
                          ? 'bg-orange-500/10 text-orange-400'
                          : 'text-gray-300 hover:bg-slate-700 hover:text-white'
>>>>>>> main
                      }`}
                    >
                      <Icon className="mr-4 flex-shrink-0 h-6 w-6" />
                      {item.name}
                    </Link>
<<<<<<< HEAD
                  );
=======
                  )
>>>>>>> main
                })}
              </nav>
            </div>
            <div className="flex-shrink-0 flex border-t border-slate-700 p-4">
              <div className="flex items-center">
                <div>
                  <UserCircleIcon className="w-10 h-10 text-gray-400" />
                </div>
                <div className="ml-3">
<<<<<<< HEAD
                  <p className="text-base font-medium text-white">
                    {user?.name || "User"}
                  </p>
                  <p className="text-sm font-medium text-gray-400">
                    {user?.email}
                  </p>
=======
                  <p className="text-base font-medium text-white">{user?.name || 'User'}</p>
                  <p className="text-sm font-medium text-gray-400">{user?.email}</p>
>>>>>>> main
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
<<<<<<< HEAD
      <div
        className={`flex-1 flex flex-col ${sidebarCollapsed ? "lg:pl-20" : "lg:pl-64"}`}
      >
=======
      <div className={`flex-1 flex flex-col ${sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-64'}`}>
>>>>>>> main
        {/* Top bar */}
        <div className="sticky top-0 z-10 flex-shrink-0 flex h-16 bg-slate-800 border-b border-slate-700">
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="px-4 border-r border-slate-700 text-gray-400 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-orange-500 lg:hidden"
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
<<<<<<< HEAD

          <div className="flex-1 px-4 flex justify-between items-center">
            <div className="flex-1" />

=======
          
          <div className="flex-1 px-4 flex justify-between items-center">
            <div className="flex-1" />
            
>>>>>>> main
            <div className="ml-4 flex items-center md:ml-6 space-x-4">
              {/* Notifications */}
              <button className="p-2 text-gray-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
                <BellIcon className="h-6 w-6" />
              </button>
<<<<<<< HEAD

=======
              
>>>>>>> main
              {/* User menu */}
              <div className="relative ml-3">
                <button className="flex items-center text-sm text-gray-400 hover:text-white transition-colors">
                  <UserCircleIcon className="w-8 h-8" />
                  <span className="ml-2 hidden md:block">{user?.name}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
<<<<<<< HEAD
  );
=======
  )
>>>>>>> main
}

export default function DashboardLayout({
  children,
}: {
<<<<<<< HEAD
  children: React.ReactNode;
=======
  children: React.ReactNode
>>>>>>> main
}) {
  return (
    <AuthProvider>
      <DashboardContent>{children}</DashboardContent>
    </AuthProvider>
<<<<<<< HEAD
  );
}
=======
  )
}
>>>>>>> main
