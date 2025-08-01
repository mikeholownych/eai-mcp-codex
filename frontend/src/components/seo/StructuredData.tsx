interface StructuredDataProps {
  data: object
}

export default function StructuredData({ data }: StructuredDataProps) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(data, null, 2)
      }}
    />
  )
}

// Organization Schema
export const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Ethical AI Insider",
  "alternateName": "EAI Codex",
  "description": "Advanced AI agent network for developers. Generate production-ready code with multi-agent collaboration, enterprise security, and seamless DevTool integrations.",
  "url": "https://new.ethical-ai-insider.com",
  "logo": "https://new.ethical-ai-insider.com/icons/icon-512x512.png",
  "image": "https://new.ethical-ai-insider.com/og-image.png",
  "sameAs": [
    "https://twitter.com/ethicalaiinsider",
    "https://linkedin.com/company/ethical-ai-insider",
    "https://github.com/ethical-ai-insider"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-555-0123",
    "contactType": "customer service",
    "availableLanguage": ["English"],
    "areaServed": "Worldwide"
  },
  "founder": {
    "@type": "Person",
    "name": "Ethical AI Insider Team"
  },
  "foundingDate": "2024",
  "address": {
    "@type": "PostalAddress",
    "addressCountry": "US"
  }
}

// Software Application Schema
export const softwareApplicationSchema = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "EAI Codex - MCP Agent Network",
  "description": "Secure, multi-tenant platform for code generation via agentic AI with real-time collaboration and enterprise features.",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Web Browser",
  "offers": {
    "@type": "Offer",
    "price": "29",
    "priceCurrency": "USD",
    "priceValidUntil": "2025-12-31",
    "availability": "https://schema.org/InStock",
    "description": "Standard plan with basic AI models and features"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "ratingCount": "1247",
    "bestRating": "5",
    "worstRating": "1"
  },
  "author": {
    "@type": "Organization",
    "name": "Ethical AI Insider"
  },
  "datePublished": "2024-01-01",
  "dateModified": "2024-12-01",
  "version": "1.0.0",
  "screenshot": "https://new.ethical-ai-insider.com/screenshots/dashboard.png",
  "downloadUrl": "https://new.ethical-ai-insider.com/register",
  "installUrl": "https://new.ethical-ai-insider.com/register",
  "softwareVersion": "1.0.0",
  "releaseNotes": "Initial release with multi-agent collaboration, OAuth integration, and enterprise security features."
}

// Service Schema
export const serviceSchema = {
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "AI Code Generation Service",
  "description": "Professional AI-powered code generation service with multi-agent collaboration and enterprise security.",
  "provider": {
    "@type": "Organization",
    "name": "Ethical AI Insider"
  },
  "areaServed": "Worldwide",
  "hasOfferCatalog": {
    "@type": "OfferCatalog",
    "name": "Code Generation Plans",
    "itemListElement": [
      {
        "@type": "Offer",
        "itemOffered": {
          "@type": "Service",
          "name": "Standard Plan",
          "description": "Basic AI models with standard features"
        },
        "price": "29",
        "priceCurrency": "USD",
        "priceSpecification": {
          "@type": "UnitPriceSpecification",
          "price": "29",
          "priceCurrency": "USD",
          "unitText": "MONTH"
        }
      },
      {
        "@type": "Offer",
        "itemOffered": {
          "@type": "Service",
          "name": "Pro Plan",
          "description": "Advanced AI models with collaboration features"
        },
        "price": "79",
        "priceCurrency": "USD",
        "priceSpecification": {
          "@type": "UnitPriceSpecification",
          "price": "79",
          "priceCurrency": "USD",
          "unitText": "MONTH"
        }
      }
    ]
  },
  "audience": {
    "@type": "Audience",
    "audienceType": "Software Developers"
  }
}

// FAQ Schema
export const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is the EAI Codex MCP Agent Network?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "EAI Codex is an advanced AI agent network that helps developers generate production-ready code through multi-agent collaboration. It integrates Claude O3, Sonnet 4, and other specialized AI models to provide intelligent code generation, real-time collaboration, and enterprise-grade security."
      }
    },
    {
      "@type": "Question",
      "name": "How does the multi-agent collaboration work?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Our multi-agent system uses specialized AI agents that work together on complex coding tasks. Each agent has specific expertise - code generation, security review, testing, etc. They collaborate in real-time to produce higher quality code than single-agent systems."
      }
    },
    {
      "@type": "Question",
      "name": "Is the platform secure for enterprise use?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes, EAI Codex is SOC 2 compliant with enterprise-grade security features including JWT tenant isolation, row-level security, comprehensive audit logging, and RBAC controls. We maintain the highest security standards for business-critical applications."
      }
    },
    {
      "@type": "Question",
      "name": "What integrations are available?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "We integrate with popular development tools including GitHub, VS Code, CI/CD pipelines, and team communication platforms like Slack. Our API allows for custom integrations to fit your existing workflow."
      }
    },
    {
      "@type": "Question",
      "name": "Can I try the platform for free?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes, we offer a free trial that includes access to basic AI models and core features. You can sign up with GitHub or Google OAuth for instant access, no credit card required."
      }
    }
  ]
}

// Breadcrumb Schema
export const breadcrumbSchema = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://new.ethical-ai-insider.com"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "AI Code Generation",
      "item": "https://new.ethical-ai-insider.com/features"
    }
  ]
}