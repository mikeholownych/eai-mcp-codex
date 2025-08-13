<<<<<<< HEAD
"use client";

import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import { modelApi } from "@/lib/api";
=======
'use client'

import React, { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { modelApi } from '@/lib/api'
>>>>>>> main
import {
  PaperAirplaneIcon,
  SparklesIcon,
  UserCircleIcon,
  LightBulbIcon,
  ClipboardDocumentIcon,
  TrashIcon,
  ArrowPathIcon,
<<<<<<< HEAD
} from "@heroicons/react/24/outline";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  type?: "text" | "code" | "suggestion";
}

const suggestionPrompts = [
  "Explain how React hooks work",
  "Write a Python function to sort an array",
  "Help me debug this JavaScript code",
  "Create a REST API endpoint in Node.js",
  "Optimize this SQL query for performance",
  "Design a database schema for an e-commerce app",
];

// Default model options as fallback
const defaultModelOptions = [
  { value: "claude-3.7-sonnet", label: "Claude 3.7 Sonnet (Recommended)" },
  { value: "claude-o3", label: "Claude O3 (Advanced)" },
  { value: "claude-sonnet-4", label: "Claude Sonnet 4 (Latest)" },
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [selectedModel, setSelectedModel] = useState("claude-3.7-sonnet");
  const [modelOptions, setModelOptions] = useState(defaultModelOptions);
  const [connectionStatus, setConnectionStatus] = useState<
    "unknown" | "connected" | "disconnected"
  >("unknown");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);
=======
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

// Default model options as fallback
const defaultModelOptions = [
  { value: 'claude-3.7-sonnet', label: 'Claude 3.7 Sonnet (Recommended)' },
  { value: 'claude-o3', label: 'Claude O3 (Advanced)' },
  { value: 'claude-sonnet-4', label: 'Claude Sonnet 4 (Latest)' },
]

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [selectedModel, setSelectedModel] = useState('claude-3.7-sonnet')
  const [modelOptions, setModelOptions] = useState(defaultModelOptions)
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'connected' | 'disconnected'>('unknown')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { user } = useAuth()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])
>>>>>>> main

  // Load available models and test connection on mount
  useEffect(() => {
    const initializeChat = async () => {
      try {
        // Test Claude connection
<<<<<<< HEAD
        const connectionTest = await modelApi.testClaudeConnection();
        setConnectionStatus(
          connectionTest.success && connectionTest.data?.status === "connected"
            ? "connected"
            : "disconnected",
        );

        // Load available models
        const modelsResponse = await modelApi.getAvailableModels();
        if (modelsResponse.success && modelsResponse.data) {
          const dynamicModelOptions = modelsResponse.data.map((model) => {
            return {
              value: model.id,
              label: `${model.name} (${model.description || "General Purpose"})`,
            };
          });

          if (dynamicModelOptions.length > 0) {
            setModelOptions(dynamicModelOptions);
            // Set first available model as default if current selection not available
            if (!dynamicModelOptions.find((m) => m.value === selectedModel)) {
              setSelectedModel(dynamicModelOptions[0].value);
=======
        const connectionTest = await modelApi.testClaudeConnection()
        setConnectionStatus(connectionTest.success && connectionTest.data?.claude_api_connected ? 'connected' : 'disconnected')

        // Load available models
        const modelsResponse = await modelApi.getAvailableModels()
        if (modelsResponse.success && modelsResponse.data) {
          const dynamicModelOptions = Object.keys(modelsResponse.data).map((modelName) => {
            const modelInfo = modelsResponse.data[modelName]
            return {
              value: modelName,
              label: `${modelName} (${modelInfo.use_cases?.join(', ') || 'General Purpose'})`
            }
          })
          
          if (dynamicModelOptions.length > 0) {
            setModelOptions(dynamicModelOptions)
            // Set first available model as default if current selection not available
            if (!dynamicModelOptions.find(m => m.value === selectedModel)) {
              setSelectedModel(dynamicModelOptions[0].value)
>>>>>>> main
            }
          }
        }
      } catch (error) {
<<<<<<< HEAD
        console.error("Failed to initialize chat:", error);
        setConnectionStatus("disconnected");
        // Keep default model options on error
      }
    };

    initializeChat();
  }, [selectedModel]);

  const handleSendMessage = async (content?: string) => {
    const messageContent = content || inputMessage.trim();
    if (!messageContent) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: messageContent,
      timestamp: new Date(),
      type: "text",
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsTyping(true);
=======
        console.error('Failed to initialize chat:', error)
        setConnectionStatus('disconnected')
        // Keep default model options on error
      }
    }

    initializeChat()
  }, [selectedModel])

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
>>>>>>> main

    try {
      // Call real AI model through model-router service
      const response = await modelApi.routeRequest(messageContent, {
        model: selectedModel,
<<<<<<< HEAD
        taskType: messageContent.toLowerCase().includes("code")
          ? "code_generation"
          : "general",
=======
        taskType: messageContent.toLowerCase().includes('code') ? 'code_generation' : 'general',
>>>>>>> main
        temperature: 0.7,
        maxTokens: 4096,
        context: {
          conversation_history: messages.slice(-5), // Send last 5 messages for context
<<<<<<< HEAD
          user_preferences: { model: selectedModel },
        },
      });
=======
          user_preferences: { model: selectedModel }
        }
      })
