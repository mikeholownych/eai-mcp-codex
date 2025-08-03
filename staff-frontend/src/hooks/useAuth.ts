'use client'

import { useRouter } from 'next/navigation'
import { useAuth as useAuthContext } from '@/contexts/AuthContext'

export function useAuth() {
  return useAuthContext()
}

export function useRequireAuth() {
  const auth = useAuthContext()
  const router = useRouter()

  if (!auth.loading && !auth.isAuthenticated) {
    router.push('/login')
    return null
  }

  return auth
}

export function useRequireRole(allowedRoles: string[]) {
  const auth = useAuthContext()
  const router = useRouter()

  if (!auth.loading && auth.user && !allowedRoles.includes(auth.user.role)) {
    router.push('/unauthorized')
    return null
  }

  return auth
}