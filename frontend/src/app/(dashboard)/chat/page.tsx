'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import {
  PaperAirplaneIcon,
  SparklesIcon,
  UserCircleIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  LightBulbIcon,
  ClipboardDocumentIcon,
  TrashIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  type?: 'text' | 'code' | 'suggestion'
}

const suggestionPrompts = [
  'Explain how React hooks work',
  'Write a Python function to sort an array',
  'Help me debug this JavaScript code',
  'Create a REST API endpoint in Node.js',
  'Optimize this SQL query for performance',
  'Design a database schema for an e-commerce app',
]

const modelOptions = [
  { value: 'claude-3.7-sonnet', label: 'Claude 3.7 Sonnet (Recommended)' },
  { value: 'claude-o3', label: 'Claude O3 (Advanced)' },
  { value: 'claude-sonnet-4', label: 'Claude Sonnet 4 (Latest)' },
]

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [selectedModel, setSelectedModel] = useState('claude-3.7-sonnet')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { user } = useAuth()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (content?: string) => {
    const messageContent = content || inputMessage.trim()
    if (!messageContent) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageContent,
      timestamp: new Date(),
      type: 'text',
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateAIResponse(messageContent),
        timestamp: new Date(),
        type: messageContent.toLowerCase().includes('code') ? 'code' : 'text',
      }
      
      setMessages(prev => [...prev, aiMessage])
      setIsTyping(false)
    }, 2000)
  }

  const generateAIResponse = (prompt: string): string => {
    if (prompt.toLowerCase().includes('react')) {
      return `Great question about React! Here's a comprehensive explanation:

React hooks are functions that let you use state and other React features in functional components. They were introduced in React 16.8 as a way to write components without classes.

Key points about hooks:
1. **useState**: Manages local state in functional components
2. **useEffect**: Handles side effects like API calls, subscriptions
3. **useContext**: Consumes context values
4. **Custom hooks**: Reusable stateful logic

Example:
\`\`\`javascript
import React, { useState, useEffect } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser(userId)
      .then(setUser)
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  return <div>Welcome {user?.name}!</div>;
}
\`\`\`

Would you like me to explain any specific hook in more detail?`
    }

    if (prompt.toLowerCase().includes('python')) {
      return `Here's a Python function to sort an array using different algorithms:

\`\`\`python
def quicksort(arr):
    """
    Efficient divide-and-conquer sorting algorithm
    Time Complexity: O(n log n) average, O(n²) worst case
    """
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)

# Alternative: Using built-in sorted() function
def sort_array_builtin(arr):
    return sorted(arr)

# Example usage
numbers = [64, 34, 25, 12, 22, 11, 90]
print("Original:", numbers)
print("Sorted (quicksort):", quicksort(numbers))
print("Sorted (built-in):", sort_array_builtin(numbers))
\`\`\`

The quicksort algorithm is generally efficient for most datasets. Would you like me to explain other sorting algorithms or help with a specific use case?`
    }

    return `I understand you're asking about "${prompt}". I'm here to help with coding questions, debugging, architecture decisions, and technical explanations.

Here are some ways I can assist:
• **Code Generation**: Write functions, classes, and complete applications
• **Debugging**: Help identify and fix issues in your code  
• **Code Review**: Analyze your code for improvements and best practices
• **Architecture**: Design system architectures and database schemas
• **Learning**: Explain concepts, frameworks, and technologies

Feel free to share your code or ask specific technical questions!`
  }

  const handleClearChat = () => {
    setMessages([])
  }

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content)
    // You could add a toast notification here
  }

  const formatMessageContent = (content: string) => {
    // Simple code block detection and formatting
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g
    const parts = content.split(codeBlockRegex)
    
    return parts.map((part, index) => {
      if (index % 3 === 2) {
        // This is code content
        return (
          <div key={index} className="my-4">
            <div className="bg-slate-800 rounded-lg p-4 overflow-x-auto">
              <pre className="text-sm text-gray-300">
                <code>{part}</code>
              </pre>
            </div>
          </div>
        )
      } else if (index % 3 === 1) {
        // This is the language identifier, skip it
        return null
      } else {
        // This is regular text
        return (
          <div key={index} className="whitespace-pre-wrap">
            {part}
          </div>
        )
      }
    })
  }

  return (
    <div className="h-full flex flex-col space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Assistant</h1>
          <p className="text-gray-400">Get instant help with coding, debugging, and technical questions</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="bg-slate-700 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            {modelOptions.map((model) => (
              <option key={model.value} value={model.value}>
                {model.label}
              </option>
            ))}
          </select>
          
          <Button variant="outline" size="sm" onClick={handleClearChat}>
            <TrashIcon className="h-4 w-4 mr-2" />
            Clear Chat
          </Button>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex-1 flex flex-col min-h-0">
        <Card className="flex-1 flex flex-col p-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <SparklesIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">
                  Start a conversation with AI
                </h3>
                <p className="text-gray-400 mb-6">
                  Ask questions, get code help, or explore technical concepts
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  {suggestionPrompts.map((prompt, index) => (
                    <button
                      key={index}
                      onClick={() => handleSendMessage(prompt)}
                      className="p-3 text-sm text-left bg-slate-700/50 hover:bg-slate-700 rounded-lg border border-slate-600 hover:border-slate-500 transition-colors"
                    >
                      <div className="flex items-start">
                        <LightBulbIcon className="h-4 w-4 text-orange-400 mt-0.5 mr-2 flex-shrink-0" />
                        <span className="text-gray-300">{prompt}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex max-w-4xl ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                      {message.role === 'user' ? (
                        <UserCircleIcon className="h-8 w-8 text-gray-400" />
                      ) : (
                        <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-orange-600 rounded-full flex items-center justify-center">
                          <SparklesIcon className="h-4 w-4 text-white" />
                        </div>
                      )}
                    </div>
                    
                    {/* Message Content */}
                    <div className={`mx-3 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm font-medium text-gray-300">
                          {message.role === 'user' ? user?.name || 'You' : 'AI Assistant'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      
                      <div
                        className={`p-4 rounded-lg ${
                          message.role === 'user'
                            ? 'bg-orange-500/10 border border-orange-500/20 text-white'
                            : 'bg-slate-700/50 border border-slate-600 text-gray-200'
                        }`}
                      >
                        <div className="text-sm">
                          {formatMessageContent(message.content)}
                        </div>
                        
                        {message.role === 'assistant' && (
                          <div className="flex items-center justify-end mt-3 pt-3 border-t border-slate-600 space-x-2">
                            <button
                              onClick={() => handleCopyMessage(message.content)}
                              className="p-1 text-gray-400 hover:text-white transition-colors"
                              title="Copy message"
                            >
                              <ClipboardDocumentIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleSendMessage(`Explain this in more detail: ${message.content.substring(0, 50)}...`)}
                              className="p-1 text-gray-400 hover:text-white transition-colors"
                              title="Ask for more details"
                            >
                              <ArrowPathIcon className="h-4 w-4" />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex">
                  <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-orange-600 rounded-full flex items-center justify-center">
                    <SparklesIcon className="h-4 w-4 text-white" />
                  </div>
                  <div className="mx-3">
                    <div className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input Area */}
          <div className="border-t border-slate-600 p-4">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
                    }
                  }}
                  placeholder="Ask me anything about code, debugging, or technical concepts..."
                  className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 resize-none max-h-32"
                  rows={3}
                />
              </div>
              
              <Button
                variant="primary"
                onClick={() => handleSendMessage()}
                disabled={!inputMessage.trim() || isTyping}
                className="px-4 py-3"
              >
                <PaperAirplaneIcon className="h-5 w-5" />
              </Button>
            </div>
            
            <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
              <span>Press Enter to send, Shift+Enter for new line</span>
              <span>Model: {modelOptions.find(m => m.value === selectedModel)?.label}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}