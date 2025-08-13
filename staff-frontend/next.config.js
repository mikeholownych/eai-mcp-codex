/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
<<<<<<< HEAD
  output: 'standalone',

  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ||
      "https://newapi.ethical-ai-insider.com",
    NEXT_PUBLIC_WS_URL:
      process.env.NEXT_PUBLIC_WS_URL || "wss://newapi.ethical-ai-insider.com",
    NEXT_PUBLIC_SITE_URL:
      process.env.NEXTAUTH_URL || "https://new.ethical-ai-insider.com",
  },

  images: {
    domains: ["avatars.githubusercontent.com"],
=======
  
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://newapi.ethical-ai-insider.com',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'wss://newapi.ethical-ai-insider.com',
    NEXT_PUBLIC_SITE_URL: process.env.NEXTAUTH_URL || 'https://new.ethical-ai-insider.com',
  },

  images: {
    domains: ['avatars.githubusercontent.com'],
>>>>>>> main
  },

  async redirects() {
    return [
      {
<<<<<<< HEAD
        source: "/dashboard",
        destination: "/",
=======
        source: '/dashboard',
        destination: '/',
>>>>>>> main
        permanent: false,
      },
    ];
  },

  async headers() {
    return [
      {
<<<<<<< HEAD
        source: "/(.*)",
        headers: [
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
=======
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
>>>>>>> main
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
