<<<<<<< HEAD
const CACHE_NAME = "mcp-agent-network-v1.0.0";
const STATIC_CACHE = "static-v1.0.0";
const DYNAMIC_CACHE = "dynamic-v1.0.0";

// Assets to cache immediately
const STATIC_ASSETS = [
  "/",
  "/demo",
  "/blog",
  "/docs",
  "/fonts/Inter-Regular.woff2",
  "/fonts/Inter-Medium.woff2",
  "/fonts/Inter-SemiBold.woff2",
  "/fonts/Inter-Bold.woff2",
  "/fonts/JetBrainsMono-Regular.woff2",
  "/fonts/JetBrainsMono-Medium.woff2",
  "/globals.css",
  "/favicon.ico",
=======
const CACHE_NAME = 'mcp-agent-network-v1.0.0';
const STATIC_CACHE = 'static-v1.0.0';
const DYNAMIC_CACHE = 'dynamic-v1.0.0';

// Assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/demo',
  '/blog',
  '/docs',
  '/fonts/Inter-Regular.woff2',
  '/fonts/Inter-Medium.woff2',
  '/fonts/Inter-SemiBold.woff2',
  '/fonts/Inter-Bold.woff2',
  '/fonts/JetBrainsMono-Regular.woff2',
  '/fonts/JetBrainsMono-Medium.woff2',
  '/globals.css',
  '/favicon.ico'
>>>>>>> main
];

// Routes that should be cached with network-first strategy
const NETWORK_FIRST_ROUTES = [
<<<<<<< HEAD
  "/api/",
  "/dashboard/",
  "/chat/",
  "/code-editor/",
];

// Routes that should bypass cache
const NO_CACHE_ROUTES = ["/api/auth/", "/api/websocket", "/ws"];

// Install event - cache static assets
self.addEventListener("install", (event) => {
  console.log("Service Worker: Install Event");

  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then((cache) => {
        console.log("Service Worker: Caching static assets");
        return cache.addAll(STATIC_ASSETS);
      }),
      caches.open(DYNAMIC_CACHE).then(() => {
        console.log("Service Worker: Dynamic cache ready");
      }),
    ]),
  );

=======
  '/api/',
  '/dashboard/',
  '/chat/',
  '/code-editor/'
];

// Routes that should bypass cache
const NO_CACHE_ROUTES = [
  '/api/auth/',
  '/api/websocket',
  '/ws'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Install Event');
  
  event.waitUntil(
    Promise.all([
      caches.open(STATIC_CACHE).then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      }),
      caches.open(DYNAMIC_CACHE).then(() => {
        console.log('Service Worker: Dynamic cache ready');
      })
    ])
  );
  
>>>>>>> main
  // Force activation of new service worker
  self.skipWaiting();
});

// Activate event - clean up old caches
<<<<<<< HEAD
self.addEventListener("activate", (event) => {
  console.log("Service Worker: Activate Event");

=======
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activate Event');
  
>>>>>>> main
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== STATIC_CACHE && cache !== DYNAMIC_CACHE) {
<<<<<<< HEAD
            console.log("Service Worker: Deleting old cache", cache);
            return caches.delete(cache);
          }
        }),
      );
    }),
  );

=======
            console.log('Service Worker: Deleting old cache', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  
>>>>>>> main
  // Take control of all pages
  self.clients.claim();
});

// Fetch event - handle requests with caching strategies
<<<<<<< HEAD
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (typeof location !== "undefined" && url.origin !== location.origin) {
    return;
  }

  // Skip non-GET requests
  if (request.method !== "GET") {
    return;
  }

  // Skip no-cache routes
  if (NO_CACHE_ROUTES.some((route) => url.pathname.startsWith(route))) {
    return;
  }

=======
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip cross-origin requests
  if (typeof location !== 'undefined' && url.origin !== location.origin) {
    return;
  }
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip no-cache routes
  if (NO_CACHE_ROUTES.some(route => url.pathname.startsWith(route))) {
    return;
  }
  
