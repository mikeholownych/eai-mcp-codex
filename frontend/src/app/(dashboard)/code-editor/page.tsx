'use client'

import React, { useState, useRef } from 'react'
import dynamic from 'next/dynamic'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import {
  PlayIcon,
  DocumentArrowDownIcon,
  FolderOpenIcon,
  SparklesIcon,
  CommandLineIcon,
  CogIcon,
  BookOpenIcon,
} from '@heroicons/react/24/outline'

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-96 bg-slate-800 rounded-lg flex items-center justify-center">
      <div className="text-gray-400">Loading editor...</div>
    </div>
  ),
})

const languages = [
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'python', label: 'Python' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' },
  { value: 'html', label: 'HTML' },
  { value: 'css', label: 'CSS' },
  { value: 'json', label: 'JSON' },
]

const codeTemplates = {
  javascript: `// JavaScript Example
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

console.log('Fibonacci sequence:');
for (let i = 0; i < 10; i++) {
  console.log(\`F(\${i}) = \${fibonacci(i)}\`);
}`,

  typescript: `// TypeScript Example
interface User {
  id: number;
  name: string;
  email: string;
}

class UserService {
  private users: User[] = [];

  addUser(user: User): void {
    this.users.push(user);
  }

  getUserById(id: number): User | undefined {
    return this.users.find(user => user.id === id);
  }
}

const userService = new UserService();
userService.addUser({ id: 1, name: 'John Doe', email: 'john@example.com' });`,

  python: `# Python Example
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)

# Example usage
numbers = [64, 34, 25, 12, 22, 11, 90]
print("Original array:", numbers)
sorted_numbers = quicksort(numbers)
print("Sorted array:", sorted_numbers)`,

  java: `// Java Example
public class Calculator {
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        
        System.out.println("Addition: " + calc.add(10, 5));
        System.out.println("Subtraction: " + calc.subtract(10, 5));
        System.out.println("Multiplication: " + calc.multiply(10, 5));
        System.out.println("Division: " + calc.divide(10, 5));
    }
    
    public double add(double a, double b) {
        return a + b;
    }
    
    public double subtract(double a, double b) {
        return a - b;
    }
    
    public double multiply(double a, double b) {
        return a * b;
    }
    
    public double divide(double a, double b) {
        if (b != 0) {
            return a / b;
        }
        throw new IllegalArgumentException("Cannot divide by zero");
    }
}`,
}

