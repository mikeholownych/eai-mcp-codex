"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import {
  HomeIcon,
  UserGroupIcon,
  LifebuoyIcon,
  CreditCardIcon,
  CogIcon,
  ShieldCheckIcon,
  DocumentTextIcon,
  VideoCameraIcon,
  ChatBubbleBottomCenterTextIcon,
  ExclamationTriangleIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  Bars3Icon,
  XMarkIcon,
  BellIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
} from "@heroicons/react/24/outline";

const navigation = [
  {
    name: "Dashboard",
    href: "/staff",
    icon: HomeIcon,
    roles: ["admin", "manager", "support"],
  },
  {
    name: "User Management",
    href: "/staff/users",
    icon: UserGroupIcon,
    roles: ["admin", "manager"],
  },
  {
    name: "Support Tickets",
    href: "/staff/tickets",
    icon: LifebuoyIcon,
    roles: ["admin", "manager", "support"],
  },
  {
    name: "Financial Suite",
    href: "/staff/finance",
    icon: CreditCardIcon,
    roles: ["admin", "cfo", "finance"],
  },
  {
    name: "Blog Management",
    href: "/staff/blog",
    icon: DocumentTextIcon,
    roles: ["admin", "manager", "content"],
  },
  {
    name: "Video Library",
    href: "/staff/videos",
    icon: VideoCameraIcon,
    roles: ["admin", "manager", "content"],
  },
  {
    name: "System Health",
    href: "/staff/system",
    icon: ExclamationTriangleIcon,
    roles: ["admin", "manager"],
  },
  {
    name: "Security Center",
    href: "/staff/security",
    icon: ShieldCheckIcon,
    roles: ["admin"],
  },
  {
    name: "Staff Chat",
    href: "/staff/chat",
    icon: ChatBubbleBottomCenterTextIcon,
    roles: ["admin", "manager", "support"],
  },
  {
    name: "Settings",
    href: "/staff/settings",
    icon: CogIcon,
    roles: ["admin", "manager"],
  },
];

