'use client'

import React, { useState } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import {
  FolderIcon,
  PlusIcon,
  EllipsisVerticalIcon,
  CalendarDaysIcon,
  CodeBracketIcon,
  TrashIcon,
  PencilIcon,
  ShareIcon,
} from '@heroicons/react/24/outline'

interface Project {
  id: string
  name: string
  description: string
  language: string
  lastModified: Date
  fileCount: number
  status: 'active' | 'archived'
}

const projects: Project[] = [
  {
    id: '1',
    name: 'E-commerce Platform',
    description: 'Full-stack e-commerce solution with React and Node.js',
    language: 'TypeScript',
    lastModified: new Date('2024-01-20T15:30:00'),
    fileCount: 47,
    status: 'active',
  },
  {
    id: '2',
    name: 'Data Analytics Dashboard',
    description: 'Interactive dashboard for business intelligence',
    language: 'Python',
    lastModified: new Date('2024-01-19T11:20:00'),
    fileCount: 23,
    status: 'active',
  },
  {
    id: '3',
    name: 'Mobile App Backend',
    description: 'REST API for mobile application',
    language: 'Java',
    lastModified: new Date('2024-01-18T14:45:00'),
    fileCount: 31,
    status: 'active',
  },
  {
    id: '4',
    name: 'Machine Learning Model',
    description: 'Customer segmentation ML pipeline',
    language: 'Python',
    lastModified: new Date('2024-01-15T09:15:00'),
    fileCount: 12,
    status: 'archived',
  },
]

const languageColors = {
  TypeScript: 'bg-blue-500/10 text-blue-400',
  JavaScript: 'bg-yellow-500/10 text-yellow-400',
  Python: 'bg-green-500/10 text-green-400',
  Java: 'bg-orange-500/10 text-orange-400',
  'C++': 'bg-purple-500/10 text-purple-400',
  Go: 'bg-cyan-500/10 text-cyan-400',
}

export default function ProjectsPage() {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [filter, setFilter] = useState<'all' | 'active' | 'archived'>('all')
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    language: 'TypeScript',
  })

  const filteredProjects = projects.filter(project => 
    filter === 'all' || project.status === filter
  )

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Creating project:', newProject)
    setShowCreateForm(false)
    setNewProject({ name: '', description: '', language: 'TypeScript' })
  }

  if (showCreateForm) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Create New Project</h1>
            <p className="text-gray-400">Start a new coding project with AI assistance</p>
          </div>
          <Button variant="outline" onClick={() => setShowCreateForm(false)}>
            Cancel
          </Button>
        </div>

        <Card className="p-6">
          <form onSubmit={handleCreateProject} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Project Name
              </label>
              <input
                type="text"
                value={newProject.name}
                onChange={(e) => setNewProject(prev => ({ ...prev, name: e.target.value }))}
                placeholder="My Awesome Project"
                className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={newProject.description}
                onChange={(e) => setNewProject(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Brief description of your project..."
                className="w-full h-24 bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 resize-none"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Primary Language
              </label>
              <select
                value={newProject.language}
                onChange={(e) => setNewProject(prev => ({ ...prev, language: e.target.value }))}
                className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
              >
                {Object.keys(languageColors).map((lang) => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>
            </div>

            <div className="flex justify-end space-x-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateForm(false)}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                Create Project
              </Button>
            </div>
          </form>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Projects</h1>
          <p className="text-gray-400">Manage your coding projects and collaborate with AI</p>
        </div>
        <Button variant="primary" onClick={() => setShowCreateForm(true)}>
          <PlusIcon className="h-4 w-4 mr-2" />
          New Project
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-1 bg-slate-800 p-1 rounded-lg w-fit">
        {(['all', 'active', 'archived'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              filter === tab
                ? 'bg-orange-500 text-white'
                : 'text-gray-400 hover:text-white hover:bg-slate-700'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            <span className="ml-2 text-xs">
              ({tab === 'all' ? projects.length : projects.filter(p => p.status === tab).length})
            </span>
          </button>
        ))}
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredProjects.map((project) => (
          <Card key={project.id} className="p-6 hover:bg-slate-700/30 transition-colors group">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
                  <FolderIcon className="h-5 w-5 text-white" />
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-semibold text-white">{project.name}</h3>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    languageColors[project.language as keyof typeof languageColors] || 'bg-gray-500/10 text-gray-400'
                  }`}>
                    {project.language}
                  </span>
                </div>
              </div>
              
              <div className="relative">
                <button className="p-1 text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity">
                  <EllipsisVerticalIcon className="h-5 w-5" />
                </button>
              </div>
            </div>

            <p className="text-gray-400 text-sm mb-4 line-clamp-2">
              {project.description}
            </p>

            <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
              <div className="flex items-center">
                <CodeBracketIcon className="h-4 w-4 mr-1" />
                {project.fileCount} files
              </div>
              <div className="flex items-center">
                <CalendarDaysIcon className="h-4 w-4 mr-1" />
                {project.lastModified.toLocaleDateString()}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm">
                  <CodeBracketIcon className="h-4 w-4 mr-1" />
                  Open
                </Button>
                
                {project.status === 'active' && (
                  <Button variant="outline" size="sm">
                    <ShareIcon className="h-4 w-4 mr-1" />
                    Share
                  </Button>
                )}
              </div>

              <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="p-1 text-gray-400 hover:text-white">
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button className="p-1 text-gray-400 hover:text-red-400">
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>

            {project.status === 'archived' && (
              <div className="mt-3 pt-3 border-t border-slate-600">
                <span className="text-xs text-gray-500">Archived project</span>
              </div>
            )}
          </Card>
        ))}
      </div>

      {filteredProjects.length === 0 && (
        <Card className="p-12 text-center">
          <FolderIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">
            {filter === 'all' ? 'No projects yet' : `No ${filter} projects`}
          </h3>
          <p className="text-gray-400 mb-6">
            {filter === 'all' 
              ? "Create your first project to start coding with AI assistance."
              : `You don't have any ${filter} projects.`
            }
          </p>
          {filter === 'all' && (
            <Button variant="primary" onClick={() => setShowCreateForm(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              Create Your First Project
            </Button>
          )}
        </Card>
      )}
    </div>
  )
}