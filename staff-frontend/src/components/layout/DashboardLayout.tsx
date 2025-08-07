"use client";

import React from "react";
import { cn } from "@/lib/utils";
import Sidebar from "./Sidebar";
import Header from "./Header";

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  user?: {
    name: string;
    email: string;
    avatar?: string;
    role: string;
    plan: string;
  };
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  title,
  subtitle,
  className,
  user = {
    name: "John Doe",
    email: "john@example.com",
    role: "customer",
    plan: "standard",
  },
}) => {
  return (
    <div className="flex h-screen bg-dark-900">
      {/* Sidebar */}
      <Sidebar role={user.role} plan={user.plan} />

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header title={title} subtitle={subtitle} user={user} />

        {/* Page content */}
        <main
          className={cn(
            "flex-1 overflow-y-auto p-6 custom-scrollbar",
            className,
          )}
        >
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
