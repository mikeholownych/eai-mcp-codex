'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import { 
  CheckIcon,
  ArrowRightIcon,
  SparklesIcon,
  CodeBracketIcon,
  ShieldCheckIcon,
  CpuChipIcon,
  CommandLineIcon,
  StarIcon,
  PlayIcon
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import ProductTour from '@/components/demo/ProductTour'
import ParticleBackground from '@/components/effects/ParticleBackground'
import EnhancedFeatures from '@/components/effects/ScrollAnimation'
import InteractiveDemo from '@/components/demo/InteractiveDemo'
import StructuredData, { 
  organizationSchema, 
  softwareApplicationSchema, 
  serviceSchema, 
  faqSchema 
} from '@/components/seo/StructuredData'

const features = [
  {
    icon: CpuChipIcon,
    title: 'Agent Network',
    description: 'Multi-agent AI collaboration with Claude O3, Sonnet 4, and specialized coding agents working together to solve complex problems.',
    gradient: 'from-purple-400 to-pink-400',
  },
  {
    icon: CodeBracketIcon,
    title: 'Code Generation',
    description: 'Transform ideas into production-ready code with intelligent AI models that understand context, patterns, and best practices.',
    gradient: 'from-blue-400 to-cyan-400',
  },
  {
    icon: ShieldCheckIcon,
    title: 'Compliance & Security',
    description: 'SOC 2 ready platform with JWT tenant isolation, comprehensive audit logging, and enterprise-grade security controls.',
    gradient: 'from-green-400 to-emerald-400',
  },
  {
    icon: CommandLineIcon,
    title: 'DevTool Integrations',
    description: 'Seamless integration with GitHub, VS Code, and popular development tools for streamlined workflows.',
    gradient: 'from-orange-400 to-red-400',
  },
  {
    icon: SparklesIcon,
    title: 'Intelligent Assistant',
    description: 'AI-powered chatbot trained on all Ethical AI Insider content with RAG architecture for contextual responses.',
    gradient: 'from-violet-400 to-purple-400',
  },
  {
    icon: StarIcon,
    title: 'Premium Support',
    description: 'Access to comprehensive video library, expert support, and collaborative workflows with staff escalations.',
    gradient: 'from-yellow-400 to-orange-400',
  },
]

const testimonials = [
  {
    name: 'Sarah Chen',
    role: 'Lead Developer at TechCorp',
    content: 'The agent network saved us 40+ hours per week. Code quality improved dramatically.',
    avatar: '/api/placeholder/48/48',
    rating: 5,
  },
  {
    name: 'Marcus Rodriguez',
    role: 'CTO at StartupXYZ',
    content: 'Best investment we made. The security compliance features are enterprise-grade.',
    avatar: '/api/placeholder/48/48',
    rating: 5,
  },
  {
    name: 'Emily Watson',
    role: 'Full Stack Engineer',
    content: 'Game-changer for solo developers. Like having a senior team at your fingertips.',
    avatar: '/api/placeholder/48/48',
    rating: 5,
  },
]

const stats = [
  { label: 'Lines of Code Generated', value: '2.5M+', suffix: '' },
  { label: 'Developer Hours Saved', value: '15K+', suffix: '' },
  { label: 'Uptime SLA', value: '99.9', suffix: '%' },
  { label: 'Security Score', value: 'A+', suffix: '' },
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

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      delayChildren: 0.3,
      staggerChildren: 0.2
    }
  }
}

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.5
    }
  }
}

const AnimatedCounter = ({ value, suffix = '', duration = 2000 }) => {
  const [count, setCount] = useState(0)
  const ref = React.useRef(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (inView) {
      const startTime = Date.now()
      const startValue = 0
      const numericValue = parseFloat(value.replace(/[^\d.]/g, ''))
      
      const updateCount = () => {
        const now = Date.now()
        const progress = Math.min((now - startTime) / duration, 1)
        const currentValue = startValue + (numericValue - startValue) * progress
        
        setCount(currentValue)
        
        if (progress < 1) {
          requestAnimationFrame(updateCount)
        }
      }
      
      requestAnimationFrame(updateCount)
    }
  }, [inView, value, duration])

  const formatValue = (val) => {
    if (value.includes('M+')) return `${Math.floor(val / 100000) / 10}M+`
    if (value.includes('K+')) return `${Math.floor(val / 100) / 10}K+`
    if (value.includes('%')) return val.toFixed(1)
    if (value === 'A+') return inView ? 'A+' : 'F'
    return Math.floor(val).toString()
  }

  return (
    <div ref={ref} className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
      {formatValue(count)}{suffix}
    </div>
  )
}