export default function CodeEditorPage() {
  const [code, setCode] = useState(codeTemplates.javascript)
  const [language, setLanguage] = useState('javascript')
  const [isRunning, setIsRunning] = useState(false)
  const [output, setOutput] = useState('')
  const [showAIPanel, setShowAIPanel] = useState(false)
  const [aiPrompt, setAiPrompt] = useState('')
  type EditorRef = {
    getValue: () => string;
    setValue: (value: string) => void;
    focus: () => void;
    updateOptions?: (options: Record<string, unknown>) => void;
  };

  const editorRef = useRef<EditorRef | null>(null)

  const handleLanguageChange = (newLanguage: string) => {
    setLanguage(newLanguage)
    setCode(codeTemplates[newLanguage as keyof typeof codeTemplates] || '')
  }

  const handleRunCode = async () => {
    setIsRunning(true)
    setOutput('Running code...')

    // Simulate code execution
    setTimeout(() => {
      setOutput(
        `Code executed successfully!\nLanguage: ${language}\nLines: ${code.split('\n').length}`,
      )
      setIsRunning(false)
    }, 2000)
  }

  const handleAIAssist = async () => {
    if (!aiPrompt.trim()) return

    setOutput('AI is analyzing your request...')

    // Simulate AI response
    setTimeout(() => {
      setOutput(
        `AI Suggestion: Based on your prompt "${aiPrompt}", here are some recommendations:\n\n1. Consider using more descriptive variable names\n2. Add error handling for edge cases\n3. Consider performance optimizations\n4. Add unit tests for your functions`,
      )
      setAiPrompt('')
    }, 2000)
  }

<<<<<<< HEAD
  const handleEditorDidMount = (editor: unknown) => {
    const typedEditor = editor as {
      getValue: () => string;
      setValue: (value: string) => void;
      focus: () => void;
      updateOptions?: (options: Record<string, unknown>) => void;
    };
=======
  const handleEditorDidMount = (editor: { getValue: () => string; setValue: (value: string) => void; focus: () => void }) => {
    editorRef.current = editor
>>>>>>> main
    
    editorRef.current = {
      getValue: () => typedEditor.getValue(),
      setValue: (value: string) => typedEditor.setValue(value),
      focus: () => typedEditor.focus(),
      updateOptions: (options: Record<string, unknown>) => typedEditor.updateOptions?.(options)
    };

    // Configure editor options if updateOptions exists
    if (typedEditor.updateOptions) {
      typedEditor.updateOptions({
        theme: 'vs-dark',
        fontSize: 14,
        minimap: { enabled: true },
        wordWrap: 'on',
        automaticLayout: true,
      });
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Code Editor</h1>
          <p className="text-gray-400">Write, edit, and test your code with AI assistance</p>
        </div>

        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <FolderOpenIcon className="h-4 w-4 mr-2" />
            Open Project
          </Button>
          <Button variant="outline" size="sm">
            <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
            Save
          </Button>
        </div>
      </div>

      {/* Editor Toolbar */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Language Selector */}
            <div className="relative">
              <select
                value={language}
                onChange={e => handleLanguageChange(e.target.value)}
                className="bg-slate-700 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
              >
                {languages.map(lang => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>

            {/* File Info */}
            <div className="text-sm text-gray-400">
              Lines: {code.split('\n').length} | Characters: {code.length}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={() => setShowAIPanel(!showAIPanel)}>
              <SparklesIcon className="h-4 w-4 mr-2" />
              AI Assistant
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={handleRunCode}
              loading={isRunning}
              disabled={isRunning}
            >
              <PlayIcon className="h-4 w-4 mr-2" />
              {isRunning ? 'Running...' : 'Run Code'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Editor and Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Code Editor */}
        <div className={showAIPanel ? 'lg:col-span-2' : 'lg:col-span-3'}>
          <Card className="p-0 overflow-hidden">
            <div className="h-96">
              <MonacoEditor
                height="100%"
                language={language}
                value={code}
                onChange={value => setCode(value || '')}
                onMount={handleEditorDidMount}
                theme="vs-dark"
                options={{
                  selectOnLineNumbers: true,
                  roundedSelection: false,
                  readOnly: false,
                  cursorStyle: 'line',
                  automaticLayout: true,
                  minimap: { enabled: true },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  wordWrap: 'on',
                }}
              />
            </div>
          </Card>
        </div>

        {/* AI Assistant Panel */}
        {showAIPanel && (
          <div className="lg:col-span-1">
            <Card className="p-4 h-96">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  <SparklesIcon className="h-5 w-5 mr-2 text-orange-400" />
                  AI Assistant
                </h3>
                <button
                  onClick={() => setShowAIPanel(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Ask AI for help:
                  </label>
                  <textarea
                    value={aiPrompt}
                    onChange={e => setAiPrompt(e.target.value)}
                    placeholder="e.g., Optimize this code, explain this function, add error handling..."
                    className="w-full h-20 bg-slate-700 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 resize-none"
                  />
                </div>

                <Button
                  variant="primary"
                  size="sm"
                  className="w-full"
                  onClick={handleAIAssist}
                  disabled={!aiPrompt.trim()}
                >
                  <SparklesIcon className="h-4 w-4 mr-2" />
                  Get AI Help
                </Button>

                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-gray-300">Quick Actions:</h4>
                  <div className="space-y-1">
                    <button className="w-full text-left text-sm text-gray-400 hover:text-white p-2 hover:bg-slate-700 rounded">
                      🔧 Optimize performance
                    </button>
                    <button className="w-full text-left text-sm text-gray-400 hover:text-white p-2 hover:bg-slate-700 rounded">
                      🐛 Debug issues
                    </button>
                    <button className="w-full text-left text-sm text-gray-400 hover:text-white p-2 hover:bg-slate-700 rounded">
                      📝 Add comments
                    </button>
                    <button className="w-full text-left text-sm text-gray-400 hover:text-white p-2 hover:bg-slate-700 rounded">
                      🧪 Generate tests
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* Output Panel */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <CommandLineIcon className="h-5 w-5 mr-2" />
            Output
          </h3>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <BookOpenIcon className="h-4 w-4 mr-2" />
              Docs
            </Button>
            <Button variant="outline" size="sm">
              <CogIcon className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-4 h-32 overflow-y-auto">
          <pre className="text-sm text-gray-300 whitespace-pre-wrap">
            {output || 'No output yet. Run your code to see results here.'}
          </pre>
        </div>
      </Card>
    </div>
  )
}
