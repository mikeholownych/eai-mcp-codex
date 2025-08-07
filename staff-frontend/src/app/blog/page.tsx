"use client";

import React from "react";
import Link from "next/link";
import {
  ArrowLeftIcon,
  CalendarIcon,
  UserIcon,
} from "@heroicons/react/24/outline";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";

const blogPosts = [
  {
    id: 1,
    title: "Introducing Multi-Agent Code Generation",
    excerpt:
      "Discover how our revolutionary multi-agent system transforms the way code is generated, reviewed, and deployed in enterprise environments.",
    author: "Dr. Sarah Chen",
    date: "2024-07-25",
    category: "AI Innovation",
    readTime: "8 min read",
    image: "/api/placeholder/400/200",
  },
  {
    id: 2,
    title: "Security-First AI: Building Trust in Automated Code Generation",
    excerpt:
      "Learn about our comprehensive security framework that ensures every line of AI-generated code meets enterprise security standards.",
    author: "Michael Rodriguez",
    date: "2024-07-20",
    category: "Security",
    readTime: "12 min read",
    image: "/api/placeholder/400/200",
  },
  {
    id: 3,
    title: "The Future of Developer Productivity with AI Agents",
    excerpt:
      "Explore how AI agents are reshaping software development workflows and what this means for developer productivity in 2024.",
    author: "Alex Thompson",
    date: "2024-07-15",
    category: "Productivity",
    readTime: "6 min read",
    image: "/api/placeholder/400/200",
  },
  {
    id: 4,
    title: "Enterprise AI Adoption: Lessons from Early Implementers",
    excerpt:
      "Real-world case studies and insights from companies successfully implementing AI-driven development practices.",
    author: "Jennifer Park",
    date: "2024-07-12",
    category: "Case Studies",
    readTime: "10 min read",
    image: "/api/placeholder/400/200",
  },
];

export default function BlogPage() {
  return (
    <div className="min-h-screen bg-slate-900">
      {/* Navigation */}
      <nav className="border-b border-slate-700 bg-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Link
                href="/"
                className="flex items-center text-slate-300 hover:text-white transition-colors"
              >
                <ArrowLeftIcon className="w-5 h-5 mr-2" />
                Back to Home
              </Link>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">AI</span>
              </div>
              <span className="text-xl font-bold text-white">
                Ethical AI Insider
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Blog Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            AI Insights & Innovation
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Stay up-to-date with the latest in AI-driven development, security
            best practices, and industry insights.
          </p>
        </div>

        {/* Featured Post */}
        <Card className="mb-12">
          <div className="lg:flex">
            <div className="lg:w-1/2">
              <div className="h-64 lg:h-full bg-gradient-to-br from-purple-600 to-blue-600 rounded-l-xl flex items-center justify-center">
                <div className="text-center">
                  <div className="w-16 h-16 bg-white bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-white font-bold text-2xl">AI</span>
                  </div>
                  <p className="text-white text-sm opacity-90">
                    Featured Article
                  </p>
                </div>
              </div>
            </div>
            <div className="lg:w-1/2 p-8">
              <div className="flex items-center space-x-4 mb-4">
                <span className="px-3 py-1 bg-purple-600 text-white text-sm rounded-full">
                  {blogPosts[0].category}
                </span>
                <div className="flex items-center text-gray-400 text-sm">
                  <CalendarIcon className="w-4 h-4 mr-1" />
                  {blogPosts[0].date}
                </div>
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">
                {blogPosts[0].title}
              </h2>
              <p className="text-gray-400 mb-6">{blogPosts[0].excerpt}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <UserIcon className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-400 text-sm">
                    {blogPosts[0].author}
                  </span>
                  <span className="text-gray-500">•</span>
                  <span className="text-gray-400 text-sm">
                    {blogPosts[0].readTime}
                  </span>
                </div>
                <Button variant="secondary" size="sm">
                  Read More
                </Button>
              </div>
            </div>
          </div>
        </Card>

        {/* Blog Posts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {blogPosts.slice(1).map((post) => (
            <Card key={post.id} hover>
              <div className="h-48 bg-gradient-to-br from-slate-700 to-slate-800 rounded-t-xl flex items-center justify-center mb-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <span className="text-white font-bold">AI</span>
                  </div>
                  <p className="text-slate-300 text-sm">{post.category}</p>
                </div>
              </div>

              <Card.Content>
                <div className="flex items-center space-x-4 mb-3">
                  <div className="flex items-center text-gray-400 text-sm">
                    <CalendarIcon className="w-4 h-4 mr-1" />
                    {post.date}
                  </div>
                  <span className="text-gray-500">•</span>
                  <span className="text-gray-400 text-sm">{post.readTime}</span>
                </div>

                <h3 className="text-xl font-semibold text-white mb-3">
                  {post.title}
                </h3>

                <p className="text-gray-400 mb-4 line-clamp-3">
                  {post.excerpt}
                </p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <UserIcon className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-400 text-sm">{post.author}</span>
                  </div>
                  <Button variant="ghost" size="sm">
                    Read More
                  </Button>
                </div>
              </Card.Content>
            </Card>
          ))}
        </div>

        {/* Newsletter Subscription */}
        <Card className="mt-12">
          <Card.Content className="text-center py-12">
            <h3 className="text-2xl font-bold text-white mb-4">
              Stay Informed
            </h3>
            <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
              Subscribe to our newsletter for the latest insights on AI
              development, security best practices, and industry trends.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md mx-auto">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <Button variant="secondary">Subscribe</Button>
            </div>
          </Card.Content>
        </Card>
      </div>
    </div>
  );
}
