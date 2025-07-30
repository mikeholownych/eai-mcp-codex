// User and Authentication Types
export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role: UserRole
  plan: UserPlan
  tenantId: string
  createdAt: Date
  lastLoginAt?: Date
  preferences: UserPreferences
  status: 'active' | 'inactive' | 'suspended'
}

export interface UserPreferences {
  theme: 'dark' | 'light'
  language: string
  notifications: {
    email: boolean
    push: boolean
    billing: boolean
    updates: boolean
  }
  editor: {
    fontSize: number
    theme: string
    autoSave: boolean
    wordWrap: boolean
  }
}

export type UserRole = 
  | 'superadmin' 
  | 'admin' 
  | 'marketing' 
  | 'sales' 
  | 'billing' 
  | 'support' 
  | 'tech' 
  | 'finance' 
  | 'legal' 
  | 'customer'

export type UserPlan = 'free' | 'standard' | 'pro' | 'enterprise'

// Tenant and Organization Types
export interface Tenant {
  id: string
  name: string
  domain: string
  plan: UserPlan
  status: 'active' | 'suspended' | 'trial'
  settings: TenantSettings
  usage: TenantUsage
  createdAt: Date
  expiresAt?: Date
}

export interface TenantSettings {
  branding: {
    logo?: string
    primaryColor: string
    secondaryColor: string
  }
  features: {
    codeGeneration: boolean
    collaboration: boolean
    videoLibrary: boolean
    advancedAnalytics: boolean
  }
  limits: {
    users: number
    storage: number
    apiCalls: number
  }
}

export interface TenantUsage {
  users: number
  storage: number
  apiCalls: number
  lastResetAt: Date
}

// Code Generation and AI Types
export interface CodeRequest {
  id: string
  prompt: string
  language: string
  model: string
  userId: string
  tenantId: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  result?: CodeResult
  createdAt: Date
  completedAt?: Date
}

export interface CodeResult {
  code: string
  explanation: string
  metadata: {
    tokensUsed: number
    processingTime: number
    confidence: number
  }
}

// Chat and RAG Types
export interface ChatSession {
  id: string
  userId: string
  tenantId: string
  title: string
  messages: ChatMessage[]
  context: ChatContext
  createdAt: Date
  updatedAt: Date
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata?: {
    sources?: string[]
    confidence?: number
    tokensUsed?: number
  }
  timestamp: Date
}

export interface ChatContext {
  documentIds: string[]
  tags: string[]
  priority: number
}

// Content Management Types
export interface BlogPost {
  id: string
  title: string
  slug: string
  content: string
  excerpt: string
  authorId: string
  status: 'draft' | 'published' | 'archived'
  tags: string[]
  featuredImage?: string
  publishedAt?: Date
  createdAt: Date
  updatedAt: Date
}

export interface VideoContent {
  id: string
  title: string
  description: string
  url: string
  thumbnail?: string
  duration: number
  tags: string[]
  planLevel: UserPlan[]
  views: number
  createdAt: Date
  updatedAt: Date
}

// Support and Tickets Types
export interface SupportTicket {
  id: string
  title: string
  description: string
  status: 'open' | 'in_progress' | 'waiting' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  userId: string
  assignedTo?: string
  tags: string[]
  messages: TicketMessage[]
  createdAt: Date
  resolvedAt?: Date
}

export interface TicketMessage {
  id: string
  ticketId: string
  userId: string
  content: string
  isInternal: boolean
  attachments: string[]
  createdAt: Date
}

// Billing and Finance Types
export interface Subscription {
  id: string
  tenantId: string
  plan: UserPlan
  status: 'active' | 'canceled' | 'past_due' | 'unpaid'
  currentPeriodStart: Date
  currentPeriodEnd: Date
  canceledAt?: Date
  amount: number
  currency: string
  paymentMethod: PaymentMethod
}

export interface PaymentMethod {
  id: string
  type: 'card' | 'paypal' | 'bank_transfer'
  last4?: string
  brand?: string
  expiryMonth?: number
  expiryYear?: number
}

export interface Invoice {
  id: string
  tenantId: string
  amount: number
  currency: string
  status: 'draft' | 'open' | 'paid' | 'void'
  dueDate: Date
  paidAt?: Date
  items: InvoiceItem[]
  createdAt: Date
}

export interface InvoiceItem {
  description: string
  quantity: number
  unitPrice: number
  amount: number
}

// Analytics and Reporting Types
export interface AnalyticsData {
  metric: string
  value: number
  change: number
  changeType: 'increase' | 'decrease' | 'neutral'
  period: 'day' | 'week' | 'month' | 'year'
  data: DataPoint[]
}

export interface DataPoint {
  date: Date
  value: number
  label?: string
}

// UI Component Types
export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  children: React.ReactNode
  onClick?: () => void
  className?: string
}

export interface InputProps {
  label?: string
  placeholder?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url'
  value?: string
  onChange?: (value: string) => void
  error?: string
  disabled?: boolean
  required?: boolean
  className?: string
}

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
  pagination?: PaginationMeta
}

export interface PaginationMeta {
  page: number
  limit: number
  total: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

// WebSocket Types
export interface WebSocketMessage {
  type: string
  payload: any
  timestamp: Date
  sessionId?: string
}

// Feature Flag Types
export interface FeatureFlag {
  key: string
  enabled: boolean
  rolloutPercentage: number
  conditions?: Record<string, any>
}

// Audit Log Types
export interface AuditLog {
  id: string
  userId: string
  tenantId: string
  action: string
  resource: string
  resourceId: string
  details: Record<string, any>
  ipAddress: string
  userAgent: string
  createdAt: Date
}

// Configuration Types
export interface AppConfig {
  apiUrl: string
  wsUrl: string
  features: Record<string, boolean>
  limits: Record<string, number>
  integrations: {
    stripe: {
      publicKey: string
    }
    paypal: {
      clientId: string
    }
  }
}

// Error Types
export interface AppError {
  code: string
  message: string
  details?: Record<string, any>
  timestamp: Date
}