>>>>>>> main
  event.respondWith(handleRequest(request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
<<<<<<< HEAD

=======
  
>>>>>>> main
  try {
    // Static assets - cache first strategy
    if (isStaticAsset(url.pathname)) {
      return await cacheFirst(request, STATIC_CACHE);
    }
<<<<<<< HEAD

=======
    
>>>>>>> main
    // API routes - network first with short cache
    if (isApiRoute(url.pathname)) {
      return await networkFirst(request, DYNAMIC_CACHE, 300000); // 5 minutes
    }
<<<<<<< HEAD

=======
    
>>>>>>> main
    // Network-first routes (dynamic content)
    if (isNetworkFirstRoute(url.pathname)) {
      return await networkFirst(request, DYNAMIC_CACHE, 60000); // 1 minute
    }
<<<<<<< HEAD

    // Default: stale while revalidate for HTML pages
    return await staleWhileRevalidate(request, DYNAMIC_CACHE);
  } catch (error) {
    console.error("Service Worker: Fetch error", error);

=======
    
    // Default: stale while revalidate for HTML pages
    return await staleWhileRevalidate(request, DYNAMIC_CACHE);
    
  } catch (error) {
    console.error('Service Worker: Fetch error', error);
    
>>>>>>> main
    // Fallback to cache or offline page
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
<<<<<<< HEAD

    // Return offline fallback for HTML requests
    if (request.headers.get("accept")?.includes("text/html")) {
=======
    
    // Return offline fallback for HTML requests
    if (request.headers.get('accept')?.includes('text/html')) {
>>>>>>> main
      return new Response(
        `<!DOCTYPE html>
        <html>
        <head>
          <title>Offline - MCP Agent Network</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body { font-family: Inter, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; text-align: center; }
            .container { max-width: 600px; margin: 0 auto; }
            .icon { font-size: 4rem; margin-bottom: 1rem; }
            h1 { color: #a855f7; margin-bottom: 1rem; }
            p { line-height: 1.6; margin-bottom: 2rem; }
            .retry-btn { background: #a855f7; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="icon">🔌</div>
            <h1>You're Offline</h1>
            <p>Unable to connect to MCP Agent Network. Please check your internet connection and try again.</p>
            <button class="retry-btn" onclick="window.location.reload()">Retry</button>
          </div>
        </body>
        </html>`,
        {
          status: 200,
<<<<<<< HEAD
          headers: { "Content-Type": "text/html" },
        },
      );
    }

    return new Response("Offline", { status: 503 });
=======
          headers: { 'Content-Type': 'text/html' }
        }
      );
    }
    
    return new Response('Offline', { status: 503 });
>>>>>>> main
  }
}

// Cache first strategy - try cache, fallback to network
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
<<<<<<< HEAD

=======
  
>>>>>>> main
  if (cachedResponse) {
    // Return cached version, but update cache in background
    updateCacheInBackground(request, cache);
    return cachedResponse;
  }
<<<<<<< HEAD

  const networkResponse = await fetch(request);

  if (networkResponse.ok) {
    cache.put(request, networkResponse.clone());
  }

=======
  
  const networkResponse = await fetch(request);
  
  if (networkResponse.ok) {
    cache.put(request, networkResponse.clone());
  }
  
>>>>>>> main
  return networkResponse;
}

// Network first strategy - try network, fallback to cache
async function networkFirst(request, cacheName, maxAge = 300000) {
  const cache = await caches.open(cacheName);
<<<<<<< HEAD

  try {
    const networkResponse = await fetch(request);

=======
  
  try {
    const networkResponse = await fetch(request);
    
>>>>>>> main
    if (networkResponse.ok) {
      // Add timestamp to track freshness
      const responseWithTimestamp = new Response(networkResponse.body, {
        status: networkResponse.status,
        statusText: networkResponse.statusText,
        headers: {
          ...Object.fromEntries(networkResponse.headers.entries()),
<<<<<<< HEAD
          "sw-cache-timestamp": Date.now().toString(),
        },
      });

=======
          'sw-cache-timestamp': Date.now().toString()
        }
      });
      
>>>>>>> main
      cache.put(request, responseWithTimestamp.clone());
      return responseWithTimestamp;
    }
  } catch (error) {
<<<<<<< HEAD
    console.log("Service Worker: Network failed, trying cache");
  }

  // Network failed, try cache
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    const timestamp = cachedResponse.headers.get("sw-cache-timestamp");
    const age = timestamp ? Date.now() - parseInt(timestamp) : Infinity;

=======
    console.log('Service Worker: Network failed, trying cache');
  }
  
  // Network failed, try cache
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    const timestamp = cachedResponse.headers.get('sw-cache-timestamp');
    const age = timestamp ? Date.now() - parseInt(timestamp) : Infinity;
    
>>>>>>> main
    if (age < maxAge) {
      return cachedResponse;
    }
  }
<<<<<<< HEAD

  throw new Error("Network failed and no valid cache available");
=======
  
  throw new Error('Network failed and no valid cache available');
>>>>>>> main
}

// Stale while revalidate - return cached version immediately, update in background
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
<<<<<<< HEAD

  // Update cache in background
  const networkUpdate = fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => {
      // Network failed, but we might have cache
    });

=======
  
  // Update cache in background
  const networkUpdate = fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => {
    // Network failed, but we might have cache
  });
  
>>>>>>> main
  // Return cached version immediately if available
  if (cachedResponse) {
    return cachedResponse;
  }
