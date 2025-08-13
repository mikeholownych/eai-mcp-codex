<<<<<<< HEAD
"use client";

import { AuthProvider } from "@/contexts/AuthContext";
=======
'use client'

import { AuthProvider } from '@/contexts/AuthContext'
>>>>>>> main

export default function AuthLayout({
  children,
}: {
<<<<<<< HEAD
  children: React.ReactNode;
}) {
  return <AuthProvider>{children}</AuthProvider>;
}
=======
  children: React.ReactNode
}) {
  return (
    <AuthProvider>
      {children}
    </AuthProvider>
  )
}
>>>>>>> main
