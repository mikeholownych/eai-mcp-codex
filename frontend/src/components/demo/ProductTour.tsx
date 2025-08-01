'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  XMarkIcon, 
  ChevronLeftIcon, 
  ChevronRightIcon,
  PlayIcon,
  CodeBracketIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  CommandLineIcon
} from '@heroicons/react/24/outline'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'

interface TourStep {
  id: string
  title: string
  description: string
  icon: React.ComponentType<{ className?: string }>
  image: string
  features: string[]
  color: string
}

const tourSteps: TourStep[] = [
  {
    id: 'agent-network',
    title: 'AI Agent Network',
    description: 'Watch multiple specialized AI agents collaborate in real-time to solve complex coding challenges.',
    icon: CpuChipIcon,
    image: '/demo/agent-network.png',
    features: [
      'Claude O3 & Sonnet 4 integration',
      'Multi-agent collaboration',
      'Real-time code review',
      'Automated testing'
    ],
    color: 'from-purple-400 to-pink-400'
  },
  {
    id: 'code-generation',
    title: 'Smart Code Generation',
    description: 'Transform ideas into production-ready code with context-aware AI that understands your patterns.',
    icon: CodeBracketIcon,
    image: '/demo/code-generation.png',
    features: [
      'Natural language to code',
      'Pattern recognition',
      'Best practices enforcement',
      'Multi-language support'
    ],
    color: 'from-blue-400 to-cyan-400'
  },
  {
    id: 'security',
    title: 'Enterprise Security',
    description: 'SOC 2 compliant platform with advanced security controls and comprehensive audit logging.',
    icon: ShieldCheckIcon,
    image: '/demo/security.png',
    features: [
      'JWT tenant isolation',
      'Row-level security',
      'Audit logging',
      'RBAC controls'
    ],
    color: 'from-green-400 to-emerald-400'
  },
  {
    id: 'integrations',
    title: 'DevTool Integrations',
    description: 'Seamlessly integrate with your existing workflow through popular development tools.',
    icon: CommandLineIcon,
    image: '/demo/integrations.png',
    features: [
      'GitHub integration',
      'VS Code extension',
      'CI/CD pipelines',
      'Slack notifications'
    ],
    color: 'from-orange-400 to-red-400'
  }
]

interface ProductTourProps {
  isOpen: boolean
  onClose: () => void
}

export default function ProductTour({ isOpen, onClose }: ProductTourProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  const nextStep = () => {
    setCurrentStep((prev) => (prev + 1) % tourSteps.length)
  }

  const prevStep = () => {
    setCurrentStep((prev) => (prev - 1 + tourSteps.length) % tourSteps.length)
  }

  const goToStep = (index: number) => {
    setCurrentStep(index)
  }

  const startDemo = () => {
    setIsPlaying(true)
    // Auto-advance through steps
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        const nextIndex = prev + 1
        if (nextIndex >= tourSteps.length) {
          clearInterval(interval)
          setIsPlaying(false)
          return 0
        }
        return nextIndex
      })
    }, 4000)
  }

  const currentTourStep = tourSteps[currentStep]
  const IconComponent = currentTourStep.icon

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
          onClick={(e) => e.target === e.currentTarget && onClose()}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: "spring", duration: 0.3 }}
            className="max-w-6xl w-full mx-auto"
          >
            <Card className="relative bg-slate-900/95 border-slate-700/50 backdrop-blur-xl overflow-hidden">
              {/* Close Button */}
              <button
                onClick={onClose}
                className="absolute top-4 right-4 z-10 p-2 rounded-full bg-slate-800/50 hover:bg-slate-700/50 transition-colors"
              >
                <XMarkIcon className="w-6 h-6 text-white" />
              </button>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 p-8">
                {/* Content Side */}
                <div className="space-y-6">
                  {/* Header */}
                  <div className="flex items-center space-x-4">
                    <div className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${currentTourStep.color} p-4 shadow-lg`}>
                      <IconComponent className="w-8 h-8 text-white" />
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold text-white mb-2">
                        {currentTourStep.title}
                      </h2>
                      <p className="text-gray-300 text-lg">
                        {currentTourStep.description}
                      </p>
                    </div>
                  </div>

                  {/* Features */}
                  <div className="space-y-3">
                    <h3 className="text-xl font-semibold text-white">Key Features:</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {currentTourStep.features.map((feature, index) => (
                        <motion.div
                          key={feature}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className="flex items-center space-x-3 p-3 rounded-lg bg-slate-800/50"
                        >
                          <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${currentTourStep.color}`} />
                          <span className="text-gray-300">{feature}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>

                  {/* Controls */}
                  <div className="flex items-center justify-between pt-6 border-t border-slate-700">
                    <div className="flex space-x-2">
                      {tourSteps.map((_, index) => (
                        <button
                          key={index}
                          onClick={() => goToStep(index)}
                          className={`w-3 h-3 rounded-full transition-all ${
                            index === currentStep
                              ? 'bg-purple-500 scale-125'
                              : 'bg-slate-600 hover:bg-slate-500'
                          }`}
                        />
                      ))}
                    </div>

                    <div className="flex items-center space-x-4">
                      {!isPlaying && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={startDemo}
                          className="bg-gradient-to-r from-purple-600 to-pink-600"
                        >
                          <PlayIcon className="w-4 h-4 mr-2" />
                          Auto Demo
                        </Button>
                      )}

                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={prevStep}
                          disabled={isPlaying}
                          className="border-slate-600"
                        >
                          <ChevronLeftIcon className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={nextStep}
                          disabled={isPlaying}
                          className="border-slate-600"
                        >
                          <ChevronRightIcon className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Visual Side */}
                <div className="relative">
                  <motion.div
                    key={currentStep}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="relative aspect-video rounded-2xl overflow-hidden bg-slate-800 border border-slate-700"
                  >
                    {/* Placeholder for demo image/video */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center space-y-4">
                        <div className={`w-24 h-24 mx-auto rounded-2xl bg-gradient-to-r ${currentTourStep.color} p-6 shadow-xl`}>
                          <IconComponent className="w-12 h-12 text-white" />
                        </div>
                        <div>
                          <h3 className="text-xl font-semibold text-white mb-2">
                            {currentTourStep.title} Demo
                          </h3>
                          <p className="text-gray-400">
                            Interactive demo would be shown here
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Animated Border */}
                    <div className={`absolute inset-0 rounded-2xl bg-gradient-to-r ${currentTourStep.color} opacity-20 animate-pulse`} />
                  </motion.div>

                  {/* Progress Indicator */}
                  <div className="mt-4 flex justify-center">
                    <div className="text-sm text-gray-400">
                      Step {currentStep + 1} of {tourSteps.length}
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom CTA */}
              <div className="border-t border-slate-700 p-6 bg-slate-800/30">
                <div className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-1">
                      Ready to transform your development workflow?
                    </h3>
                    <p className="text-gray-400">
                      Join thousands of developers using our AI agent network.
                    </p>
                  </div>
                  <div className="flex space-x-4">
                    <Button variant="outline" size="sm" className="border-slate-600">
                      Learn More
                    </Button>
                    <Button 
                      variant="secondary" 
                      size="sm"
                      className="bg-gradient-to-r from-purple-600 to-pink-600"
                    >
                      Start Free Trial
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}