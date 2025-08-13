<<<<<<< HEAD
"use client";

import React, { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { debug } from "@/lib/utils";
=======
'use client'

import React, { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { useRouter } from 'next/navigation'
import { debug } from '@/lib/utils'
>>>>>>> main
import {
  PencilSquareIcon,
  DocumentTextIcon,
  EyeIcon,
  TrashIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  TagIcon,
  ShareIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  UserCircleIcon,
<<<<<<< HEAD
} from "@heroicons/react/24/outline";

// Helper functions for blog status
const getBlogStatusColor = (status: string): string => {
  switch (status) {
    case "published":
      return "bg-green-100 text-green-800";
    case "draft":
      return "bg-yellow-100 text-yellow-800";
    case "archived":
      return "bg-gray-100 text-gray-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
};

const getBlogStatusIcon = (status: string) => {
  switch (status) {
    case "published":
      return <CheckCircleIcon className="h-3 w-3" />;
    case "draft":
      return <ClockIcon className="h-3 w-3" />;
    case "archived":
      return <ExclamationTriangleIcon className="h-3 w-3" />;
    default:
      return <ClockIcon className="h-3 w-3" />;
  }
};

const mockBlogPosts = [
  {
    id: "post-001",
    title: "The Future of AI-Assisted Code Generation",
    slug: "future-ai-assisted-code-generation",
    excerpt:
      "Exploring how AI agents are revolutionizing the software development process...",
    content: "<p>Full content here...</p>",
    status: "published",
    author: {
      name: "Sarah Johnson",
      email: "sarah@ethicalai.com",
      role: "content",
    },
    tags: ["AI", "Development", "Innovation"],
    created_at: "2024-01-15T10:00:00Z",
    published_at: "2024-01-15T14:00:00Z",
    updated_at: "2024-01-15T16:30:00Z",
    views: 2847,
    syndicated: true,
    seo_score: 85,
  },
  {
    id: "post-002",
    title: "Best Practices for Multi-Agent Collaboration",
    slug: "best-practices-multi-agent-collaboration",
    excerpt:
      "Learn how to implement effective collaboration patterns between AI agents...",
    content: "<p>Full content here...</p>",
    status: "draft",
    author: {
      name: "Mike Chen",
      email: "mike@ethicalai.com",
      role: "content",
    },
    tags: ["Collaboration", "Agents", "Best Practices"],
    created_at: "2024-01-14T09:30:00Z",
    published_at: null,
    updated_at: "2024-01-14T17:45:00Z",
    views: 0,
    syndicated: false,
    seo_score: 72,
  },
  {
    id: "post-003",
    title: "Security Considerations in AI Development",
    slug: "security-considerations-ai-development",
    excerpt:
      "Essential security practices when building AI-powered applications...",
    content: "<p>Full content here...</p>",
    status: "review",
    author: {
      name: "Alex Rivera",
      email: "alex@ethicalai.com",
      role: "content",
    },
    tags: ["Security", "AI", "Development"],
    created_at: "2024-01-13T11:15:00Z",
    published_at: null,
    updated_at: "2024-01-13T15:20:00Z",
    views: 0,
    syndicated: false,
    seo_score: 91,
  },
];

export default function BlogContentManagement() {
  const { user } = useAuth();
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedTag, setSelectedTag] = useState("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSyndicateModal, setShowSyndicateModal] = useState(false);

  // Check if user has permission to manage blog content
  if (!user || !["admin", "content", "manager"].includes(user.role)) {
=======
} from '@heroicons/react/24/outline'

const mockBlogPosts = [
  {
    id: 'post-001',
    title: 'The Future of AI-Assisted Code Generation',
    slug: 'future-ai-assisted-code-generation',
    excerpt: 'Exploring how AI agents are revolutionizing the software development process...',
    content: '<p>Full content here...</p>',
    status: 'published',
    author: {
      name: 'Sarah Johnson',
      email: 'sarah@ethicalai.com',
      role: 'content'
    },
    tags: ['AI', 'Development', 'Innovation'],
    created_at: '2024-01-15T10:00:00Z',
    published_at: '2024-01-15T14:00:00Z',
    updated_at: '2024-01-15T16:30:00Z',
    views: 2847,
    syndicated: true,
    seo_score: 85
  },
  {
    id: 'post-002',
    title: 'Best Practices for Multi-Agent Collaboration',
    slug: 'best-practices-multi-agent-collaboration',
    excerpt: 'Learn how to implement effective collaboration patterns between AI agents...',
    content: '<p>Full content here...</p>',
    status: 'draft',
    author: {
      name: 'Mike Chen',
      email: 'mike@ethicalai.com',
      role: 'content'
    },
    tags: ['Collaboration', 'Agents', 'Best Practices'],
    created_at: '2024-01-14T09:30:00Z',
    published_at: null,
    updated_at: '2024-01-14T17:45:00Z',
    views: 0,
    syndicated: false,
    seo_score: 72
  },
  {
    id: 'post-003',
    title: 'Security Considerations in AI Development',
    slug: 'security-considerations-ai-development',
    excerpt: 'Essential security practices when building AI-powered applications...',
    content: '<p>Full content here...</p>',
    status: 'review',
    author: {
      name: 'Alex Rivera',
      email: 'alex@ethicalai.com',
      role: 'content'
    },
    tags: ['Security', 'AI', 'Development'],
    created_at: '2024-01-13T11:15:00Z',
    published_at: null,
    updated_at: '2024-01-13T15:20:00Z',
    views: 0,
    syndicated: false,
    seo_score: 91
  }
]

export default function BlogContentManagement() {
  const { user } = useAuth()
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [selectedTag, setSelectedTag] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showSyndicateModal, setShowSyndicateModal] = useState(false)

  // Check if user has permission to manage blog content
  if (!user || !['admin', 'content', 'manager'].includes(user.role)) {
>>>>>>> main
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
        <p className="mt-1 text-sm text-gray-400">
          You don&apos;t have permission to access blog management.
        </p>
      </div>
<<<<<<< HEAD
    );
  }

  const filteredPosts = mockBlogPosts.filter((post) => {
    const matchesSearch =
      post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      post.excerpt.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      selectedStatus === "all" || post.status === selectedStatus;
    const matchesTag = selectedTag === "all" || post.tags.includes(selectedTag);
    return matchesSearch && matchesStatus && matchesTag;
  });

  const allTags = [...new Set(mockBlogPosts.flatMap((post) => post.tags))];

  const blogStats = {
    total_posts: mockBlogPosts.length,
    published: mockBlogPosts.filter((p) => p.status === "published").length,
    drafts: mockBlogPosts.filter((p) => p.status === "draft").length,
    in_review: mockBlogPosts.filter((p) => p.status === "review").length,
    total_views: mockBlogPosts.reduce((sum, post) => sum + post.views, 0),
  };

  const handleCreatePost = () => {
    setShowCreateModal(true);
  };

  const handleEditPost = (postId: string) => {
    debug("Edit post", { postId });
    router.push(`/staff/blog?edit=${postId}`);
  };

  const handleDeletePost = (postId: string) => {
    if (
      !confirm(
        "Are you sure you want to delete this blog post? This action cannot be undone.",
      )
    ) {
      return;
    }
    debug("Delete post", { postId });
    alert(`Delete post ${postId}`);
  };

  const handlePublishPost = (postId: string) => {
    debug("Publish post", { postId });
    alert(`Publish post ${postId}`);
  };

  const handleSyndicatePost = (postId: string) => {
    debug("Syndicate post", { postId });
    setShowSyndicateModal(true);
  };
=======
    )
  }

  const filteredPosts = mockBlogPosts.filter(post => {
    const matchesSearch = post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         post.excerpt.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = selectedStatus === 'all' || post.status === selectedStatus
    const matchesTag = selectedTag === 'all' || post.tags.includes(selectedTag)
    return matchesSearch && matchesStatus && matchesTag
  })

  const allTags = [...new Set(mockBlogPosts.flatMap(post => post.tags))]

  const blogStats = {
    total_posts: mockBlogPosts.length,
    published: mockBlogPosts.filter(p => p.status === 'published').length,
    drafts: mockBlogPosts.filter(p => p.status === 'draft').length,
    in_review: mockBlogPosts.filter(p => p.status === 'review').length,
    total_views: mockBlogPosts.reduce((sum, post) => sum + post.views, 0)
  }

  const handleCreatePost = () => {
    setShowCreateModal(true)
  }

  const handleEditPost = (postId: string) => {
    debug('Edit post', { postId })
    router.push(`/staff/blog?edit=${postId}`)
  }

  const handleDeletePost = (postId: string) => {
    if (!confirm('Are you sure you want to delete this blog post? This action cannot be undone.')) {
      return
    }
    debug('Delete post', { postId })
    alert(`Delete post ${postId}`)
  }

  const handlePublishPost = (postId: string) => {
    debug('Publish post', { postId })
    alert(`Publish post ${postId}`)
  }

  const handleSyndicatePost = (postId: string) => {
    debug('Syndicate post', { postId })
    setShowSyndicateModal(true)
  }
>>>>>>> main

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
<<<<<<< HEAD
          <h1 className="text-2xl font-bold text-white">
            Blog Content Management
          </h1>
          <p className="text-gray-400">
            Create, edit, and manage Ethical AI Insider blog content
          </p>
        </div>

=======
          <h1 className="text-2xl font-bold text-white">Blog Content Management</h1>
          <p className="text-gray-400">Create, edit, and manage Ethical AI Insider blog content</p>
        </div>
        
>>>>>>> main
        <Button variant="primary" onClick={handleCreatePost}>
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Post
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DocumentTextIcon className="h-8 w-8 text-blue-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Total Posts</p>
<<<<<<< HEAD
              <p className="text-2xl font-semibold text-white">
                {blogStats.total_posts}
              </p>
=======
              <p className="text-2xl font-semibold text-white">{blogStats.total_posts}</p>
>>>>>>> main
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
<<<<<<< HEAD
              <p className="text-2xl font-semibold text-white">
                {blogStats.published}
              </p>
=======
              <p className="text-2xl font-semibold text-white">{blogStats.published}</p>
>>>>>>> main
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <PencilSquareIcon className="h-8 w-8 text-gray-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Drafts</p>
<<<<<<< HEAD
              <p className="text-2xl font-semibold text-white">
                {blogStats.drafts}
              </p>
=======
              <p className="text-2xl font-semibold text-white">{blogStats.drafts}</p>
>>>>>>> main
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="h-8 w-8 text-yellow-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">In Review</p>
<<<<<<< HEAD
              <p className="text-2xl font-semibold text-white">
                {blogStats.in_review}
              </p>
=======
              <p className="text-2xl font-semibold text-white">{blogStats.in_review}</p>
>>>>>>> main
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
<<<<<<< HEAD
              <p className="text-2xl font-semibold text-white">
                {blogStats.total_views.toLocaleString()}
              </p>
=======
              <p className="text-2xl font-semibold text-white">{blogStats.total_views.toLocaleString()}</p>
>>>>>>> main
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search posts..."
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
            <option value="review">In Review</option>
            <option value="scheduled">Scheduled</option>
          </select>

          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            <option value="all">All Tags</option>
<<<<<<< HEAD
            {allTags.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
=======
            {allTags.map(tag => (
              <option key={tag} value={tag}>{tag}</option>
>>>>>>> main
            ))}
          </select>

          <div className="text-sm text-gray-400 flex items-center">
            Showing {filteredPosts.length} of {mockBlogPosts.length} posts
          </div>
        </div>
      </Card>

      {/* Blog Posts Table */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-700/50">
              <tr>
<<<<<<< HEAD
                <th className="text-left py-3 px-6 font-medium text-gray-300">
                  Post
                </th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">
                  Author
                </th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">
                  Status
                </th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">
                  Tags
                </th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">
                  Views
                </th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">
                  Updated
                </th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">
                  Actions
                </th>
=======
                <th className="text-left py-3 px-6 font-medium text-gray-300">Post</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Author</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Status</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Tags</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Views</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Updated</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Actions</th>
>>>>>>> main
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {filteredPosts.map((post) => (
                <tr key={post.id} className="hover:bg-slate-700/30">
                  <td className="py-4 px-6">
                    <div>
<<<<<<< HEAD
                      <div className="text-sm font-medium text-white line-clamp-1">
                        {post.title}
                      </div>
                      <div className="text-sm text-gray-400 line-clamp-2 mt-1">
                        {post.excerpt}
                      </div>
=======
                      <div className="text-sm font-medium text-white line-clamp-1">{post.title}</div>
                      <div className="text-sm text-gray-400 line-clamp-2 mt-1">{post.excerpt}</div>
>>>>>>> main
                      <div className="flex items-center mt-2 space-x-2">
                        {post.syndicated && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400">
                            <ShareIcon className="h-3 w-3 mr-1" />
                            Syndicated
                          </span>
                        )}
<<<<<<< HEAD
                        <span className="text-xs text-gray-500">
                          SEO: {post.seo_score}/100
                        </span>
=======
                        <span className="text-xs text-gray-500">SEO: {post.seo_score}/100</span>
>>>>>>> main
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center">
                      <UserCircleIcon className="h-6 w-6 text-gray-400 mr-2" />
                      <div>
<<<<<<< HEAD
                        <div className="text-sm font-medium text-white">
                          {post.author.name}
                        </div>
                        <div className="text-xs text-gray-400 capitalize">
                          {post.author.role}
                        </div>
=======
                        <div className="text-sm font-medium text-white">{post.author.name}</div>
                        <div className="text-xs text-gray-400 capitalize">{post.author.role}</div>
>>>>>>> main
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6">
<<<<<<< HEAD
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getBlogStatusColor(post.status)}`}
                    >
=======
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getBlogStatusColor(post.status)}`}>
>>>>>>> main
                      {getBlogStatusIcon(post.status)}
                      <span className="ml-1 capitalize">{post.status}</span>
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex flex-wrap gap-1">
<<<<<<< HEAD
                      {post.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-500/10 text-gray-400"
                        >
=======
                      {post.tags.slice(0, 2).map(tag => (
                        <span key={tag} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-500/10 text-gray-400">
>>>>>>> main
                          <TagIcon className="h-3 w-3 mr-1" />
                          {tag}
                        </span>
                      ))}
                      {post.tags.length > 2 && (
<<<<<<< HEAD
                        <span className="text-xs text-gray-500">
                          +{post.tags.length - 2} more
                        </span>
=======
                        <span className="text-xs text-gray-500">+{post.tags.length - 2} more</span>
>>>>>>> main
                      )}
                    </div>
                  </td>
                  <td className="py-4 px-6">
<<<<<<< HEAD
                    <div className="text-sm text-white">
                      {post.views.toLocaleString()}
                    </div>
=======
                    <div className="text-sm text-white">{post.views.toLocaleString()}</div>
>>>>>>> main
                    <div className="text-xs text-gray-400">views</div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="text-sm text-gray-400">
                      {new Date(post.updated_at).toLocaleDateString()}
                    </div>
                    <div className="text-xs text-gray-500">
<<<<<<< HEAD
                      {new Date(post.updated_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
=======
                      {new Date(post.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
>>>>>>> main
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleEditPost(post.id)}
                        className="p-1 text-gray-400 hover:text-blue-400 transition-colors"
                        title="Edit Post"
                      >
                        <PencilSquareIcon className="h-4 w-4" />
                      </button>
<<<<<<< HEAD
                      {post.status === "published" && (
=======
                      {post.status === 'published' && (
>>>>>>> main
                        <button
                          onClick={() => handleSyndicatePost(post.id)}
                          className="p-1 text-gray-400 hover:text-green-400 transition-colors"
                          title="Syndicate"
                        >
                          <ShareIcon className="h-4 w-4" />
                        </button>
                      )}
<<<<<<< HEAD
                      {post.status === "draft" && user.role === "admin" && (
=======
                      {post.status === 'draft' && user.role === 'admin' && (
>>>>>>> main
                        <button
                          onClick={() => handlePublishPost(post.id)}
                          className="p-1 text-gray-400 hover:text-green-400 transition-colors"
                          title="Publish"
                        >
                          <CheckCircleIcon className="h-4 w-4" />
                        </button>
                      )}
<<<<<<< HEAD
                      {["admin", "content"].includes(user.role) && (
=======
                      {['admin', 'content'].includes(user.role) && (
>>>>>>> main
                        <button
                          onClick={() => handleDeletePost(post.id)}
                          className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                          title="Delete Post"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {filteredPosts.length === 0 && (
        <Card className="p-12 text-center">
          <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
<<<<<<< HEAD
          <h3 className="text-lg font-medium text-white mb-2">
            No blog posts found
          </h3>
=======
          <h3 className="text-lg font-medium text-white mb-2">No blog posts found</h3>
>>>>>>> main
          <p className="text-gray-400 mb-6">
            Try adjusting your search criteria or create a new blog post.
          </p>
          <Button variant="primary" onClick={handleCreatePost}>
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Blog Post
          </Button>
        </Card>
      )}

      {/* Create Post Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 p-6 rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-white mb-4">
              Create New Blog Post
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Title
                </label>
<<<<<<< HEAD
                <input
                  type="text"
=======
                <input 
                  type="text" 
>>>>>>> main
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                  placeholder="Enter blog post title..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Excerpt
                </label>
<<<<<<< HEAD
                <textarea
=======
                <textarea 
>>>>>>> main
                  rows={3}
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                  placeholder="Brief description of the post..."
                ></textarea>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Tags (comma-separated)
                </label>
<<<<<<< HEAD
                <input
                  type="text"
=======
                <input 
                  type="text" 
>>>>>>> main
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
                  placeholder="AI, Development, Best Practices"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Status
                </label>
                <select className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600">
                  <option value="draft">Draft</option>
                  <option value="review">Ready for Review</option>
<<<<<<< HEAD
                  {user.role === "admin" && (
                    <option value="published">Publish Immediately</option>
                  )}
                </select>
              </div>
              <div className="flex space-x-3 mt-6">
                <Button
                  variant="outline"
=======
                  {user.role === 'admin' && <option value="published">Publish Immediately</option>}
                </select>
              </div>
              <div className="flex space-x-3 mt-6">
                <Button 
                  variant="outline" 
>>>>>>> main
                  className="flex-1"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
<<<<<<< HEAD
                <Button
                  variant="primary"
                  className="flex-1"
                  onClick={() => {
                    // Handle create post
                    setShowCreateModal(false);
=======
                <Button 
                  variant="primary" 
                  className="flex-1"
                  onClick={() => {
                    // Handle create post
                    setShowCreateModal(false)
>>>>>>> main
                  }}
                >
                  Create Post
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Syndicate Modal */}
      {showSyndicateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">
              Syndicate Blog Post
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Syndication Channels
                </label>
                <div className="space-y-2">
                  {[
<<<<<<< HEAD
                    {
                      id: "newsletter",
                      name: "ConvertKit Newsletter",
                      enabled: true,
                    },
                    {
                      id: "medium",
                      name: "Medium Publication",
                      enabled: false,
                    },
                    { id: "devto", name: "Dev.to Community", enabled: false },
                    {
                      id: "linkedin",
                      name: "LinkedIn Article",
                      enabled: false,
                    },
                  ].map((channel) => (
                    <label key={channel.id} className="flex items-center">
                      <input
                        type="checkbox"
=======
                    { id: 'newsletter', name: 'ConvertKit Newsletter', enabled: true },
                    { id: 'medium', name: 'Medium Publication', enabled: false },
                    { id: 'devto', name: 'Dev.to Community', enabled: false },
                    { id: 'linkedin', name: 'LinkedIn Article', enabled: false }
                  ].map(channel => (
                    <label key={channel.id} className="flex items-center">
                      <input 
                        type="checkbox" 
>>>>>>> main
                        defaultChecked={channel.enabled}
                        className="mr-3 rounded bg-slate-700 border-slate-600 text-orange-500 focus:ring-orange-500"
                      />
                      <span className="text-white">{channel.name}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
<<<<<<< HEAD
                <Button
                  variant="outline"
=======
                <Button 
                  variant="outline" 
>>>>>>> main
                  className="flex-1"
                  onClick={() => setShowSyndicateModal(false)}
                >
                  Cancel
                </Button>
<<<<<<< HEAD
                <Button
                  variant="primary"
                  className="flex-1"
                  onClick={() => {
                    // Handle syndicate
                    setShowSyndicateModal(false);
=======
                <Button 
                  variant="primary" 
                  className="flex-1"
                  onClick={() => {
                    // Handle syndicate
                    setShowSyndicateModal(false)
>>>>>>> main
                  }}
                >
                  Syndicate
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
<<<<<<< HEAD
  );
}
=======
  )
}
>>>>>>> main
