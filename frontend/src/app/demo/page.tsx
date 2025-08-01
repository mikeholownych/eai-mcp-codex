'use client'

import React from 'react'
import Link from 'next/link'
import { PlayIcon, ArrowLeftIcon } from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'

export default function DemoPage() {
  return (
    <div className="min-h-screen bg-slate-900">
      {/* Navigation */}
      <nav className="border-b border-slate-700 bg-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Link href="/" className="flex items-center text-slate-300 hover:text-white transition-colors">
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

      {/* Demo Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Interactive Demo
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Experience the power of our AI-driven development platform. See how our agents collaborate to generate production-ready code.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          <Card>
            <Card.Header>
              <div className="flex items-center space-x-3">
                <PlayIcon className="w-8 h-8 text-purple-400" />
                <h3 className="text-xl font-semibold text-white">Live Code Generation</h3>
              </div>
            </Card.Header>
            <Card.Content>
              <p className="text-gray-400 mb-4">
                Watch our AI agents collaborate in real-time to generate complex applications, 
                from React components to full-stack APIs.
              </p>
              <Button variant="secondary" className="w-full">
                Start Interactive Demo
              </Button>
            </Card.Content>
          </Card>

          <Card>
            <Card.Header>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">AI</span>
                </div>
                <h3 className="text-xl font-semibold text-white">Agent Collaboration</h3>
              </div>
            </Card.Header>
            <Card.Content>
              <p className="text-gray-400 mb-4">
                See how multiple specialized agents work together: security audits, 
                code reviews, performance optimization, and more.
              </p>
              <Button variant="outline" className="w-full">
                View Agent Network
              </Button>
            </Card.Content>
          </Card>
        </div>

        <Card className="mb-8">
          <Card.Header>
            <h3 className="text-2xl font-semibold text-white text-center">Coming Soon</h3>
          </Card.Header>
          <Card.Content>
            <div className="text-center">
              <div className="w-24 h-24 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <PlayIcon className="w-12 h-12 text-white" />
              </div>
              <p className="text-gray-400 mb-6 max-w-2xl mx-auto">
                Our interactive demo is currently in development. It will showcase real-time agent collaboration, 
                code generation workflows, and the full power of our MCP Agent Network.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/register">
                  <Button variant="secondary">
                    Get Early Access
                  </Button>
                </Link>
                <Link href="/contact">
                  <Button variant="outline">
                    Request Demo Call
                  </Button>
                </Link>
              </div>
            </div>
          </Card.Content>
        </Card>

        {/* Demo Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <Card.Header>
              <h4 className="text-lg font-semibold text-white">Real-time Collaboration</h4>
            </Card.Header>
            <Card.Content>
              <p className="text-gray-400 text-sm">
                Watch multiple AI agents work together on complex coding tasks with live updates and progress tracking.
              </p>
            </Card.Content>
          </Card>

          <Card>
            <Card.Header>
              <h4 className="text-lg font-semibold text-white">Security Validation</h4>
            </Card.Header>
            <Card.Content>
              <p className="text-gray-400 text-sm">
                See automated security reviews, vulnerability scanning, and compliance checks in action.
              </p>
            </Card.Content>
          </Card>

          <Card>
            <Card.Header>
              <h4 className="text-lg font-semibold text-white">Production Ready</h4>
            </Card.Header>
            <Card.Content>
              <p className="text-gray-400 text-sm">
                Experience how our platform generates enterprise-grade code with proper testing and documentation.
              </p>
            </Card.Content>
          </Card>
        </div>
      </div>
    </div>
  )
}