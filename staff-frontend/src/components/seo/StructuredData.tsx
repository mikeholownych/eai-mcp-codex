interface StructuredDataProps {
  data: object;
}

export default function StructuredData({ data }: StructuredDataProps) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(data, null, 2),
      }}
    />
  );
}

// Organization Schema
export const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "AI-Powered Development Platform",
  alternateName: "EAI Codex",
  description:
    "Unleash your potential with our cutting-edge AI agent network. Generate production-ready code, collaborate seamlessly, and secure your innovations with enterprise-grade tools. Stop building, start creating – the future of development is here.",
  url: "https://new.ethical-ai-insider.com",
  logo: "https://new.ethical-ai-insider.com/icons/icon-512x512.png",
  image: "https://new.ethical-ai-insider.com/og-image.png",
  sameAs: [
    "https://twitter.com/ethicalaiinsider",
    "https://linkedin.com/company/ethical-ai-insider",
    "https://github.com/ethical-ai-insider",
  ],
  contactPoint: {
    "@type": "ContactPoint",
    telephone: "+1-555-0123",
    contactType: "customer service",
    availableLanguage: ["English"],
    areaServed: "Worldwide",
  },
  founder: {
    "@type": "Person",
    name: "Ethical AI Insider Team",
  },
  foundingDate: "2024",
  address: {
    "@type": "PostalAddress",
    addressCountry: "US",
  },
};

// Software Application Schema
export const softwareApplicationSchema = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "EAI Codex - AI-Powered Development Platform",
  description:
    "Revolutionize your development workflow with our secure, multi-tenant AI platform. Leverage agentic AI for intelligent code generation, real-time collaboration, and robust enterprise features. Experience the future of coding.",
  applicationCategory: "DeveloperApplication",
  operatingSystem: "Web Browser",
  offers: {
    "@type": "Offer",
    price: "29",
    priceCurrency: "USD",
    priceValidUntil: "2025-12-31",
    availability: "https://schema.org/InStock",
    description: "Standard plan with basic AI models and features",
  },
  aggregateRating: {
    "@type": "AggregateRating",
    ratingValue: "4.9",
    ratingCount: "2500",
    bestRating: "5",
    worstRating: "1",
  },
  author: {
    "@type": "Organization",
    name: "Ethical AI Insider",
  },
  datePublished: "2024-01-01",
  dateModified: "2024-12-01",
  version: "1.1.0",
  screenshot: "https://new.ethical-ai-insider.com/screenshots/dashboard.png",
  downloadUrl: "https://new.ethical-ai-insider.com/register",
  installUrl: "https://new.ethical-ai-insider.com/register",
  softwareVersion: "1.1.0",
  releaseNotes:
    "Major update: Enhanced multi-agent collaboration, improved code generation accuracy, new security protocols, and expanded DevTool integrations for a seamless development experience.",
};

// Service Schema
export const serviceSchema = {
  "@context": "https://schema.org",
  "@type": "Service",
  name: "AI-Powered Software Development Service",
  description:
    "Transform your ideas into production-ready software with our professional AI-powered development service. Featuring multi-agent collaboration, advanced security, and seamless integration into your existing workflows.",
  provider: {
    "@type": "Organization",
    name: "Ethical AI Insider",
  },
  areaServed: "Worldwide",
  hasOfferCatalog: {
    "@type": "OfferCatalog",
    name: "Code Generation Plans",
    itemListElement: [
      {
        "@type": "Offer",
        itemOffered: {
          "@type": "Service",
          name: "Standard Plan",
          description: "Basic AI models with standard features",
        },
        price: "29",
        priceCurrency: "USD",
        priceSpecification: {
          "@type": "UnitPriceSpecification",
          price: "29",
          priceCurrency: "USD",
          unitText: "MONTH",
        },
      },
      {
        "@type": "Offer",
        itemOffered: {
          "@type": "Service",
          name: "Pro Plan",
          description: "Advanced AI models with collaboration features",
        },
        price: "79",
        priceCurrency: "USD",
        priceSpecification: {
          "@type": "UnitPriceSpecification",
          price: "79",
          priceCurrency: "USD",
          unitText: "MONTH",
        },
      },
    ],
  },
  audience: {
    "@type": "Audience",
    audienceType: "Software Developers",
  },
};

// FAQ Schema
export const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "What is the EAI Codex AI-Powered Development Platform?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "EAI Codex is a revolutionary AI-powered platform designed to accelerate software development. It leverages an advanced multi-agent AI network, including models like Claude O3 and Sonnet 4, to generate high-quality, production-ready code, facilitate real-time collaboration, and ensure enterprise-grade security for your projects.",
      },
    },
    {
      "@type": "Question",
      name: "How does the multi-agent AI collaboration enhance development?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Our platform utilizes a sophisticated multi-agent AI system where specialized AI agents collaborate on various development tasks. For instance, one agent might focus on code generation, another on security auditing, and yet another on testing. This collaborative approach ensures higher code quality, faster development cycles, and more robust solutions compared to traditional single-agent or human-only workflows.",
      },
    },
    {
      "@type": "Question",
      name: "What security measures are in place for enterprise users?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "EAI Codex is built with enterprise-grade security at its core. We are SOC 2 compliant and implement robust features such as JWT tenant isolation, row-level security, comprehensive audit logging, and Role-Based Access Control (RBAC). Our commitment is to provide a highly secure environment for all your business-critical development needs.",
      },
    },
    {
      "@type": "Question",
      name: "Which development tools integrate with EAI Codex?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "EAI Codex offers seamless integration with a wide array of popular development tools, including GitHub, VS Code, and various CI/CD pipelines. We also support integrations with team communication platforms like Slack. Furthermore, our flexible API enables you to create custom integrations tailored to your specific workflow and existing tech stack.",
      },
    },
    {
      "@type": "Question",
      name: "Is there a free trial available for EAI Codex?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Absolutely! We encourage you to experience the power of EAI Codex with our free trial. It provides full access to our basic AI models and core features. You can sign up instantly using your GitHub or Google OAuth account – no credit card required. Start transforming your development process today!",
      },
    },
  ],
};

// Breadcrumb Schema
export const breadcrumbSchema = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    {
      "@type": "ListItem",
      position: 1,
      name: "Home",
      item: "https://new.ethical-ai-insider.com",
    },
    {
      "@type": "ListItem",
      position: 2,
      name: "AI Code Generation",
      item: "https://new.ethical-ai-insider.com/features",
    },
  ],
};

// WebSite Schema
export const websiteSchema = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "EAI Codex - AI-Powered Development Platform",
  url: "https://new.ethical-ai-insider.com",
  potentialAction: {
    "@type": "SearchAction",
    target: "https://new.ethical-ai-insider.com/search?q={search_term_string}",
    "query-input": "required name=search_term_string",
  },
};