<<<<<<< HEAD

=======
  
>>>>>>> main
  // No cache, wait for network
  return await networkUpdate;
}

// Update cache in background without blocking the response
function updateCacheInBackground(request, cache) {
<<<<<<< HEAD
  fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
    })
    .catch(() => {
      // Ignore network errors in background updates
    });
=======
  fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
  }).catch(() => {
    // Ignore network errors in background updates
  });
>>>>>>> main
}

// Helper functions
function isStaticAsset(pathname) {
<<<<<<< HEAD
  return (
    pathname.startsWith("/_next/static/") ||
    pathname.startsWith("/fonts/") ||
    pathname.match(
      /\.(css|js|woff|woff2|ttf|eot|svg|png|jpg|jpeg|gif|ico|webp|avif)$/,
    )
  );
}

function isApiRoute(pathname) {
  return pathname.startsWith("/api/");
}

function isNetworkFirstRoute(pathname) {
  return NETWORK_FIRST_ROUTES.some((route) => pathname.startsWith(route));
}

// Background sync for offline actions
self.addEventListener("sync", (event) => {
  if (event.tag === "background-sync") {
    event.waitUntil(
      // Handle offline actions when back online
      handleBackgroundSync(),
=======
  return pathname.startsWith('/_next/static/') ||
         pathname.startsWith('/fonts/') ||
         pathname.match(/\.(css|js|woff|woff2|ttf|eot|svg|png|jpg|jpeg|gif|ico|webp|avif)$/);
}

function isApiRoute(pathname) {
  return pathname.startsWith('/api/');
}

function isNetworkFirstRoute(pathname) {
  return NETWORK_FIRST_ROUTES.some(route => pathname.startsWith(route));
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Handle offline actions when back online
      handleBackgroundSync()
>>>>>>> main
    );
  }
});

async function handleBackgroundSync() {
  // Implementation for handling offline actions
<<<<<<< HEAD
  console.log("Service Worker: Background sync triggered");

  // Example: retry failed API requests
  const cache = await caches.open(DYNAMIC_CACHE);
  const requests = await cache.keys();

  for (const request of requests) {
    if (request.url.includes("failed-request")) {
=======
  console.log('Service Worker: Background sync triggered');
  
  // Example: retry failed API requests
  const cache = await caches.open(DYNAMIC_CACHE);
  const requests = await cache.keys();
  
  for (const request of requests) {
    if (request.url.includes('failed-request')) {
>>>>>>> main
      try {
        await fetch(request);
        await cache.delete(request);
      } catch (error) {
<<<<<<< HEAD
        console.log("Service Worker: Retry failed for", request.url);
=======
        console.log('Service Worker: Retry failed for', request.url);
>>>>>>> main
      }
    }
  }
}

// Push notification handling
<<<<<<< HEAD
self.addEventListener("push", (event) => {
  if (event.data) {
    const data = event.data.json();

    const options = {
      body: data.body,
      icon: "/favicon.ico",
      badge: "/favicon.ico",
      tag: data.tag || "mcp-notification",
      data: data.data || {},
      actions: data.actions || [],
    };

    event.waitUntil(
      self.registration.showNotification(
        data.title || "MCP Agent Network",
        options,
      ),
=======
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    
    const options = {
      body: data.body,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: data.tag || 'mcp-notification',
      data: data.data || {},
      actions: data.actions || []
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'MCP Agent Network', options)
>>>>>>> main
    );
  }
});

// Notification click handling
<<<<<<< HEAD
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  if (event.action) {
    // Handle action clicks
    console.log("Service Worker: Notification action clicked", event.action);
  } else {
    // Handle notification click
    event.waitUntil(clients.openWindow(event.notification.data.url || "/"));
=======
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action) {
    // Handle action clicks
    console.log('Service Worker: Notification action clicked', event.action);
  } else {
    // Handle notification click
    event.waitUntil(
      clients.openWindow(event.notification.data.url || '/')
    );
>>>>>>> main
  }
});

// Performance monitoring
<<<<<<< HEAD
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "PERFORMANCE_METRICS") {
    // Handle performance metrics from the main thread
    console.log(
      "Service Worker: Received performance metrics",
      event.data.metrics,
    );

    // Could send to analytics endpoint
    fetch("/api/analytics/sw-metrics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(event.data.metrics),
=======
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'PERFORMANCE_METRICS') {
    // Handle performance metrics from the main thread
    console.log('Service Worker: Received performance metrics', event.data.metrics);
    
    // Could send to analytics endpoint
    fetch('/api/analytics/sw-metrics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event.data.metrics)
>>>>>>> main
    }).catch(() => {
      // Ignore analytics errors
    });
  }
<<<<<<< HEAD
});
=======
});
>>>>>>> main
