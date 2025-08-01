'use client'

import { useEffect } from 'react'

interface WebVital {
  name: string
  value: number
  id: string
  delta?: number
}

export default function WebVitalsReporter() {
  useEffect(() => {
    // Only run in browser
    if (typeof window === 'undefined') return

    // Import web-vitals dynamically
    import('web-vitals').then(({ onFCP, onLCP, onCLS, onFID, onTTFB, onINP }) => {
      const vitalsHandler = (metric: WebVital) => {
        // Send to analytics endpoint
        if (typeof fetch !== 'undefined') {
          fetch('/api/analytics/vitals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: metric.name,
              value: metric.value,
              id: metric.id,
              url: window.location.href,
              userAgent: navigator.userAgent,
              timestamp: Date.now()
            })
          }).catch(() => {
            // Ignore analytics errors
          })
        }

        // Send to service worker for performance monitoring
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
          navigator.serviceWorker.controller.postMessage({
            type: 'PERFORMANCE_METRICS',
            metrics: {
              name: metric.name,
              value: metric.value,
              id: metric.id,
              url: window.location.href,
              timestamp: Date.now()
            }
          })
        }

        // Log to console in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`[Web Vitals] ${metric.name}:`, metric.value)
        }
      }

      // Track all Core Web Vitals
      onFCP(vitalsHandler)  // First Contentful Paint
      onLCP(vitalsHandler)  // Largest Contentful Paint  
      onCLS(vitalsHandler)  // Cumulative Layout Shift
      onFID(vitalsHandler)  // First Input Delay
      onTTFB(vitalsHandler) // Time to First Byte
      onINP(vitalsHandler)  // Interaction to Next Paint
    }).catch((error) => {
      console.warn('Failed to load web-vitals library:', error)
    })
  }, [])

  // Track additional performance metrics
  useEffect(() => {
    if (typeof window === 'undefined') return

    const trackPerformance = () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      
      if (navigation) {
        const metrics = {
          // Navigation timing
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
          
          // Connection timing
          dnsLookup: navigation.domainLookupEnd - navigation.domainLookupStart,
          tcpConnect: navigation.connectEnd - navigation.connectStart,
          
          // Request/Response timing
          requestTime: navigation.responseStart - navigation.requestStart,
          responseTime: navigation.responseEnd - navigation.responseStart,
          
          // Critical rendering path
          domInteractive: navigation.domInteractive - navigation.fetchStart,
          domComplete: navigation.domComplete - navigation.fetchStart
        }

        // Send custom metrics
        if (typeof fetch !== 'undefined') {
          fetch('/api/analytics/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              ...metrics,
              url: window.location.href,
              userAgent: navigator.userAgent,
              timestamp: Date.now()
            })
          }).catch(() => {
            // Ignore analytics errors
          })
        }

        if (process.env.NODE_ENV === 'development') {
          console.table(metrics)
        }
      }
    }

    // Track performance on load
    if (document.readyState === 'complete') {
      trackPerformance()
    } else {
      window.addEventListener('load', trackPerformance, { once: true })
    }
  }, [])

  // Track resource loading performance
  useEffect(() => {
    if (typeof window === 'undefined') return

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      
      entries.forEach((entry) => {
        if (entry.entryType === 'resource') {
          const resource = entry as PerformanceResourceTiming
          
          // Track slow resources (>1s)
          if (resource.duration > 1000) {
            console.warn(`Slow resource detected: ${resource.name} (${Math.round(resource.duration)}ms)`)
            
            if (typeof fetch !== 'undefined') {
              fetch('/api/analytics/slow-resources', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  url: resource.name,
                  duration: Math.round(resource.duration),
                  size: resource.transferSize,
                  type: resource.initiatorType,
                  page: window.location.href,
                  timestamp: Date.now()
                })
              }).catch(() => {
                // Ignore analytics errors
              })
            }
          }
        }
      })
    })

    try {
      observer.observe({ entryTypes: ['resource'] })
    } catch (error) {
      console.warn('Performance Observer not supported:', error)
    }

    return () => observer.disconnect()
  }, [])

  return null // This component doesn't render anything
}