>>>>>>> main

      if (response.success && response.data) {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
<<<<<<< HEAD
          role: "assistant",
          content:
            response.data.response ||
            "I received your message but couldn't generate a response.",
          timestamp: new Date(),
          type: messageContent.toLowerCase().includes("code") ? "code" : "text",
        };

        setMessages((prev) => [...prev, aiMessage]);
=======
          role: 'assistant',
          content: response.data.result || response.data.content || 'I received your message but couldn\'t generate a response.',
          timestamp: new Date(),
          type: messageContent.toLowerCase().includes('code') ? 'code' : 'text',
        }
        
        setMessages(prev => [...prev, aiMessage])
>>>>>>> main
      } else {
        // Fallback message if API call succeeds but no proper response
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
<<<<<<< HEAD
          role: "assistant",
          content:
            "I apologize, but I encountered an issue generating a response. Please try again.",
          timestamp: new Date(),
          type: "text",
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error("Error calling model API:", error);

      // Fallback to mock response if API fails
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: generateAIResponse(messageContent),
        timestamp: new Date(),
        type: messageContent.toLowerCase().includes("code") ? "code" : "text",
      };

      setMessages((prev) => [...prev, aiMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const generateAIResponse = (prompt: string): string => {
    if (prompt.toLowerCase().includes("react")) {
=======
          role: 'assistant',
          content: 'I apologize, but I encountered an issue generating a response. Please try again.',
          timestamp: new Date(),
          type: 'text',
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      console.error('Error calling model API:', error)
      
      // Fallback to mock response if API fails
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateAIResponse(messageContent),
        timestamp: new Date(),
        type: messageContent.toLowerCase().includes('code') ? 'code' : 'text',
      }
      
      setMessages(prev => [...prev, aiMessage])
    } finally {
      setIsTyping(false)
    }
  }

  const generateAIResponse = (prompt: string): string => {
    if (prompt.toLowerCase().includes('react')) {
>>>>>>> main
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

<<<<<<< HEAD
Would you like me to explain any specific hook in more detail?`;
    }

    if (prompt.toLowerCase().includes("python")) {
=======
Would you like me to explain any specific hook in more detail?`
    }

    if (prompt.toLowerCase().includes('python')) {
>>>>>>> main
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

<<<<<<< HEAD
The quicksort algorithm is generally efficient for most datasets. Would you like me to explain other sorting algorithms or help with a specific use case?`;
=======
The quicksort algorithm is generally efficient for most datasets. Would you like me to explain other sorting algorithms or help with a specific use case?`
>>>>>>> main
    }

    return `I understand you're asking about "${prompt}". I'm here to help with coding questions, debugging, architecture decisions, and technical explanations.

Here are some ways I can assist:
• **Code Generation**: Write functions, classes, and complete applications
• **Debugging**: Help identify and fix issues in your code  
• **Code Review**: Analyze your code for improvements and best practices
• **Architecture**: Design system architectures and database schemas
• **Learning**: Explain concepts, frameworks, and technologies

<<<<<<< HEAD
Feel free to share your code or ask specific technical questions!`;
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    // You could add a toast notification here
  };

  const formatMessageContent = (content: string) => {
    // Simple code block detection and formatting
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts = content.split(codeBlockRegex);

=======
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
    
>>>>>>> main
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
<<<<<<< HEAD
        );
      } else if (index % 3 === 1) {
        // This is the language identifier, skip it
        return null;
=======
        )
      } else if (index % 3 === 1) {
        // This is the language identifier, skip it
        return null
>>>>>>> main
      } else {
        // This is regular text
        return (
          <div key={index} className="whitespace-pre-wrap">
            {part}
          </div>
<<<<<<< HEAD
        );
      }
    });
  };
