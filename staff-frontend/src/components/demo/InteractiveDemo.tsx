<<<<<<< HEAD
"use client";

import React, { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  PlayIcon,
  PauseIcon,
  CodeBracketIcon,
  SparklesIcon,
  CheckIcon,
} from "@heroicons/react/24/outline";

interface InteractiveDemoProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const InteractiveDemo: React.FC<InteractiveDemoProps> = ({
  isOpen = false,
  onClose,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [code, setCode] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const demoSteps = useMemo(
    () => [
      {
        title: "Describe Your Idea",
        description:
          "Simply describe what you want to build in natural language",
        code: `// Just describe what you want:
"Create a React component with a button that shows a counter and changes color when clicked"`,
      },
      {
        title: "AI Analysis",
        description: "Our agents analyze your requirements and create a plan",
        code: `// AI agents are working together...
🤖 Planner Agent: Breaking down requirements
🔧 Developer Agent: Designing component structure
🎨 UI Agent: Planning responsive design
🔒 Security Agent: Reviewing best practices`,
      },
      {
        title: "Code Generation",
        description: "Production-ready code is generated with best practices",
        code: `import React, { useState } from 'react'
=======
'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PlayIcon, PauseIcon, CodeBracketIcon, SparklesIcon, CheckIcon } from '@heroicons/react/24/outline'

interface InteractiveDemoProps {
  isOpen?: boolean
  onClose?: () => void
}

const InteractiveDemo: React.FC<InteractiveDemoProps> = ({ isOpen = false, onClose }) => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [code, setCode] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)

  const demoSteps = useMemo(() => [
    {
      title: "Describe Your Idea",
      description: "Simply describe what you want to build in natural language",
      code: `// Just describe what you want:
"Create a React component with a button that shows a counter and changes color when clicked"`
    },
    {
      title: "AI Analysis",
      description: "Our agents analyze your requirements and create a plan",
      code: `// AI agents are working together...
🤖 Planner Agent: Breaking down requirements
🔧 Developer Agent: Designing component structure
🎨 UI Agent: Planning responsive design
🔒 Security Agent: Reviewing best practices`
    },
    {
      title: "Code Generation",
      description: "Production-ready code is generated with best practices",
      code: `import React, { useState } from 'react'
>>>>>>> main
import { motion } from 'framer-motion'

interface CounterButtonProps {
  initialCount?: number
}

const CounterButton: React.FC<CounterButtonProps> = ({ 
  initialCount = 0 
}) => {
  const [count, setCount] = useState(initialCount)
  const [colorIndex, setColorIndex] = useState(0)
  
  const colors = [
    'from-purple-500 to-pink-500',
    'from-blue-500 to-cyan-500',
    'from-green-500 to-emerald-500'
  ]
  
  const handleClick = () => {
    setCount(count + 1)
    setColorIndex((colorIndex + 1) % colors.length)
  }
  
  return (
    <motion.button
      onClick={handleClick}
      className={\`px-6 py-3 bg-gradient-to-r \${colors[colorIndex]} 
                 text-white font-semibold rounded-lg 
                 shadow-lg hover:shadow-xl 
                 transform hover:scale-105 transition-all\`}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      Clicked {count} times
    </motion.button>
  )
}

<<<<<<< HEAD
export default CounterButton`,
      },
      {
        title: "Review & Deploy",
        description: "Code is reviewed, tested, and ready for production",
        code: `✅ Code Quality: 95/100
=======
export default CounterButton`
    },
    {
      title: "Review & Deploy",
      description: "Code is reviewed, tested, and ready for production",
      code: `✅ Code Quality: 95/100
>>>>>>> main
✅ Security Scan: Passed
✅ Performance: Optimized
✅ Accessibility: WCAG 2.1 compliant
✅ Tests: Auto-generated
✅ Documentation: Complete

<<<<<<< HEAD
// Ready to deploy! 🚀`,
      },
    ],
    [],
  );

  useEffect(() => {
    if (isOpen && currentStep < demoSteps.length) {
      const timer = setTimeout(
        () => {
          if (currentStep < demoSteps.length - 1) {
            setCurrentStep(currentStep + 1);
          } else {
            setIsPlaying(false);
          }
        },
        isPlaying ? 3000 : 10000,
      );
      return () => clearTimeout(timer);
    }
  }, [isOpen, currentStep, isPlaying, demoSteps.length]);

  useEffect(() => {
    if (isOpen) {
      setCode(demoSteps[0].code);
      setCurrentStep(0);
      setIsPlaying(true);
    }
  }, [isOpen, demoSteps]);

  useEffect(() => {
    if (currentStep < demoSteps.length) {
      setIsGenerating(true);
      const targetCode = demoSteps[currentStep].code;

      // Simulate typing effect
      let i = 0;
      const typeCode = () => {
        if (i <= targetCode.length) {
          setCode(targetCode.substring(0, i));
          i++;
          setTimeout(typeCode, 20);
        } else {
          setIsGenerating(false);
        }
      };

      setCode("");
      typeCode();
    }
  }, [currentStep, demoSteps]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setCurrentStep(0);
    setIsPlaying(true);
  };

  if (!isOpen) return null;
=======
// Ready to deploy! 🚀`
    }
  ], [])

  useEffect(() => {
    if (isOpen && currentStep < demoSteps.length) {
      const timer = setTimeout(() => {
        if (currentStep < demoSteps.length - 1) {
          setCurrentStep(currentStep + 1)
        } else {
          setIsPlaying(false)
        }
      }, isPlaying ? 3000 : 10000)
      return () => clearTimeout(timer)
    }
  }, [isOpen, currentStep, isPlaying, demoSteps.length])

  useEffect(() => {
    if (isOpen) {
      setCode(demoSteps[0].code)
      setCurrentStep(0)
      setIsPlaying(true)
    }
  }, [isOpen, demoSteps])

  useEffect(() => {
    if (currentStep < demoSteps.length) {
      setIsGenerating(true)
      const targetCode = demoSteps[currentStep].code
      
      // Simulate typing effect
      let i = 0
      const typeCode = () => {
        if (i <= targetCode.length) {
          setCode(targetCode.substring(0, i))
          i++
          setTimeout(typeCode, 20)
        } else {
          setIsGenerating(false)
        }
      }
      
      setCode('')
      typeCode()
    }
  }, [currentStep, demoSteps])

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying)
  }

  const handleReset = () => {
    setCurrentStep(0)
    setIsPlaying(true)
  }

  if (!isOpen) return null
