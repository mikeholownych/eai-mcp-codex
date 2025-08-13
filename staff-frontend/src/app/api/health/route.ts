<<<<<<< HEAD
import { NextResponse } from "next/server";

export async function GET() {
  const healthData = {
    status: "healthy",
    timestamp: new Date().toISOString(),
    service: "mcp-frontend",
    version: process.env.npm_package_version || "1.0.0",
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || "development",
=======
import { NextResponse } from 'next/server';

export async function GET() {
  const healthData = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'mcp-frontend',
    version: process.env.npm_package_version || '1.0.0',
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development',
>>>>>>> main
    memory: {
      used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
      total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
      free: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
    },
    dependencies: {
<<<<<<< HEAD
      next: "healthy",
      node: process.version,
    },
=======
      next: 'healthy',
      node: process.version,
    }
>>>>>>> main
  };

  return NextResponse.json(healthData, {
    status: 200,
    headers: {
<<<<<<< HEAD
      "Cache-Control": "no-cache, no-store, must-revalidate",
      Pragma: "no-cache",
      Expires: "0",
    },
  });
}
=======
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
    },
  });
}
>>>>>>> main