=======
        )
      }
    })
  }
>>>>>>> main

  return (
    <div className="h-full flex flex-col space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Assistant</h1>
<<<<<<< HEAD
          <p className="text-gray-400">
            Get instant help with coding, debugging, and technical questions
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Connection Status Indicator */}
          <div className="flex items-center space-x-2">
            <div
              className={`w-2 h-2 rounded-full ${
                connectionStatus === "connected"
                  ? "bg-green-500"
                  : connectionStatus === "disconnected"
                    ? "bg-red-500"
                    : "bg-yellow-500"
              }`}
            />
            <span className="text-xs text-gray-400">
              {connectionStatus === "connected"
                ? "AI Connected"
                : connectionStatus === "disconnected"
                  ? "AI Offline"
                  : "Connecting..."}
            </span>
          </div>

=======
          <p className="text-gray-400">Get instant help with coding, debugging, and technical questions</p>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Connection Status Indicator */}
          <div className="flex items-center space-x-2">
            <div 
              className={`w-2 h-2 rounded-full ${
                connectionStatus === 'connected' ? 'bg-green-500' : 
                connectionStatus === 'disconnected' ? 'bg-red-500' : 
                'bg-yellow-500'
              }`}
            />
            <span className="text-xs text-gray-400">
              {connectionStatus === 'connected' ? 'AI Connected' : 
               connectionStatus === 'disconnected' ? 'AI Offline' : 
               'Connecting...'}
            </span>
          </div>
          
>>>>>>> main
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="bg-slate-700 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 min-w-[200px]"
<<<<<<< HEAD
            disabled={connectionStatus === "disconnected"}
=======
            disabled={connectionStatus === 'disconnected'}
>>>>>>> main
          >
            {modelOptions.map((model) => (
              <option key={model.value} value={model.value}>
                {model.label}
              </option>
            ))}
          </select>
<<<<<<< HEAD

=======
          
>>>>>>> main
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
<<<<<<< HEAD

=======
                
>>>>>>> main
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
<<<<<<< HEAD
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`flex max-w-4xl ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                  >
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                      {message.role === "user" ? (
=======
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex max-w-4xl ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                      {message.role === 'user' ? (
>>>>>>> main
                        <UserCircleIcon className="h-8 w-8 text-gray-400" />
                      ) : (
                        <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-orange-600 rounded-full flex items-center justify-center">
                          <SparklesIcon className="h-4 w-4 text-white" />
                        </div>
                      )}
                    </div>
<<<<<<< HEAD

                    {/* Message Content */}
                    <div
                      className={`mx-3 ${message.role === "user" ? "text-right" : "text-left"}`}
                    >
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm font-medium text-gray-300">
                          {message.role === "user"
                            ? user?.name || "You"
                            : "AI Assistant"}
=======
                    
                    {/* Message Content */}
                    <div className={`mx-3 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm font-medium text-gray-300">
                          {message.role === 'user' ? user?.name || 'You' : 'AI Assistant'}