function StaffContent({ children }: { children: React.ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  // Check if user has staff role
  if (
    !user ||
    !["admin", "manager", "support", "content", "cfo", "finance"].includes(
      user.role,
    )
  ) {
    router.push("/unauthorized");
    return null;
  }

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

  // Filter navigation items based on user role
  const filteredNavigation = navigation.filter((item) =>
    item.roles.includes(user.role),
  );

  const ROLE_BADGE_COLORS: Record<string, string> = {
    admin: "bg-red-500/10 text-red-400",
    cfo: "bg-yellow-500/10 text-yellow-400",
    finance: "bg-yellow-500/10 text-yellow-400",
    manager: "bg-blue-500/10 text-blue-400",
    support: "bg-green-500/10 text-green-400",
    content: "bg-purple-500/10 text-purple-400",
  };

  const getRoleBadgeColor = (role: string) =>
    ROLE_BADGE_COLORS[role] ?? "bg-gray-500/10 text-gray-400";

  return (
    <div className="min-h-screen bg-slate-900 flex">
      {/* Desktop Sidebar */}
      <div
        className={`hidden lg:fixed lg:inset-y-0 lg:flex lg:flex-col transition-all duration-300 ${
          sidebarCollapsed ? "lg:w-20" : "lg:w-64"
        }`}
      >
        <div className="flex flex-col flex-grow pt-5 bg-slate-800 overflow-y-auto border-r border-slate-700">
          {/* Logo */}
          <div className="flex items-center flex-shrink-0 px-4">
            <div className="w-8 h-8 bg-gradient-to-r from-red-500 to-red-600 rounded-lg flex items-center justify-center">
              <ShieldCheckIcon className="h-4 w-4 text-white" />
            </div>
            {!sidebarCollapsed && (
              <div className="ml-3">
                <h1 className="text-lg font-semibold text-white">
                  Staff Portal
                </h1>
                <p className="text-xs text-gray-400">Admin Dashboard</p>
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
            {filteredNavigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? "bg-red-500/10 text-red-400 border-r-2 border-red-500"
                      : "text-gray-300 hover:bg-slate-700 hover:text-white"
                  }`}
                >
                  <Icon
                    className={`flex-shrink-0 w-6 h-6 ${
                      isActive
                        ? "text-red-400"
                        : "text-gray-400 group-hover:text-gray-300"
                    }`}
                  />
                  {!sidebarCollapsed && (
                    <span className="ml-3">{item.name}</span>
                  )}
                </Link>
              );
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
                    {user?.name || "Staff User"}
                  </p>
                  <div className="flex items-center mt-1">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getRoleBadgeColor(user.role)}`}
                    >
                      {user.role.toUpperCase()}
                    </span>
                  </div>
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
      <div className={`lg:hidden ${mobileMenuOpen ? "block" : "hidden"}`}>
        <div className="fixed inset-0 flex z-40">
          <div
            className="fixed inset-0 bg-gray-600 bg-opacity-75"
            onClick={() => setMobileMenuOpen(false)}
          />
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
                <div className="w-8 h-8 bg-gradient-to-r from-red-500 to-red-600 rounded-lg flex items-center justify-center">
                  <ShieldCheckIcon className="h-4 w-4 text-white" />
                </div>
                <div className="ml-3">
                  <h1 className="text-lg font-semibold text-white">
                    Staff Portal
                  </h1>
                  <p className="text-xs text-gray-400">Admin Dashboard</p>
                </div>
              </div>
              <nav className="mt-5 px-2 space-y-1">
                {filteredNavigation.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`group flex items-center px-2 py-2 text-base font-medium rounded-md transition-colors ${
                        isActive
                          ? "bg-red-500/10 text-red-400"
                          : "text-gray-300 hover:bg-slate-700 hover:text-white"
                      }`}
                    >
                      <Icon className="mr-4 flex-shrink-0 h-6 w-6" />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
            </div>
            <div className="flex-shrink-0 flex border-t border-slate-700 p-4">
              <div className="flex items-center">
                <div>
                  <UserCircleIcon className="w-10 h-10 text-gray-400" />
                </div>
                <div className="ml-3">
                  <p className="text-base font-medium text-white">
                    {user?.name || "Staff User"}
                  </p>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getRoleBadgeColor(user.role)}`}
                  >
                    {user.role.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div
        className={`flex-1 flex flex-col ${sidebarCollapsed ? "lg:pl-20" : "lg:pl-64"}`}
      >
        {/* Top bar */}
        <div className="sticky top-0 z-10 flex-shrink-0 flex h-16 bg-slate-800 border-b border-slate-700">
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="px-4 border-r border-slate-700 text-gray-400 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-red-500 lg:hidden"
          >
            <Bars3Icon className="h-6 w-6" />
          </button>

          <div className="flex-1 px-4 flex justify-between items-center">
            <div className="flex-1" />

            <div className="ml-4 flex items-center md:ml-6 space-x-4">
              {/* Notifications */}
              <button className="p-2 text-gray-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors relative">
                <BellIcon className="h-6 w-6" />
                <span className="absolute top-1 right-1 block h-2 w-2 rounded-full bg-red-500"></span>
              </button>

              {/* User menu */}
              <div className="relative ml-3">
                <button className="flex items-center text-sm text-gray-400 hover:text-white transition-colors">
                  <UserCircleIcon className="w-8 h-8" />
                  <span className="ml-2 hidden md:block">{user?.name}</span>
                  <span
                    className={`ml-2 hidden md:inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getRoleBadgeColor(user.role)}`}
                  >
                    {user.role.toUpperCase()}
                  </span>
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
  );
}

export default function StaffLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <StaffContent>{children}</StaffContent>
    </AuthProvider>
  );
}
