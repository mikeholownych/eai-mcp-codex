'use client'

import React, { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { debug } from '@/lib/utils'
import {
  VIDEO_STATUS_COLORS,
  VIDEO_STATUS_ICONS,
  VISIBILITY_COLORS,
} from '@/lib/statusHelpers'
import {
  VideoCameraIcon,
  ArrowUpTrayIcon as CloudUploadIcon,
  TagIcon,
  PlayIcon,
  EyeIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  CogIcon,
  ShareIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline'

const mockVideos = [
  {
    id: 'video-001',
    title: 'Getting Started with MCP Agent Development',
    description: 'A comprehensive walkthrough of building your first MCP agent using our platform.',
    duration: 1245, // seconds
    thumbnail: '/thumbnails/video-001.jpg',
    video_url: 'https://cdn.ethicalai.com/videos/video-001.mp4',
    status: 'published',
    visibility: 'enterprise',
    tags: ['Tutorial', 'MCP', 'Getting Started'],
    author: {
      name: 'David Kim',
      email: 'david@ethicalai.com',
      role: 'content'
    },
    views: 3247,
    likes: 89,
    created_at: '2024-01-15T10:00:00Z',
    published_at: '2024-01-15T14:00:00Z',
    updated_at: '2024-01-15T16:30:00Z',
    processing_status: 'completed',
    cdn_status: 'synced',
    auto_captions: true,
    seo_optimized: true
  },
  {
    id: 'video-002',
    title: 'Advanced Agent Collaboration Patterns',
    description: 'Learn how to implement complex multi-agent workflows and collaboration patterns.',
    duration: 2156,
    thumbnail: '/thumbnails/video-002.jpg',
    video_url: 'https://cdn.ethicalai.com/videos/video-002.mp4',
    status: 'processing',
    visibility: 'professional',
    tags: ['Advanced', 'Collaboration', 'Patterns'],
    author: {
      name: 'Sarah Johnson',
      email: 'sarah@ethicalai.com',
      role: 'content'
    },
    views: 0,
    likes: 0,
    created_at: '2024-01-14T09:30:00Z',
    published_at: null,
    updated_at: '2024-01-14T17:45:00Z',
    processing_status: 'encoding',
    cdn_status: 'uploading',
    auto_captions: false,
    seo_optimized: false
  },
  {
    id: 'video-003',
    title: 'Security Best Practices for AI Agents',
    description: 'Essential security considerations when deploying AI agents in production environments.',
    duration: 1876,
    thumbnail: '/thumbnails/video-003.jpg',
    video_url: 'https://cdn.ethicalai.com/videos/video-003.mp4',
    status: 'draft',
    visibility: 'standard',
    tags: ['Security', 'Best Practices', 'Production'],
    author: {
      name: 'Alex Rivera',
      email: 'alex@ethicalai.com',
      role: 'content'
    },
    views: 0,
    likes: 0,
    created_at: '2024-01-13T11:15:00Z',
    published_at: null,
    updated_at: '2024-01-13T15:20:00Z',
    processing_status: 'pending',
    cdn_status: 'waiting',
    auto_captions: false,
    seo_optimized: false
  }
]

const getStatusColor = (status: string) =>
  VIDEO_STATUS_COLORS[status] ?? VIDEO_STATUS_COLORS.draft

const getStatusIcon = (status: string) =>
  VIDEO_STATUS_ICONS[status] ?? VIDEO_STATUS_ICONS.draft

const getVisibilityColor = (visibility: string) =>
  VISIBILITY_COLORS[visibility] ?? VISIBILITY_COLORS.free

const formatDuration = (seconds: number) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export default function VideoContentManagement() {
  const { user } = useAuth()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [selectedVisibility, setSelectedVisibility] = useState('all')
  const [selectedTag, setSelectedTag] = useState('all')
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showPublishModal, setShowPublishModal] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)

  // Check if user has permission to manage video content
  if (!user || !['admin', 'content', 'manager'].includes(user.role)) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
        <p className="mt-1 text-sm text-gray-400">
          You don't have permission to access video management.
        </p>
      </div>
    )
  }

  const filteredVideos = mockVideos.filter(video => {
    const matchesSearch = video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         video.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = selectedStatus === 'all' || video.status === selectedStatus
    const matchesVisibility = selectedVisibility === 'all' || video.visibility === selectedVisibility
    const matchesTag = selectedTag === 'all' || video.tags.includes(selectedTag)
    return matchesSearch && matchesStatus && matchesVisibility && matchesTag
  })

  const allTags = [...new Set(mockVideos.flatMap(video => video.tags))]

  const videoStats = {
    total_videos: mockVideos.length,
    published: mockVideos.filter(v => v.status === 'published').length,
    processing: mockVideos.filter(v => v.status === 'processing').length,
    drafts: mockVideos.filter(v => v.status === 'draft').length,
    total_views: mockVideos.reduce((sum, video) => sum + video.views, 0),
    total_duration: mockVideos.reduce((sum, video) => sum + video.duration, 0)
  }

  const handleUploadVideo = () => {
    setShowUploadModal(true)
  }

  const handleEditVideo = (videoId: string) => {
    debug('Edit video', { videoId })
    alert(`Edit video ${videoId}`)
  }

  const handleDeleteVideo = (videoId: string) => {
    if (!confirm('Are you sure you want to delete this video? This action cannot be undone.')) {
      return
    }
    debug('Delete video', { videoId })
  }

  const handlePublishVideo = (videoId: string) => {
    debug('Publish video', { videoId })
    setShowPublishModal(true)
  }

  const simulateUpload = () => {
    setIsUploading(true)
    setUploadProgress(0)
    
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsUploading(false)
          setShowUploadModal(false)
          setUploadProgress(0)
          return 100
        }
        return prev + Math.random() * 15
      })
    }, 500)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Video Content Management</h1>
          <p className="text-gray-400">Upload, manage, and publish video content with auto-processing</p>
        </div>
        
        <Button variant="primary" onClick={handleUploadVideo}>
          <CloudUploadIcon className="h-4 w-4 mr-2" />
          Upload Video
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-6">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <VideoCameraIcon className="h-8 w-8 text-blue-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Total Videos</p>
              <p className="text-2xl font-semibold text-white">{videoStats.total_videos}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="h-8 w-8 text-green-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Published</p>
              <p className="text-2xl font-semibold text-white">{videoStats.published}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CogIcon className="h-8 w-8 text-blue-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Processing</p>
              <p className="text-2xl font-semibold text-white">{videoStats.processing}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DocumentTextIcon className="h-8 w-8 text-gray-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Drafts</p>
              <p className="text-2xl font-semibold text-white">{videoStats.drafts}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <EyeIcon className="h-8 w-8 text-purple-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Total Views</p>
              <p className="text-2xl font-semibold text-white">{videoStats.total_views.toLocaleString()}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="h-8 w-8 text-yellow-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Total Duration</p>
              <p className="text-2xl font-semibold text-white">{Math.floor(videoStats.total_duration / 3600)}h</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search videos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            />
          </div>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            <option value="all">All Status</option>
            <option value="published">Published</option>
            <option value="draft">Draft</option>
            <option value="processing">Processing</option>
            <option value="scheduled">Scheduled</option>
          </select>

          <select
            value={selectedVisibility}
            onChange={(e) => setSelectedVisibility(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            <option value="all">All Plans</option>
            <option value="free">Free</option>
            <option value="standard">Standard</option>
            <option value="professional">Professional</option>
            <option value="enterprise">Enterprise</option>
          </select>

          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            <option value="all">All Tags</option>
            {allTags.map(tag => (
              <option key={tag} value={tag}>{tag}</option>
            ))}
          </select>

          <div className="text-sm text-gray-400 flex items-center">
            Showing {filteredVideos.length} of {mockVideos.length} videos
          </div>
        </div>
      </Card>

      {/* Videos Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredVideos.map(video => (
          <Card key={video.id} className="p-0 overflow-hidden">
            {/* Thumbnail */}
            <div className="relative aspect-video bg-slate-700 flex items-center justify-center">
              <PlayIcon className="h-12 w-12 text-white/60" />
              <div className="absolute top-2 right-2">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(video.status)}`}>
                  {getStatusIcon(video.status)}
                  <span className="ml-1 capitalize">{video.status}</span>
                </span>
              </div>
              <div className="absolute bottom-2 right-2 bg-black/75 text-white text-xs px-2 py-1 rounded">
                {formatDuration(video.duration)}
              </div>
            </div>
            
            {/* Content */}
            <div className="p-4">
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-sm font-medium text-white line-clamp-2 flex-1">
                  {video.title}
                </h3>
              </div>
              
              <p className="text-sm text-gray-400 line-clamp-2 mb-3">
                {video.description}
              </p>
              
              {/* Author & Stats */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <UserCircleIcon className="h-4 w-4 text-gray-400 mr-1" />
                  <span className="text-xs text-gray-400">{video.author.name}</span>
                </div>
                <div className="flex items-center space-x-3 text-xs text-gray-400">
                  <span className="flex items-center">
                    <EyeIcon className="h-3 w-3 mr-1" />
                    {video.views.toLocaleString()}
                  </span>
                </div>
              </div>
              
              {/* Tags */}
              <div className="flex flex-wrap gap-1 mb-3">
                {video.tags.slice(0, 3).map(tag => (
                  <span key={tag} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-500/10 text-gray-400">
                    <TagIcon className="h-3 w-3 mr-1" />
                    {tag}
                  </span>
                ))}
              </div>
              
              {/* Plan Access */}
              <div className="flex items-center justify-between mb-4">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getVisibilityColor(video.visibility)}`}>
                  {video.visibility.toUpperCase()}
                </span>
                <div className="flex items-center space-x-1">
                  {video.auto_captions && (
                    <span className="text-xs text-green-400" title="Auto-captions enabled">
                      CC
                    </span>
                  )}
                  {video.seo_optimized && (
                    <span className="text-xs text-blue-400" title="SEO optimized">
                      SEO
                    </span>
                  )}
                </div>
              </div>
              
              {/* Processing Status */}
              {video.status === 'processing' && (
                <div className="mb-4">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Processing: {video.processing_status}</span>
                    <span>CDN: {video.cdn_status}</span>
                  </div>
                  <div className="bg-slate-600 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: '65%' }}
                    ></div>
                  </div>
                </div>
              )}
              
              {/* Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-600">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditVideo(video.id)}
                    className="p-1 text-gray-400 hover:text-blue-400 transition-colors"
                    title="Edit Video"
                  >
                    <CogIcon className="h-4 w-4" />
                  </button>
                  
                  {video.status === 'published' && (
                    <button
                      className="p-1 text-gray-400 hover:text-green-400 transition-colors"
                      title="Share Video"
                    >
                      <ShareIcon className="h-4 w-4" />
                    </button>
                  )}
                  
                  {video.status === 'draft' && user.role === 'admin' && (
                    <button
                      onClick={() => handlePublishVideo(video.id)}
                      className="p-1 text-gray-400 hover:text-green-400 transition-colors"
                      title="Publish Video"
                    >
                      <CheckCircleIcon className="h-4 w-4" />
                    </button>
                  )}
                  
                  {['admin', 'content'].includes(user.role) && (
                    <button
                      onClick={() => handleDeleteVideo(video.id)}
                      className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                      title="Delete Video"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  )}
                </div>
                
                <div className="text-xs text-gray-500">
                  {new Date(video.updated_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {filteredVideos.length === 0 && (
        <Card className="p-12 text-center">
          <VideoCameraIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No videos found</h3>
          <p className="text-gray-400 mb-6">
            Try adjusting your search criteria or upload a new video.
          </p>
          <Button variant="primary" onClick={handleUploadVideo}>
            <CloudUploadIcon className="h-4 w-4 mr-2" />
            Upload Video
          </Button>
        </Card>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 p-6 rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-white mb-4">
              Upload New Video
            </h3>
            
            {!isUploading ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Video File
                  </label>
                  <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center">
                    <CloudUploadIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-white mb-2">Drag and drop your video file here</p>
                    <p className="text-sm text-gray-400 mb-4">or click to browse</p>
                    <input 
                      type="file" 
                      accept="video/*" 
                      className="hidden" 
                      id="video-upload"
                    />
                    <label 
                      htmlFor="video-upload" 
                      className="inline-flex items-center px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 cursor-pointer"
                    >
                      Select File
                    </label>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Title
                    </label>
                    <input 
                      type="text" 
                      className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                      placeholder="Enter video title..."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Plan Access
                    </label>
                    <select className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600">
                      <option value="free">Free</option>
                      <option value="standard">Standard</option>
                      <option value="professional">Professional</option>
                      <option value="enterprise">Enterprise</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Description
                  </label>
                  <textarea 
                    rows={3}
                    className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                    placeholder="Brief description of the video..."
                  ></textarea>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Tags (comma-separated)
                  </label>
                  <input 
                    type="text" 
                    className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                    placeholder="Tutorial, MCP, Getting Started"
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input 
                      type="checkbox" 
                      defaultChecked
                      className="mr-3 rounded bg-slate-700 border-slate-600 text-orange-500 focus:ring-orange-500"
                    />
                    <span className="text-white">Enable auto-captions</span>
                  </label>
                  
                  <label className="flex items-center">
                    <input 
                      type="checkbox" 
                      defaultChecked
                      className="mr-3 rounded bg-slate-700 border-slate-600 text-orange-500 focus:ring-orange-500"
                    />
                    <span className="text-white">Optimize for SEO</span>
                  </label>
                  
                  <label className="flex items-center">
                    <input 
                      type="checkbox" 
                      className="mr-3 rounded bg-slate-700 border-slate-600 text-orange-500 focus:ring-orange-500"
                    />
                    <span className="text-white">Publish immediately after processing</span>
                  </label>
                </div>
                
                <div className="flex space-x-3 mt-6">
                  <Button 
                    variant="outline" 
                    className="flex-1"
                    onClick={() => setShowUploadModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button 
                    variant="primary" 
                    className="flex-1"
                    onClick={simulateUpload}
                  >
                    Upload Video
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <CloudUploadIcon className="h-16 w-16 text-blue-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">Uploading Video...</h3>
                <p className="text-gray-400 mb-6">Please don't close this window</p>
                
                <div className="bg-slate-700 rounded-full h-4 mb-4">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                
                <p className="text-sm text-gray-400">
                  {Math.round(uploadProgress)}% complete
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}