>>>>>>> main
                        </span>
                        <span className="text-xs text-gray-500">
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
<<<<<<< HEAD

                      <div
                        className={`p-4 rounded-lg ${
                          message.role === "user"
                            ? "bg-orange-500/10 border border-orange-500/20 text-white"
                            : "bg-slate-700/50 border border-slate-600 text-gray-200"
=======
                      
                      <div
                        className={`p-4 rounded-lg ${
                          message.role === 'user'
                            ? 'bg-orange-500/10 border border-orange-500/20 text-white'
                            : 'bg-slate-700/50 border border-slate-600 text-gray-200'
>>>>>>> main
                        }`}
                      >
                        <div className="text-sm">
                          {formatMessageContent(message.content)}
                        </div>
<<<<<<< HEAD

                        {message.role === "assistant" && (
=======
                        
                        {message.role === 'assistant' && (
>>>>>>> main
                          <div className="flex items-center justify-end mt-3 pt-3 border-t border-slate-600 space-x-2">
                            <button
                              onClick={() => handleCopyMessage(message.content)}
                              className="p-1 text-gray-400 hover:text-white transition-colors"
                              title="Copy message"
                            >
                              <ClipboardDocumentIcon className="h-4 w-4" />
                            </button>
                            <button
<<<<<<< HEAD
                              onClick={() =>
                                handleSendMessage(
                                  `Explain this in more detail: ${message.content.substring(0, 50)}...`,
                                )
                              }
=======
                              onClick={() => handleSendMessage(`Explain this in more detail: ${message.content.substring(0, 50)}...`)}
>>>>>>> main
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
<<<<<<< HEAD

=======
            
>>>>>>> main
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
<<<<<<< HEAD
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.1s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
=======
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
>>>>>>> main
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
<<<<<<< HEAD

            <div ref={messagesEndRef} />
          </div>

=======
            
            <div ref={messagesEndRef} />
          </div>
          
>>>>>>> main
          {/* Input Area */}
          <div className="border-t border-slate-600 p-4">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
<<<<<<< HEAD
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
=======
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendMessage()
>>>>>>> main
                    }
                  }}
                  placeholder="Ask me anything about code, debugging, or technical concepts..."
                  className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 resize-none max-h-32"
                  rows={3}
                />
              </div>
<<<<<<< HEAD

              <Button
                variant="primary"
                onClick={() => handleSendMessage()}
                disabled={
                  !inputMessage.trim() ||
                  isTyping ||
                  connectionStatus === "disconnected"
                }
                className="px-4 py-3"
                title={
                  connectionStatus === "disconnected"
                    ? "AI service is offline"
                    : ""
                }
=======
              
              <Button
                variant="primary"
                onClick={() => handleSendMessage()}
                disabled={!inputMessage.trim() || isTyping || connectionStatus === 'disconnected'}
                className="px-4 py-3"
                title={connectionStatus === 'disconnected' ? 'AI service is offline' : ''}
>>>>>>> main
              >
                <PaperAirplaneIcon className="h-5 w-5" />
              </Button>
            </div>
<<<<<<< HEAD

            <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
              <span>Press Enter to send, Shift+Enter for new line</span>
              <span>
                Model:{" "}
                {modelOptions.find((m) => m.value === selectedModel)?.label}
              </span>
=======
            
            <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
              <span>Press Enter to send, Shift+Enter for new line</span>
              <span>Model: {modelOptions.find(m => m.value === selectedModel)?.label}</span>
>>>>>>> main
            </div>
          </div>
        </Card>
      </div>
    </div>
<<<<<<< HEAD
  );
}
=======
  )
}
>>>>>>> main
