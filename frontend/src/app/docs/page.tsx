'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import {
  ArrowLeftIcon,
  BookOpenIcon,
  CodeBracketIcon,
  CogIcon,
  ShieldCheckIcon,
  RocketLaunchIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'

const documentationSections = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: RocketLaunchIcon,
    description: 'Quick setup and first steps with the MCP Agent Network',
    articles: [
      { title: 'Installation & Setup', href: '#installation', time: '5 min' },
      { title: 'Your First AI Agent', href: '#first-agent', time: '10 min' },
      { title: 'Authentication & API Keys', href: '#auth', time: '3 min' },
      { title: 'Project Configuration', href: '#config', time: '8 min' },
    ],
  },
  {
    id: 'api-reference',
    title: 'API Reference',
    icon: CodeBracketIcon,
    description: 'Complete API documentation and code examples',
    articles: [
      { title: 'REST API Overview', href: '#rest-api', time: '12 min' },
      { title: 'WebSocket Integration', href: '#websocket', time: '15 min' },
      { title: 'Agent Communication Protocol', href: '#agent-protocol', time: '20 min' },
      { title: 'Error Handling', href: '#errors', time: '8 min' },
    ],
  },
  {
    id: 'security',
    title: 'Security & Compliance',
    icon: ShieldCheckIcon,
    description: 'Security best practices and compliance guidelines',
    articles: [
      { title: 'Security Architecture', href: '#security-arch', time: '15 min' },
      { title: 'SOC 2 Compliance', href: '#soc2', time: '10 min' },
      { title: 'Data Encryption', href: '#encryption', time: '12 min' },
      { title: 'Audit Logging', href: '#audit-logs', time: '8 min' },
    ],
  },
  {
    id: 'configuration',
    title: 'Configuration',
    icon: CogIcon,
    description: 'System configuration and customization options',
    articles: [
      { title: 'Environment Variables', href: '#env-vars', time: '5 min' },
      { title: 'Agent Configuration', href: '#agent-config', time: '12 min' },
      { title: 'Workflow Orchestration', href: '#workflows', time: '18 min' },
      { title: 'Custom Integrations', href: '#integrations', time: '25 min' },
    ],
  },
]

const quickLinks = [
  { title: 'Installation Guide', href: '#installation', category: 'Setup' },
  { title: 'API Authentication', href: '#auth', category: 'Security' },
  { title: 'Agent Collaboration', href: '#collaboration', category: 'Advanced' },
  { title: 'Troubleshooting', href: '#troubleshooting', category: 'Support' },
  { title: 'Best Practices', href: '#best-practices', category: 'Guide' },
  { title: 'Performance Tuning', href: '#performance', category: 'Optimization' },
]

export default function DocsPage() {
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Navigation */}
      <nav className="border-b border-slate-700 bg-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Link
                href="/"
                className="flex items-center text-slate-300 hover:text-white transition-colors"
              >
                <ArrowLeftIcon className="w-5 h-5 mr-2" />
                Back to Home
              </Link>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <span className="text-xl font-bold text-white">Ethical AI Insider</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Documentation Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">Documentation</h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-8">
            Comprehensive guides and references for the MCP Agent Network platform
          </p>

          {/* Search Bar */}
          <div className="max-w-md mx-auto relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search documentation..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Quick Links */}
        <Card className="mb-12">
          <Card.Header>
            <h2 className="text-xl font-semibold text-white flex items-center">
              <RocketLaunchIcon className="w-6 h-6 mr-2 text-purple-400" />
              Quick Links
            </h2>
          </Card.Header>
          <Card.Content>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {quickLinks.map((link, index) => (
                <a
                  key={index}
                  href={link.href}
                  className="p-3 rounded-lg bg-slate-700 hover:bg-slate-600 transition-colors group"
                >
                  <div className="text-sm text-purple-400 mb-1">{link.category}</div>
                  <div className="text-white group-hover:text-purple-300 transition-colors">
                    {link.title}
                  </div>
                </a>
              ))}
            </div>
          </Card.Content>
        </Card>

        {/* Documentation Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {documentationSections.map(section => {
            const IconComponent = section.icon
            return (
              <Card key={section.id} hover>
                <Card.Header>
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                      <IconComponent className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-white">{section.title}</h3>
                  </div>
                  <p className="text-gray-400">{section.description}</p>
                </Card.Header>

                <Card.Content>
                  <div className="space-y-3">
                    {section.articles.map((article, index) => (
                      <a
                        key={index}
                        href={article.href}
                        className="flex items-center justify-between p-2 rounded-md hover:bg-slate-700 transition-colors group"
                      >
                        <div className="flex items-center space-x-3">
                          <DocumentTextIcon className="w-4 h-4 text-gray-400 group-hover:text-purple-400" />
                          <span className="text-gray-300 group-hover:text-white">
                            {article.title}
                          </span>
                        </div>
                        <span className="text-sm text-gray-500">{article.time}</span>
                      </a>
                    ))}
                  </div>
                </Card.Content>

                <Card.Footer>
                  <Button variant="ghost" size="sm" className="w-full">
                    View All {section.title} Docs
                  </Button>
                </Card.Footer>
              </Card>
            )
          })}
        </div>

        {/* Additional Resources */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <Card.Header>
              <BookOpenIcon className="w-8 h-8 text-blue-400 mb-2" />
              <h3 className="text-lg font-semibold text-white">Tutorials</h3>
            </Card.Header>
            <Card.Content>
              <p className="text-gray-400 text-sm mb-4">
                Step-by-step guides for common use cases and implementation patterns.
              </p>
              <Button variant="outline" size="sm" className="w-full">
                Browse Tutorials
              </Button>
            </Card.Content>
          </Card>

          <Card>
            <Card.Header>
              <CodeBracketIcon className="w-8 h-8 text-green-400 mb-2" />
              <h3 className="text-lg font-semibold text-white">Code Examples</h3>
            </Card.Header>
            <Card.Content>
              <p className="text-gray-400 text-sm mb-4">
                Ready-to-use code snippets and integration examples for popular frameworks.
              </p>
              <Button variant="outline" size="sm" className="w-full">
                View Examples
              </Button>
            </Card.Content>
          </Card>

          <Card>
            <Card.Header>
              <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center mb-2">
                <span className="text-white font-bold text-sm">?</span>
              </div>
              <h3 className="text-lg font-semibold text-white">Support</h3>
            </Card.Header>
            <Card.Content>
              <p className="text-gray-400 text-sm mb-4">
                Need help? Get support from our team and community of developers.
              </p>
              <Button variant="outline" size="sm" className="w-full">
                Get Support
              </Button>
            </Card.Content>
          </Card>
        </div>

        {/* Coming Soon Notice */}
        <Card className="mt-12">
          <Card.Content className="text-center py-8">
            <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <DocumentTextIcon className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Comprehensive Documentation Coming Soon
            </h3>
            <p className="text-gray-400 mb-6 max-w-2xl mx-auto">
              We&apos;re working on detailed documentation covering every aspect of the MCP Agent
              Network. In the meantime, reach out to our team for specific questions or
              implementation guidance.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/contact">
                <Button variant="secondary">Contact Support</Button>
              </Link>
              <Link href="/register">
                <Button variant="outline">Get Early Access</Button>
              </Link>
            </div>
          </Card.Content>
        </Card>
      </div>
    </div>
  )
}
