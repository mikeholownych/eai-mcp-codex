'use client'

import React, { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import {
  LifebuoyIcon,
  PlusIcon,
  ChatBubbleBottomCenterTextIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  TagIcon,
  UserCircleIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline'

interface Ticket {
  id: string
  title: string
  description: string
  status: 'open' | 'in-progress' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  category: string
  createdAt: Date
  updatedAt: Date
  messages: TicketMessage[]
}

interface TicketMessage {
  id: string
  content: string
  isStaff: boolean
  author: string
  timestamp: Date
}

const tickets: Ticket[] = [
  {
    id: '1',
    title: 'API Rate Limiting Issues',
    description: 'Experiencing unexpected rate limiting on API calls despite being under the limit.',
    status: 'in-progress',
    priority: 'high',
    category: 'API',
    createdAt: new Date('2024-01-20T10:30:00'),
    updatedAt: new Date('2024-01-21T14:15:00'),
    messages: [
      {
        id: '1',
        content: 'Experiencing unexpected rate limiting on API calls despite being under the limit. This is affecting our production deployment.',
        isStaff: false,
        author: 'John Doe',
        timestamp: new Date('2024-01-20T10:30:00'),
      },
      {
        id: '2',
        content: 'Hi John, thank you for reaching out. We&apos;re investigating this issue. Can you please provide your API key prefix and the timestamp of when you first noticed this issue?',
        isStaff: true,
        author: 'Sarah Support',
        timestamp: new Date('2024-01-20T11:45:00'),
      },
      {
        id: '3',
        content: 'Sure! API key prefix is sk_test_abc123... and we first noticed this around 2024-01-20 at 09:00 UTC.',
        isStaff: false,
        author: 'John Doe',
        timestamp: new Date('2024-01-20T12:00:00'),
      },
      {
        id: '4',
        content: 'Thanks for the details. We&apos;ve identified the issue and are working on a fix. This should be resolved within the next 2 hours.',
        isStaff: true,
        author: 'Sarah Support',
        timestamp: new Date('2024-01-21T14:15:00'),
      },
    ],
  },
  {
    id: '2',
    title: 'Code Editor Performance',
    description: 'Code editor is running slowly with large files (>1000 lines).',
    status: 'open',
    priority: 'medium',
    category: 'Performance',
    createdAt: new Date('2024-01-19T16:20:00'),
    updatedAt: new Date('2024-01-19T16:20:00'),
    messages: [
      {
        id: '1',
        content: 'The code editor becomes very slow when working with large files over 1000 lines. Typing has a noticeable delay.',
        isStaff: false,
        author: 'John Doe',
        timestamp: new Date('2024-01-19T16:20:00'),
      },
    ],
  },
  {
    id: '3',
    title: 'Billing Discrepancy',
    description: 'Charged twice for the same subscription period.',
    status: 'resolved',
    priority: 'high',
    category: 'Billing',
    createdAt: new Date('2024-01-18T09:15:00'),
    updatedAt: new Date('2024-01-18T17:30:00'),
    messages: [
      {
        id: '1',
        content: 'I notice I was charged twice for my Pro subscription for January. Can you please look into this?',
        isStaff: false,
        author: 'John Doe',
        timestamp: new Date('2024-01-18T09:15:00'),
      },
      {
        id: '2',
        content: 'We&apos;ve reviewed your account and found the duplicate charge. A refund has been processed and should appear in your account within 3-5 business days.',
        isStaff: true,
        author: 'Mike Billing',
        timestamp: new Date('2024-01-18T17:30:00'),
      },
    ],
  },
]

const categories = [
  'General',
  'API',
  'Billing',
  'Performance',
  'Bug Report',
  'Feature Request',
  'Account',
  'Security',
]

const priorityColors = {
  low: 'bg-green-500/10 text-green-400',
  medium: 'bg-yellow-500/10 text-yellow-400',
  high: 'bg-orange-500/10 text-orange-400',
  urgent: 'bg-red-500/10 text-red-400',
}

const statusColors = {
  open: 'bg-blue-500/10 text-blue-400',
  'in-progress': 'bg-yellow-500/10 text-yellow-400',
  resolved: 'bg-green-500/10 text-green-400',
  closed: 'bg-gray-500/10 text-gray-400',
}

const statusIcons = {
  open: ClockIcon,
  'in-progress': ExclamationTriangleIcon,
  resolved: CheckCircleIcon,
  closed: CheckCircleIcon,
}

export default function SupportPage() {
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const [showNewTicketForm, setShowNewTicketForm] = useState(false)
  const [newMessage, setNewMessage] = useState('')
  const [newTicketData, setNewTicketData] = useState({
    title: '',
    description: '',
    category: 'General',
    priority: 'medium' as const,
  })
  const { user } = useAuth()

  const handleCreateTicket = (e: React.FormEvent) => {
    e.preventDefault()
    // Here you would normally send the ticket to your API
    console.log('Creating ticket:', newTicketData)
    setShowNewTicketForm(false)
    setNewTicketData({
      title: '',
      description: '',
      category: 'General',
      priority: 'medium',
    })
  }

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTicket || !newMessage.trim()) return
    
    // Here you would normally send the message to your API
    console.log('Sending message:', newMessage)
    setNewMessage('')
  }

  if (showNewTicketForm) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Create Support Ticket</h1>
            <p className="text-gray-400">Get help from our support team</p>
          </div>
          <Button
            variant="outline"
            onClick={() => setShowNewTicketForm(false)}
          >
            Cancel
          </Button>
        </div>

        <Card className="p-6">
          <form onSubmit={handleCreateTicket} className="space-y-6">
            <Input
              label="Subject"
              value={newTicketData.title}
              onChange={(value) => setNewTicketData(prev => ({ ...prev, title: value }))}
              placeholder="Brief description of your issue"
              required
            />

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={newTicketData.description}
                onChange={(e) => setNewTicketData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Please provide detailed information about your issue..."
                className="w-full h-32 bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 resize-none"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Category
                </label>
                <select
                  value={newTicketData.category}
                  onChange={(e) => setNewTicketData(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                >
                  {categories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Priority
                </label>
                <select
                  value={newTicketData.priority}
                  onChange={(e) => setNewTicketData(prev => ({ ...prev, priority: e.target.value as 'low' | 'medium' | 'high' | 'urgent' }))}
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowNewTicketForm(false)}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                Create Ticket
              </Button>
            </div>
          </form>
        </Card>
      </div>
    )
  }

  if (selectedTicket) {
    const StatusIcon = statusIcons[selectedTicket.status]
    
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedTicket(null)}
            >
              ← Back to Tickets
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-white">{selectedTicket.title}</h1>
              <p className="text-gray-400">Ticket #{selectedTicket.id}</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColors[selectedTicket.status]}`}>
              <StatusIcon className="h-4 w-4 mr-1" />
              {selectedTicket.status.replace('-', ' ').toUpperCase()}
            </span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${priorityColors[selectedTicket.priority]}`}>
              {selectedTicket.priority.toUpperCase()}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            <Card className="p-6">
              <div className="space-y-6">
                {selectedTicket.messages.map((message, index) => (
                  <div key={message.id} className={`flex ${message.isStaff ? 'justify-start' : 'justify-end'}`}>
                    <div className={`flex max-w-4xl ${message.isStaff ? 'flex-row' : 'flex-row-reverse'}`}>
                      <div className="flex-shrink-0">
                        {message.isStaff ? (
                          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                            <LifebuoyIcon className="h-4 w-4 text-white" />
                          </div>
                        ) : (
                          <UserCircleIcon className="h-8 w-8 text-gray-400" />
                        )}
                      </div>
                      
                      <div className={`mx-3 ${message.isStaff ? 'text-left' : 'text-right'}`}>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-sm font-medium text-gray-300">
                            {message.author}
                          </span>
                          {message.isStaff && (
                            <span className="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded text-xs">
                              Staff
                            </span>
                          )}
                          <span className="text-xs text-gray-500">
                            {message.timestamp.toLocaleString()}
                          </span>
                        </div>
                        
                        <div
                          className={`p-4 rounded-lg ${
                            message.isStaff
                              ? 'bg-blue-500/10 border border-blue-500/20 text-white'
                              : 'bg-slate-700/50 border border-slate-600 text-gray-200'
                          }`}
                        >
                          <div className="text-sm whitespace-pre-wrap">
                            {message.content}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {selectedTicket.status !== 'closed' && (
                <div className="mt-8 pt-6 border-t border-slate-600">
                  <form onSubmit={handleSendMessage} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Add a message
                      </label>
                      <textarea
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder="Type your message here..."
                        className="w-full h-24 bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 resize-none"
                        required
                      />
                    </div>
                    
                    <div className="flex justify-end">
                      <Button type="submit" variant="primary" disabled={!newMessage.trim()}>
                        <ChatBubbleBottomCenterTextIcon className="h-4 w-4 mr-2" />
                        Send Message
                      </Button>
                    </div>
                  </form>
                </div>
              )}
            </Card>
          </div>

          <div className="lg:col-span-1">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Ticket Details</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-400">Category</label>
                  <div className="flex items-center mt-1">
                    <TagIcon className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="text-white">{selectedTicket.category}</span>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-400">Created</label>
                  <div className="flex items-center mt-1">
                    <ClockIcon className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="text-white">{selectedTicket.createdAt.toLocaleDateString()}</span>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-400">Last Updated</label>
                  <div className="flex items-center mt-1">
                    <ClockIcon className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="text-white">{selectedTicket.updatedAt.toLocaleDateString()}</span>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-400">Messages</label>
                  <div className="flex items-center mt-1">
                    <ChatBubbleBottomCenterTextIcon className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="text-white">{selectedTicket.messages.length}</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Support Tickets</h1>
          <p className="text-gray-400">Get help from our support team</p>
        </div>
        <Button variant="primary" onClick={() => setShowNewTicketForm(true)}>
          <PlusIcon className="h-4 w-4 mr-2" />
          New Ticket
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {tickets.map((ticket) => {
          const StatusIcon = statusIcons[ticket.status]
          
          return (
            <Card key={ticket.id} className="p-6 hover:bg-slate-700/30 transition-colors cursor-pointer" onClick={() => setSelectedTicket(ticket)}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-white">{ticket.title}</h3>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusColors[ticket.status]}`}>
                      <StatusIcon className="h-3 w-3 mr-1" />
                      {ticket.status.replace('-', ' ')}
                    </span>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${priorityColors[ticket.priority]}`}>
                      {ticket.priority}
                    </span>
                  </div>
                  
                  <p className="text-gray-400 mb-3 line-clamp-2">{ticket.description}</p>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center">
                      <TagIcon className="h-4 w-4 mr-1" />
                      {ticket.category}
                    </div>
                    <div className="flex items-center">
                      <ClockIcon className="h-4 w-4 mr-1" />
                      {ticket.createdAt.toLocaleDateString()}
                    </div>
                    <div className="flex items-center">
                      <ChatBubbleBottomCenterTextIcon className="h-4 w-4 mr-1" />
                      {ticket.messages.length} messages
                    </div>
                  </div>
                </div>
                
                <ArrowRightIcon className="h-5 w-5 text-gray-400 ml-4" />
              </div>
            </Card>
          )
        })}
      </div>

      {tickets.length === 0 && (
        <Card className="p-12 text-center">
          <LifebuoyIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No support tickets</h3>
          <p className="text-gray-400 mb-6">
            You haven&apos;t created any support tickets yet. If you need help, don&apos;t hesitate to reach out!
          </p>
          <Button variant="primary" onClick={() => setShowNewTicketForm(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Your First Ticket
          </Button>
        </Card>
      )}
    </div>
  )
}