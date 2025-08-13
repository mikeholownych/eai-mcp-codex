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
  isDefault?: boolean
  isEnabled?: boolean
  metadata?: Record<string, any>
  createdAt: Date
  updatedAt: Date
}

export interface PaymentIntent {
  id: string
  customerId: string
  amount: number
  currency: string
  status: 'requires_payment_method' | 'requires_confirmation' | 'requires_action' | 'processing' | 'requires_capture' | 'canceled' | 'succeeded'
  captureMethod: 'automatic' | 'manual'
  confirmationMethod: 'automatic' | 'manual'
  providerId: string
  metadata?: Record<string, any>
  invoiceId?: string
  createdAt: Date
  updatedAt: Date
}

export interface Charge {
  id: string
  paymentIntentId: string
  amount: number
  currency: string
  status: 'succeeded' | 'pending' | 'failed' | 'canceled'
  failureCode?: string
  failureMessage?: string
  metadata?: Record<string, any>
  createdAt: Date
}

export interface Refund {
  id: string
  chargeId: string
  amount: number
  currency: string
  reason?: string
  status: 'succeeded' | 'pending' | 'failed'
  metadata?: Record<string, any>
  createdAt: Date
}

export interface SetupIntent {
  id: string
  customerId: string
  status: 'requires_payment_method' | 'requires_confirmation' | 'requires_action' | 'processing' | 'canceled' | 'succeeded'
  paymentMethodTypes: string[]
  metadata?: Record<string, any>
  createdAt: Date
  updatedAt: Date
}

export interface Mandate {
  id: string
  customerId: string
  paymentMethodId: string
  type: 'sepa' | 'ach' | 'bacs'
  status: 'active' | 'inactive' | 'pending'
  metadata?: Record<string, any>
  createdAt: Date
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

export interface Dispute {
  id: string
  chargeId: string
  amount: number
  currency: string
  reason: string
  status: 'needs_response' | 'under_review' | 'won' | 'lost'
  evidence?: Record<string, any>
  createdAt: Date
  updatedAt: Date
}

export interface Customer {
  id: string
  email: string
  name?: string
  phone?: string
  address?: {
    line1?: string
    line2?: string
    city?: string
    state?: string
    postalCode?: string
    country?: string
  }
  metadata?: Record<string, any>
  createdAt: Date
  updatedAt: Date
}

// Payment API Request/Response Types
export interface CreatePaymentIntentRequest {
  customerId: string
  amount: number
  currency: string
  captureMethod?: 'automatic' | 'manual'
  confirmationMethod?: 'automatic' | 'manual'
  metadata?: Record<string, any>
  idempotencyKey?: string
}

export interface CreatePaymentMethodRequest {
  customerId: string
  paymentMethodType: string
  paymentMethodData: Record<string, any>
  idempotencyKey?: string
}

export interface SetupIntentRequest {
  customerId: string
  paymentMethodTypes: string[]
  metadata?: Record<string, any>
  idempotencyKey?: string
}

export interface MandateRequest {
  customerId: string
  paymentMethodId: string
  type: 'sepa' | 'ach' | 'bacs'
  metadata?: Record<string, any>
}

export interface PaymentMethodEligibilityRequest {
  paymentMethodType: string
  currency: string
  country?: string
}

export interface PaymentMethodEligibilityResponse {
  eligible: boolean
  requirements?: string[]
  restrictions?: string[]
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
  type?: 'button' | 'submit' | 'reset'
  title?: string
<<<<<<< HEAD
  href?: string
=======
>>>>>>> main
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
export interface ApiResponse<T = unknown> {
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
  payload: unknown
  timestamp: Date
  sessionId?: string
}

// Feature Flag Types
export interface FeatureFlag {
  key: string
  enabled: boolean
  rolloutPercentage: number
  conditions?: Record<string, unknown>
}

// Audit Log Types
export interface AuditLog {
  id: string
  userId: string
  tenantId: string
  action: string
  resource: string
  resourceId: string
  details: Record<string, unknown>
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

// Model Router Types
export interface ModelRouteRequest {
  text: string
  request_id: string
  temperature?: number
  max_tokens?: number
  task_type?: string
  priority?: string
  system_prompt?: string
  context?: Record<string, unknown>
}

export interface ModelRouteResponse {
  request_id: string
  model: string
  response: string
  tokens_used: number
  processing_time: number
  confidence: number
  timestamp: Date
}

export interface AvailableModel {
  id: string
  name: string
  description: string
  parameters: {
    max_tokens: number
    temperature: {
      min: number
      max: number
      default: number
    }
  }
  status: 'available' | 'unavailable' | 'degraded'
}

export interface ModelStats {
  total_requests: number
  successful_requests: number
  failed_requests: number
  average_response_time: number
  tokens_used: number
<<<<<<< HEAD
  model_usage: Record<
    string,
    {
      requests: number
      tokens: number
      avg_response_time: number
    }
  >
=======
  model_usage: Record<string, {
    requests: number
    tokens: number
    avg_response_time: number
  }>
>>>>>>> main
}

// System Health Types
export interface SystemHealth {
  api_performance: {
    status: 'healthy' | 'warning' | 'critical'
    success_rate: number
    avg_response_time: number
  }
  database_status: {
    status: 'healthy' | 'optimal' | 'moderate' | 'critical'
    utilization: number
    connection_pool: string
  }
  memory_usage: {
    status: 'healthy' | 'optimal' | 'moderate' | 'critical'
    usage_percent: number
    available_gb: number
  }
  service_status: Record<string, 'healthy' | 'warning' | 'critical'>
}

// Error Types
export interface AppError {
  code: string
  message: string
  details?: Record<string, unknown>
  timestamp: Date
}