>>>>>>> main

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-slate-900 border border-slate-700 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <CodeBracketIcon className="w-6 h-6 text-white" />
                </div>
                <div>
<<<<<<< HEAD
                  <h3 className="text-xl font-bold text-white">
                    Live Code Generation Demo
                  </h3>
                  <p className="text-purple-100">
                    Watch AI agents create code in real-time
                  </p>
=======
                  <h3 className="text-xl font-bold text-white">Live Code Generation Demo</h3>
                  <p className="text-purple-100">Watch AI agents create code in real-time</p>
>>>>>>> main
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={handlePlayPause}
                  className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center hover:bg-white/30 transition-colors"
                >
                  {isPlaying ? (
                    <PauseIcon className="w-5 h-5 text-white" />
                  ) : (
                    <PlayIcon className="w-5 h-5 text-white" />
                  )}
                </button>
                <button
                  onClick={handleReset}
                  className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center hover:bg-white/30 transition-colors"
                >
                  <SparklesIcon className="w-5 h-5 text-white" />
                </button>
                <button
                  onClick={onClose}
                  className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center hover:bg-white/30 transition-colors"
                >
                  ×
                </button>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="bg-slate-800 p-4">
            <div className="flex items-center justify-between mb-2">
<<<<<<< HEAD
              <span className="text-sm text-gray-400">
                Step {currentStep + 1} of {demoSteps.length}
              </span>
              <span className="text-sm text-gray-400">
                {Math.round(((currentStep + 1) / demoSteps.length) * 100)}%
              </span>
