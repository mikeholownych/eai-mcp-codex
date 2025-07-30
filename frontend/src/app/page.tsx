'use client'

import React from 'react'
import Link from 'next/link'
import { 
  CodeBracketIcon, 
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  PlayIcon,
  CheckIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'

const features = [
  {
    icon: CodeBracketIcon,
    title: 'AI Code Generation',
    description: 'Generate high-quality code with advanced AI models including Claude O3, Sonnet 4, and specialized coding models.',
  },
  {
    icon: ChatBubbleLeftRightIcon,
    title: 'Intelligent Assistant',
    description: 'AI-powered chatbot trained on all Ethical AI Insider content with RAG architecture for contextual responses.',
  },
  {
    icon: UserGroupIcon,
    title: 'Real-time Collaboration',
    description: 'Multi-agent collaboration with staff-led escalations and seamless team workflows.',
  },
  {
    icon: ShieldCheckIcon,
    title: 'Enterprise Security',
    description: 'SOC 2 ready with JWT tenant isolation, row-level security, and comprehensive audit logging.',
  },
  {
    icon: ChartBarIcon,
    title: 'Advanced Analytics',
    description: 'Detailed insights, usage metrics, and performance analytics with custom dashboards.',
  },
  {
    icon: PlayIcon,
    title: 'Video Library',
    description: 'Comprehensive video tutorials and walkthroughs with plan-based access control.',
  },
]

const pricingPlans = [
  {
    name: 'Standard',
    price: '$29',
    period: 'per month',
    description: 'Perfect for individual developers and small teams',
    features: [
      'Code generation with basic models',
      'AI assistant with standard knowledge base',
      'Basic video library access',
      'Email support',
      '10,000 API calls/month',
      '5GB storage',
    ],
    highlighted: false,
  },
  {
    name: 'Pro',
    price: '$79',
    period: 'per month',
    description: 'Advanced features for growing businesses',
    features: [
      'All Standard features',
      'Advanced AI models (Claude O3, Sonnet 4)',
      'Real-time collaboration',
      'Priority support',
      '50,000 API calls/month',
      '25GB storage',
      'Custom integrations',
    ],
    highlighted: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: 'contact us',
    description: 'Complete solution for large organizations',
    features: [
      'All Pro features',
      'Unlimited API calls',
      'Unlimited storage',
      'Dedicated support team',
      'Custom deployment options',
      'Advanced security features',
      'SLA guarantees',
    ],
    highlighted: false,
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-dark-900">
      {/* Navigation */}
      <nav className="border-b border-dark-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <span className="text-xl font-bold text-white">Ethical AI Insider</span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <Link href="#features" className="text-gray-300 hover:text-white transition-colors">
                Features
              </Link>
              <Link href="#pricing" className="text-gray-300 hover:text-white transition-colors">
                Pricing
              </Link>
              <Link href="/docs" className="text-gray-300 hover:text-white transition-colors">
                Docs
              </Link>
              <Link href="/blog" className="text-gray-300 hover:text-white transition-colors">
                Blog
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/login">
                <Button variant="ghost" size="sm">
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="primary" size="sm">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
            The Future of{' '}
            <span className="bg-gradient-primary bg-clip-text text-transparent">
              Ethical AI
            </span>{' '}
            Development
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Secure, multi-tenant platform for code generation via agentic AI with real-time collaboration, 
            comprehensive video library, and enterprise-grade security features.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/register">
              <Button size="lg" className="w-full sm:w-auto">
                Start Free Trial
                <ArrowRightIcon className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Link href="/demo">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                Watch Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Powerful Features for Modern Development
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Everything you need to build, collaborate, and scale with AI-powered development tools.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} hover className="h-full">
                <Card.Header>
                  <div className="w-12 h-12 bg-gradient-primary rounded-xl flex items-center justify-center mb-4">
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                </Card.Header>
                <Card.Content>
                  <p className="text-gray-300">{feature.description}</p>
                </Card.Content>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Choose Your Plan
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Flexible pricing for teams of all sizes. Start free and upgrade as you grow.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {pricingPlans.map((plan, index) => (
              <Card 
                key={index} 
                className={`h-full ${plan.highlighted ? 'ring-2 ring-primary-500 shadow-glow' : ''}`}
              >
                <Card.Header>
                  <div className="text-center">
                    <h3 className="text-2xl font-semibold text-white mb-2">{plan.name}</h3>
                    <div className="mb-4">
                      <span className="text-4xl font-bold text-white">{plan.price}</span>
                      {plan.price !== 'Custom' && (
                        <span className="text-gray-400 ml-2">{plan.period}</span>
                      )}
                    </div>
                    <p className="text-gray-300">{plan.description}</p>
                  </div>
                </Card.Header>
                
                <Card.Content>
                  <ul className="space-y-3">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-center">
                        <CheckIcon className="w-5 h-5 text-primary-400 mr-3 flex-shrink-0" />
                        <span className="text-gray-300">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </Card.Content>
                
                <Card.Footer>
                  <Button 
                    variant={plan.highlighted ? 'primary' : 'outline'} 
                    size="lg" 
                    className="w-full"
                  >
                    {plan.price === 'Custom' ? 'Contact Sales' : 'Get Started'}
                  </Button>
                </Card.Footer>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <Card className="bg-gradient-primary text-white">
            <Card.Content>
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to Transform Your Development Process?
              </h2>
              <p className="text-xl mb-8 opacity-90">
                Join thousands of developers who trust Ethical AI Insider for their AI-powered development needs.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/register">
                  <Button variant="secondary" size="lg" className="w-full sm:w-auto">
                    Start Free Trial
                  </Button>
                </Link>
                <Link href="/contact">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto border-white text-white hover:bg-white hover:text-primary-600">
                    Contact Sales
                  </Button>
                </Link>
              </div>
            </Card.Content>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-dark-700 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">AI</span>
                </div>
                <span className="text-xl font-bold text-white">Ethical AI Insider</span>
              </div>
              <p className="text-gray-400">
                Building the future of ethical AI development with secure, collaborative tools.
              </p>
            </div>
            
            <div>
              <h3 className="text-white font-semibold mb-4">Product</h3>
              <ul className="space-y-2">
                <li><Link href="/features" className="text-gray-400 hover:text-white transition-colors">Features</Link></li>
                <li><Link href="/pricing" className="text-gray-400 hover:text-white transition-colors">Pricing</Link></li>
                <li><Link href="/docs" className="text-gray-400 hover:text-white transition-colors">Documentation</Link></li>
                <li><Link href="/api" className="text-gray-400 hover:text-white transition-colors">API</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-white font-semibold mb-4">Company</h3>
              <ul className="space-y-2">
                <li><Link href="/about" className="text-gray-400 hover:text-white transition-colors">About</Link></li>
                <li><Link href="/blog" className="text-gray-400 hover:text-white transition-colors">Blog</Link></li>
                <li><Link href="/careers" className="text-gray-400 hover:text-white transition-colors">Careers</Link></li>
                <li><Link href="/contact" className="text-gray-400 hover:text-white transition-colors">Contact</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-white font-semibold mb-4">Support</h3>
              <ul className="space-y-2">
                <li><Link href="/help" className="text-gray-400 hover:text-white transition-colors">Help Center</Link></li>
                <li><Link href="/community" className="text-gray-400 hover:text-white transition-colors">Community</Link></li>
                <li><Link href="/status" className="text-gray-400 hover:text-white transition-colors">Status</Link></li>
                <li><Link href="/security" className="text-gray-400 hover:text-white transition-colors">Security</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="mt-12 pt-8 border-t border-dark-700 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400">
              © 2024 Ethical AI Insider. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <Link href="/privacy" className="text-gray-400 hover:text-white transition-colors">Privacy</Link>
              <Link href="/terms" className="text-gray-400 hover:text-white transition-colors">Terms</Link>
              <Link href="/cookies" className="text-gray-400 hover:text-white transition-colors">Cookies</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}