"use client";

import React from "react";
import { useAuth } from "@/contexts/AuthContext";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import {
  CodeBracketIcon,
  ChatBubbleBottomCenterTextIcon,
  DocumentTextIcon,
  ChartBarIcon,
  ClockIcon,
  CpuChipIcon,
  ArrowUpIcon,
  ArrowDownIcon,
} from "@heroicons/react/24/outline";

const quickActions = [
  {
    name: "New Code Project",
    description: "Start coding with AI assistance",
    href: "/dashboard/code-editor",
    icon: CodeBracketIcon,
    color: "from-blue-500 to-blue-600",
  },
  {
    name: "Chat with AI",
    description: "Get instant help and answers",
    href: "/dashboard/chat",
    icon: ChatBubbleBottomCenterTextIcon,
    color: "from-green-500 to-green-600",
  },
  {
    name: "Browse Projects",
    description: "View and manage your projects",
    href: "/dashboard/projects",
    icon: DocumentTextIcon,
    color: "from-purple-500 to-purple-600",
  },
];

const stats = [
  {
    name: "API Calls This Month",
    value: "2,847",
    change: "+12%",
    changeType: "increase",
    icon: CpuChipIcon,
  },
  {
    name: "Active Projects",
    value: "8",
    change: "+2",
    changeType: "increase",
    icon: DocumentTextIcon,
  },
  {
    name: "Code Generation",
    value: "156",
    change: "+8%",
    changeType: "increase",
    icon: CodeBracketIcon,
  },
  {
    name: "Chat Sessions",
    value: "42",
    change: "-5%",
    changeType: "decrease",
    icon: ChatBubbleBottomCenterTextIcon,
  },
];

const recentActivity = [
  {
    id: 1,
    type: "code",
    title: "Created React component",
    description: "UserProfile.tsx",
    time: "2 hours ago",
    icon: CodeBracketIcon,
  },
  {
    id: 2,
    type: "chat",
    title: "AI Chat Session",
    description: "Discussed authentication implementation",
    time: "4 hours ago",
    icon: ChatBubbleBottomCenterTextIcon,
  },
  {
    id: 3,
    type: "project",
    title: "Updated project settings",
    description: "E-commerce Platform",
    time: "1 day ago",
    icon: DocumentTextIcon,
  },
];

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">
          Welcome back, {user?.name?.split(" ")[0] || "User"}! 👋
        </h1>
        <p className="mt-2 text-gray-400">
          Here&apos;s what&apos;s happening with your AI development workspace
          today.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.name} className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Icon className="h-8 w-8 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-400 truncate">
                      {item.name}
                    </dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-white">
                        {item.value}
                      </div>
                      <div
                        className={`ml-2 flex items-baseline text-sm font-semibold ${
                          item.changeType === "increase"
                            ? "text-green-400"
                            : "text-red-400"
                        }`}
                      >
                        {item.changeType === "increase" ? (
                          <ArrowUpIcon className="h-4 w-4 flex-shrink-0 self-center" />
                        ) : (
                          <ArrowDownIcon className="h-4 w-4 flex-shrink-0 self-center" />
                        )}
                        <span className="sr-only">
                          {item.changeType === "increase"
                            ? "Increased"
                            : "Decreased"}{" "}
                          by
                        </span>
                        {item.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Card
                key={action.name}
                className="p-6 hover:bg-slate-700/50 transition-colors cursor-pointer"
              >
                <div className="flex items-center">
                  <div
                    className={`flex-shrink-0 w-12 h-12 bg-gradient-to-r ${action.color} rounded-lg flex items-center justify-center`}
                  >
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-sm font-medium text-white">
                      {action.name}
                    </h3>
                    <p className="text-sm text-gray-400">
                      {action.description}
                    </p>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Recent Activity and Usage Overview */}
      <div className="lg:grid lg:grid-cols-2 lg:gap-8">
        {/* Recent Activity */}
        <div>
          <h2 className="text-xl font-semibold text-white mb-4">
            Recent Activity
          </h2>
          <Card className="p-6">
            <div className="flow-root">
              <ul className="-mb-8">
                {recentActivity.map((item, itemIdx) => {
                  const Icon = item.icon;
                  return (
                    <li key={item.id}>
                      <div className="relative pb-8">
                        {itemIdx !== recentActivity.length - 1 ? (
                          <span
                            className="absolute top-5 left-5 -ml-px h-full w-0.5 bg-slate-600"
                            aria-hidden="true"
                          />
                        ) : null}
                        <div className="relative flex items-start space-x-3">
                          <div className="relative">
                            <div className="h-10 w-10 bg-slate-700 rounded-full flex items-center justify-center">
                              <Icon className="h-5 w-5 text-gray-400" />
                            </div>
                          </div>
                          <div className="min-w-0 flex-1">
                            <div>
                              <div className="text-sm">
                                <span className="font-medium text-white">
                                  {item.title}
                                </span>
                              </div>
                              <p className="mt-0.5 text-sm text-gray-400">
                                {item.description}
                              </p>
                            </div>
                            <div className="mt-2 text-sm text-gray-500">
                              <div className="flex items-center">
                                <ClockIcon className="h-4 w-4 mr-1" />
                                {item.time}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          </Card>
        </div>

        {/* Usage Overview */}
        <div>
          <h2 className="text-xl font-semibold text-white mb-4">
            Usage Overview
          </h2>
          <Card className="p-6">
            <div className="space-y-6">
              {/* API Usage */}
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-300">
                    API Calls
                  </h3>
                  <span className="text-sm text-gray-400">2,847 / 5,000</span>
                </div>
                <div className="mt-2">
                  <div className="bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-orange-500 to-orange-600 h-2 rounded-full"
                      style={{ width: "57%" }}
                    />
                  </div>
                </div>
              </div>

              {/* Storage Usage */}
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-300">Storage</h3>
                  <span className="text-sm text-gray-400">1.2 GB / 10 GB</span>
                </div>
                <div className="mt-2">
                  <div className="bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full"
                      style={{ width: "12%" }}
                    />
                  </div>
                </div>
              </div>

              {/* Bandwidth */}
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-300">
                    Bandwidth
                  </h3>
                  <span className="text-sm text-gray-400">845 MB / 2 GB</span>
                </div>
                <div className="mt-2">
                  <div className="bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full"
                      style={{ width: "42%" }}
                    />
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-600">
                <Button variant="outline" size="sm" className="w-full">
                  <ChartBarIcon className="h-4 w-4 mr-2" />
                  View Detailed Analytics
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