=======
              <span className="text-sm text-gray-400">Step {currentStep + 1} of {demoSteps.length}</span>
              <span className="text-sm text-gray-400">{Math.round(((currentStep + 1) / demoSteps.length) * 100)}%</span>
>>>>>>> main
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <motion.div
                className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                initial={{ width: 0 }}
<<<<<<< HEAD
                animate={{
                  width: `${((currentStep + 1) / demoSteps.length) * 100}%`,
                }}
=======
                animate={{ width: `${((currentStep + 1) / demoSteps.length) * 100}%` }}
>>>>>>> main
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>

          {/* Content */}
          <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Panel - Info */}
            <div className="space-y-6">
              <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                <h4 className="text-lg font-semibold text-white mb-2">
                  {demoSteps[currentStep]?.title}
                </h4>
                <p className="text-gray-300">
                  {demoSteps[currentStep]?.description}
                </p>
              </div>

              <div className="space-y-3">
                {demoSteps.map((step, index) => (
                  <motion.div
                    key={index}
                    className={`flex items-center space-x-3 p-3 rounded-lg transition-all ${
<<<<<<< HEAD
                      index === currentStep
                        ? "bg-purple-500/20 border border-purple-500/50"
                        : "bg-slate-800/50"
                    }`}
                    animate={{ scale: index === currentStep ? 1.02 : 1 }}
                  >
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center ${
                        index === currentStep ? "bg-purple-500" : "bg-slate-700"
                      }`}
                    >
=======
                      index === currentStep ? 'bg-purple-500/20 border border-purple-500/50' : 'bg-slate-800/50'
                    }`}
                    animate={{ scale: index === currentStep ? 1.02 : 1 }}
                  >
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      index === currentStep ? 'bg-purple-500' : 'bg-slate-700'
                    }`}>
>>>>>>> main
                      {index < currentStep ? (
                        <CheckIcon className="w-4 h-4 text-white" />
                      ) : (
                        <span className="text-xs text-white">{index + 1}</span>
                      )}
                    </div>
                    <div>
<<<<<<< HEAD
                      <h5 className="text-sm font-medium text-white">
                        {step.title}
                      </h5>
                      <p className="text-xs text-gray-400">
                        {step.description}
                      </p>
=======
                      <h5 className="text-sm font-medium text-white">{step.title}</h5>
                      <p className="text-xs text-gray-400">{step.description}</p>
>>>>>>> main
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Right Panel - Code */}
            <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
              <div className="bg-slate-800 px-4 py-3 border-b border-slate-700 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                </div>
                <div className="text-sm text-gray-400">demo.jsx</div>
              </div>
              <div className="p-4 font-mono text-sm overflow-auto max-h-96">
                <pre className="text-gray-300">
                  <code>{code}</code>
                </pre>
                {isGenerating && (
                  <div className="inline-block w-2 h-4 bg-purple-500 animate-pulse ml-1"></div>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="bg-slate-800 border-t border-slate-700 p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-400">
<<<<<<< HEAD
                {currentStep === demoSteps.length - 1
                  ? "Demo complete! Ready to try it yourself?"
                  : "Auto-playing demo..."}
=======
                {currentStep === demoSteps.length - 1 ? "Demo complete! Ready to try it yourself?" : "Auto-playing demo..."}
>>>>>>> main
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                  disabled={currentStep === 0}
                  className="px-4 py-2 bg-slate-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
<<<<<<< HEAD
                  onClick={() =>
                    setCurrentStep(
                      Math.min(demoSteps.length - 1, currentStep + 1),
                    )
                  }
=======
                  onClick={() => setCurrentStep(Math.min(demoSteps.length - 1, currentStep + 1))}
>>>>>>> main
                  disabled={currentStep === demoSteps.length - 1}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
<<<<<<< HEAD
  );
};

export default InteractiveDemo;
=======
  )
}

export default InteractiveDemo
>>>>>>> main
