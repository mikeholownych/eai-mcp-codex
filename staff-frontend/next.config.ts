/** @type {import('next').NextConfig} */
const cryptoLib = require("crypto");
const isProd = process.env.NODE_ENV === "production";

const nextConfig = {
  reactStrictMode: !isProd,

  // Output configuration for production
  output: isProd ? "standalone" : undefined,

  // Production optimizations
  ...(isProd
    ? {
        compress: true,
        poweredByHeader: false,
        generateEtags: false,
        swcMinify: true,
        experimental: {
          optimizeCss: true,
          optimizePackageImports: ["@headlessui/react", "@heroicons/react"],
        },
      }
    : {}),

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000",
    NEXT_PUBLIC_EARLY_ACCESS: process.env.NEXT_PUBLIC_EARLY_ACCESS || "false",
    NEXT_PUBLIC_SITE_URL:
      process.env.NEXTAUTH_URL || "https://new.ethical-ai-insider.com",
  },

  // Image domains for external images
  images: {
    domains: ["avatars.githubusercontent.com", "github.com"],
    remotePatterns: [
      {
        protocol: "https",
        hostname: "avatars.githubusercontent.com",
        port: "",
        pathname: "/u/**",
      },
    ],
  },

  // Redirects for better UX
  async redirects() {
    return [
      {
        source: "/dashboard",
        destination: "/",
        permanent: false,
      },
      {
        source: "/app",
        destination: "/",
        permanent: false,
      },
    ];
  },

  // Security headers
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=31536000; includeSubDomains; preload",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },

  // Webpack configuration for better builds
  webpack: (
    config: any,
    { buildId, dev, isServer, defaultLoaders, webpack }: any,
  ) => {
    // Production optimizations
    if (!dev) {
      config.optimization.splitChunks = {
        chunks: "all",
        cacheGroups: {
          framework: {
            chunks: "all",
            name: "framework",
            test: /(?<!node_modules.*)[\\/]node_modules[\\/](react|react-dom|scheduler|prop-types|use-subscription)[\\/]/,
            priority: 40,
            enforce: true,
          },
          lib: {
            test(module: any) {
              return (
                module.size() > 160000 &&
                /node_modules[/\\]/.test(module.identifier())
              );
            },
            name(module: any) {
              const hash = cryptoLib.createHash("sha1");
              hash.update(module.identifier());
              return hash.digest("hex").substring(0, 8);
            },
            priority: 30,
            minChunks: 1,
            reuseExistingChunk: true,
          },
        },
      };
    }

    return config;
  },

  // Error handling
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },

  // TypeScript configuration
  typescript: {
    ignoreBuildErrors: false,
  },

  // ESLint configuration
  eslint: {
    ignoreDuringBuilds: false,
  },
};

module.exports = nextConfig;
