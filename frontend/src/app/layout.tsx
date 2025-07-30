import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Ethical AI Insider - MCP Agent Network',
  description: 'Secure, multi-tenant platform for code generation via agentic AI with real-time collaboration and enterprise features.',
  keywords: 'AI, code generation, ethics, agents, collaboration, enterprise',
  authors: [{ name: 'Ethical AI Insider' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#f37a0a',
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
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
