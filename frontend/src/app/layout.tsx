import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Ethical AI Insider - MCP Agent Network',
  description: 'Secure, multi-tenant platform for code generation via agentic AI with real-time collaboration and enterprise features.',
  keywords: 'AI, code generation, ethics, agents, collaboration, enterprise',
  authors: [{ name: 'Ethical AI Insider' }],
  openGraph: {
    title: 'Ethical AI Insider - MCP Agent Network',
    description: 'Secure, multi-tenant platform for code generation via agentic AI',
    type: 'website',
    siteName: 'Ethical AI Insider',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Ethical AI Insider - MCP Agent Network',
    description: 'Secure, multi-tenant platform for code generation via agentic AI',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'your-google-verification-code',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#a855f7',
  colorScheme: 'dark',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        {/* Preconnect to external domains */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        
        {/* Preload critical fonts */}
        <link
          rel="preload"
          href="/fonts/Inter-Regular.woff2"
          as="font"
          type="font/woff2"
          crossOrigin=""
        />
        <link
          rel="preload"
          href="/fonts/Inter-Medium.woff2"
          as="font"
          type="font/woff2"
          crossOrigin=""
        />
        
        {/* DNS prefetch for API endpoints */}
        <link rel="dns-prefetch" href="//newapi.ethical-ai-insider.com" />
        
        {/* Optimize resource loading */}
        <link rel="preload" href="/globals.css" as="style" />
        
        {/* Performance monitoring script */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Web Vitals tracking
              function vitals(name, value, id) {
                if (typeof gtag !== 'undefined') {
                  gtag('event', name, {
                    event_category: 'Web Vitals',
                    value: Math.round(name === 'CLS' ? value * 1000 : value),
                    event_label: id,
                    non_interaction: true,
                  });
                }
                
                // Send to custom analytics endpoint
                if (typeof fetch !== 'undefined') {
                  fetch('/api/analytics/vitals', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, value, id, url: window.location.href })
                  }).catch(() => {});
                }
              }
              
              // Load Web Vitals library and track metrics
              if ('loading' in HTMLImageElement.prototype) {
                import('https://unpkg.com/web-vitals@3/dist/web-vitals.js').then(({ onFCP, onLCP, onCLS, onFID, onTTFB }) => {
                  onFCP(vitals);
                  onLCP(vitals);
                  onCLS(vitals);
                  onFID(vitals);
                  onTTFB(vitals);
                });
              }
            `,
          }}
        />
      </head>
      <body className="antialiased min-h-screen">
        {children}
        
        {/* Service Worker Registration */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js')
                    .then(function(registration) {
                      console.log('SW registered: ', registration);
                    })
                    .catch(function(registrationError) {
                      console.log('SW registration failed: ', registrationError);
                    });
                });
              }
            `,
          }}
        />
      </body>
    </html>
  )
}