export default function HomePage() {
  const [showTour, setShowTour] = useState(false)
  const [showDemo, setShowDemo] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900">
      {/* 3D Particle Background */}
      <ParticleBackground />
      
      {/* Background Effects */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-900/20 via-slate-900 to-slate-900" style={{ zIndex: 2 }} />
      <div className="fixed inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]" style={{ zIndex: 3 }} />
      
      {/* Navigation */}
      <motion.nav 
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="relative border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-xl"
        style={{ zIndex: 10 }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <motion.div 
              className="flex items-center space-x-2"
              whileHover={{ scale: 1.05 }}
              transition={{ type: "spring", stiffness: 400, damping: 10 }}
            >
              <div className="w-8 h-8 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg flex items-center justify-center shadow-lg shadow-purple-500/25">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <span className="text-xl font-bold text-white">Ethical AI Insider</span>
            </motion.div>
            
            <div className="hidden md:flex items-center space-x-8">
              {['Features', 'Pricing', 'Docs', 'Blog'].map((item) => (
                <motion.div key={item} whileHover={{ y: -2 }} transition={{ type: "spring", stiffness: 300 }}>
                  <Link href={`#${item.toLowerCase()}`} className="text-gray-300 hover:text-white transition-colors relative group">
                    {item}
                    <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-purple-400 to-pink-400 transition-all group-hover:w-full"></span>
                  </Link>
                </motion.div>
              ))}
            </div>
            
            <div className="flex items-center space-x-4">
              <Link href="/login">
                <Button variant="ghost" size="sm" className="hover:bg-slate-800/50">
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button variant="secondary" size="sm" className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg shadow-purple-500/25">
                    Get Started
                  </Button>
                </motion.div>
              </Link>
            </div>
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="relative py-32 px-4 sm:px-6 lg:px-8 overflow-hidden" style={{ zIndex: 5 }}>
        <motion.div 
          className="max-w-7xl mx-auto text-center"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Floating Particles */}
          <div className="absolute inset-0 overflow-hidden">
            {[...Array(20)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-2 h-2 bg-purple-400/20 rounded-full"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                }}
                animate={{
                  y: [0, -30, 0],
                  opacity: [0.2, 0.8, 0.2],
                }}
                transition={{
                  duration: 3 + Math.random() * 2,
                  repeat: Infinity,
                  delay: Math.random() * 2,
                }}
              />
            ))}
          </div>

          <motion.div variants={itemVariants} className="mb-8">
            <motion.h1 
              className="text-6xl md:text-8xl font-extrabold text-white mb-6 leading-tight tracking-tight"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            >
              Transform Ideas Into{' '}
              <motion.span 
                className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-purple-600"
                animate={{
                  backgroundPosition: ['0% 50%', '100% 50%', '0% 50%']
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "linear"
                }}
                style={{
                  backgroundSize: '200% 200%'
                }}
              >
                Production Code
              </motion.span>
            </motion.h1>
          </motion.div>

          <motion.p 
            variants={itemVariants}
            className="text-xl md:text-2xl text-gray-300 mb-12 max-w-4xl mx-auto leading-relaxed"
          >
            The most advanced AI agent network for developers. Generate production-ready code with 
            multi-agent collaboration, enterprise security, and seamless DevTool integrations.
          </motion.p>

          <motion.div 
            variants={itemVariants}
            className="flex flex-col sm:flex-row gap-6 justify-center mb-20"
          >
            <Link href="/register">
              <motion.div
                whileHover={{ scale: 1.05, boxShadow: '0 20px 40px rgba(168, 85, 247, 0.4)' }}
                whileTap={{ scale: 0.95 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <Button 
                  variant="secondary" 
                  size="lg" 
                  className="w-full sm:w-auto bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold px-8 py-4 text-lg shadow-2xl shadow-purple-500/25 border-0"
                >
                  Start Free Trial
                  <ArrowRightIcon className="ml-2 w-5 h-5" />
                </Button>
              </motion.div>
            </Link>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button 
                variant="outline" 
                size="lg" 
                className="w-full sm:w-auto border-slate-600 text-slate-300 hover:bg-slate-800/50 hover:border-slate-500 px-8 py-4 text-lg backdrop-blur-sm"
                onClick={() => setShowDemo(true)}
              >
                <PlayIcon className="w-5 h-5 mr-2" />
                Live Demo
              </Button>
            </motion.div>
          </motion.div>

          {/* Animated Stats */}
          <motion.div 
            variants={itemVariants}
            className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto"
          >
            {stats.map((stat, index) => (
              <motion.div 
                key={index}
                className="text-center"
                whileHover={{ scale: 1.05 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                <div className="text-gray-400 mt-2 text-sm md:text-base">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>

          {/* Social Proof */}
          <motion.div 
            variants={itemVariants}
            className="mt-16 flex flex-col items-center"
          >
            <div className="flex items-center space-x-1 mb-4">
              {[...Array(5)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.1 * i, type: "spring", stiffness: 300 }}
                >
                  <StarIcon className="w-6 h-6 text-yellow-400 fill-current" />
                </motion.div>
              ))}
            </div>
            <p className="text-gray-400">Trusted by 10,000+ developers worldwide</p>
          </motion.div>
        </motion.div>
      </section>

      {/* Enhanced Features Section */}
      <EnhancedFeatures />
      
      {/* Features Section */}
      <section id="features" className="relative py-24 px-4 sm:px-6 lg:px-8" style={{ zIndex: 5 }}>
        <div className="max-w-7xl mx-auto">
          <motion.div 
            className="text-center mb-20"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <motion.h2 
              className="text-4xl md:text-5xl font-bold text-white mb-6"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              viewport={{ once: true }}
            >
              Powerful Features for Modern Development
            </motion.h2>
            <motion.p 
              className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
            >
              Everything you need to build, collaborate, and scale with the most advanced AI-powered development platform.
            </motion.p>
          </motion.div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const IconComponent = feature.icon
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  whileHover={{ 
                    y: -8,
                    transition: { type: "spring", stiffness: 300, damping: 20 }
                  }}
                >
                  <Card hover className="h-full bg-slate-800/50 border-slate-700/50 backdrop-blur-sm overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-10 transition-opacity duration-500" 
                         style={{ background: `linear-gradient(135deg, var(--tw-gradient-stops))` }} />
                    <Card.Header className="relative">
                      <div className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${feature.gradient} p-4 mb-6 shadow-lg`}>
                        <IconComponent className="w-8 h-8 text-white" />
                      </div>
                      <h3 className="text-2xl font-semibold text-white mb-3 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-purple-400 group-hover:to-pink-400 transition-all duration-300">
                        {feature.title}
                      </h3>
                    </Card.Header>
                    <Card.Content className="relative">
                      <p className="text-gray-300 leading-relaxed text-lg">{feature.description}</p>
                    </Card.Content>
                  </Card>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-800/30" style={{ zIndex: 5 }}>
        <div className="max-w-7xl mx-auto">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Loved by Developers Worldwide
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Join thousands of developers who have transformed their workflow with our AI agent network.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ y: -4 }}
              >
                <Card className="h-full bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                  <Card.Content className="p-8">
                    <div className="flex items-center mb-4">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <StarIcon key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                      ))}
                    </div>
                    <p className="text-gray-300 mb-6 text-lg leading-relaxed italic">
                      &quot;{testimonial.content}&quot;
                    </p>
                    <div className="flex items-center">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-400 to-pink-400 flex items-center justify-center text-white font-semibold mr-4">
                        {testimonial.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div>
                        <div className="font-semibold text-white">{testimonial.name}</div>
                        <div className="text-gray-400 text-sm">{testimonial.role}</div>
                      </div>
                    </div>
                  </Card.Content>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8" style={{ zIndex: 5 }}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Choose Your Plan
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Flexible pricing for teams of all sizes. Start free and upgrade as you grow.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {pricingPlans.map((plan, index) => (
              <Card 
                key={index} 
                className={`h-full ${plan.highlighted ? 'ring-2 ring-purple-500' : ''}`}
              >
                <Card.Header>
                  <div className="text-center">
                    <h3 className="text-2xl font-semibold text-white mb-2">{plan.name}</h3>
                    <div className="mb-4">
                      <span className="text-4xl font-bold text-white">{plan.price}</span>
                      {plan.price !== 'Custom' && (
                        <span className="text-gray-500 ml-2">{plan.period}</span>
                      )}
                    </div>
                    <p className="text-gray-400">{plan.description}</p>
                  </div>
                </Card.Header>
                
                <Card.Content>
                  <ul className="space-y-3">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-center">
                        <CheckIcon className="w-5 h-5 text-primary-400 mr-3 flex-shrink-0" />
                        <span className="text-gray-400">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </Card.Content>
                
                <Card.Footer>
                  <Button 
                    variant={plan.highlighted ? 'secondary' : 'outline'} 
                    size="lg" 
                    className={`w-full ${!plan.highlighted ? 'border-gray-600 text-gray-300 hover:bg-gray-800' : ''}`}
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
      <section className="py-20 px-4 sm:px-6 lg:px-8" style={{ zIndex: 5 }}>
        <div className="max-w-4xl mx-auto text-center">
          <Card className="bg-slate-800 border-slate-700">
            <Card.Content className="py-16">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                Ready to Transform Your Development Process?
              </h2>
              <p className="text-xl mb-8 text-gray-400 max-w-2xl mx-auto">
                Join thousands of developers who trust Ethical AI Insider for their AI-powered development needs.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/register">
                  <Button 
                    variant="secondary" 
                    size="lg" 
                    className="w-full sm:w-auto"
                  >
                    Start Free Trial
                  </Button>
                </Link>
                <Link href="/contact">
                  <Button 
                    variant="outline" 
                    size="lg" 
                    className="w-full sm:w-auto border-gray-600 text-gray-300 hover:bg-gray-700"
                  >
                    Contact Sales
                  </Button>
                </Link>
              </div>
            </Card.Content>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-700 bg-slate-800 py-12 px-4 sm:px-6 lg:px-8" style={{ zIndex: 5 }}>
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">AI</span>
                </div>
                <span className="text-xl font-bold text-white">Ethical AI Insider</span>
              </div>
              <p className="text-gray-500">
                Building the future of ethical AI development with secure, collaborative tools.
              </p>
            </div>
            
            <div>
              <h3 className="text-white font-semibold mb-4">Product</h3>
              <ul className="space-y-2">
                <li><Link href="/features" className="text-gray-500 hover:text-white transition-colors">Features</Link></li>
                <li><Link href="/pricing" className="text-gray-500 hover:text-white transition-colors">Pricing</Link></li>
                <li><Link href="/docs" className="text-gray-500 hover:text-white transition-colors">Documentation</Link></li>
                <li><Link href="/api" className="text-gray-500 hover:text-white transition-colors">API</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-white font-semibold mb-4">Company</h3>
              <ul className="space-y-2">
                <li><Link href="/about" className="text-gray-500 hover:text-white transition-colors">About</Link></li>
                <li><Link href="/blog" className="text-gray-500 hover:text-white transition-colors">Blog</Link></li>
                <li><Link href="/careers" className="text-gray-500 hover:text-white transition-colors">Careers</Link></li>
                <li><Link href="/contact" className="text-gray-500 hover:text-white transition-colors">Contact</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-white font-semibold mb-4">Support</h3>
              <ul className="space-y-2">
                <li><Link href="/help" className="text-gray-500 hover:text-white transition-colors">Help Center</Link></li>
                <li><Link href="/community" className="text-gray-500 hover:text-white transition-colors">Community</Link></li>
                <li><Link href="/status" className="text-gray-500 hover:text-white transition-colors">Status</Link></li>
                <li><Link href="/security" className="text-gray-500 hover:text-white transition-colors">Security</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="mt-12 pt-8 border-t border-slate-700 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-500">
              © 2024 Ethical AI Insider. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <Link href="/privacy" className="text-gray-500 hover:text-white transition-colors">Privacy</Link>
              <Link href="/terms" className="text-gray-500 hover:text-white transition-colors">Terms</Link>
              <Link href="/cookies" className="text-gray-500 hover:text-white transition-colors">Cookies</Link>
            </div>
          </div>
        </div>
      </footer>

      {/* Interactive Demo */}
      <InteractiveDemo 
        isOpen={showDemo} 
        onClose={() => setShowDemo(false)} 
      />
      
      {/* Product Tour */}
      <ProductTour 
        isOpen={showTour} 
        onClose={() => setShowTour(false)} 
      />

      {/* Structured Data for SEO */}
      <StructuredData data={organizationSchema} />
      <StructuredData data={softwareApplicationSchema} />
      <StructuredData data={serviceSchema} />
      <StructuredData data={faqSchema} />
    </div>
  )
}