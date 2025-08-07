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
];

// Routes that should be cached with network-first strategy
const NETWORK_FIRST_ROUTES = [
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

  // Force activation of new service worker
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener("activate", (event) => {
  console.log("Service Worker: Activate Event");

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== STATIC_CACHE && cache !== DYNAMIC_CACHE) {
            console.log("Service Worker: Deleting old cache", cache);
            return caches.delete(cache);
          }
        }),
      );
    }),
  );

  // Take control of all pages
  self.clients.claim();
});

// Fetch event - handle requests with caching strategies
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

  event.respondWith(handleRequest(request));
});

async function handleRequest(request) {
  const url = new URL(request.url);

  try {
    // Static assets - cache first strategy
    if (isStaticAsset(url.pathname)) {
      return await cacheFirst(request, STATIC_CACHE);
    }

    // API routes - network first with short cache
    if (isApiRoute(url.pathname)) {
      return await networkFirst(request, DYNAMIC_CACHE, 300000); // 5 minutes
    }

    // Network-first routes (dynamic content)
    if (isNetworkFirstRoute(url.pathname)) {
      return await networkFirst(request, DYNAMIC_CACHE, 60000); // 1 minute
    }

    // Default: stale while revalidate for HTML pages
    return await staleWhileRevalidate(request, DYNAMIC_CACHE);
  } catch (error) {
    console.error("Service Worker: Fetch error", error);

    // Fallback to cache or offline page
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline fallback for HTML requests
    if (request.headers.get("accept")?.includes("text/html")) {
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
          headers: { "Content-Type": "text/html" },
        },
      );
    }

    return new Response("Offline", { status: 503 });
  }
}

// Cache first strategy - try cache, fallback to network
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    // Return cached version, but update cache in background
    updateCacheInBackground(request, cache);
    return cachedResponse;
  }

  const networkResponse = await fetch(request);

  if (networkResponse.ok) {
    cache.put(request, networkResponse.clone());
  }

  return networkResponse;
}

// Network first strategy - try network, fallback to cache
async function networkFirst(request, cacheName, maxAge = 300000) {
  const cache = await caches.open(cacheName);

  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Add timestamp to track freshness
      const responseWithTimestamp = new Response(networkResponse.body, {
        status: networkResponse.status,
        statusText: networkResponse.statusText,
        headers: {
          ...Object.fromEntries(networkResponse.headers.entries()),
          "sw-cache-timestamp": Date.now().toString(),
        },
      });

      cache.put(request, responseWithTimestamp.clone());
      return responseWithTimestamp;
    }
  } catch (error) {
    console.log("Service Worker: Network failed, trying cache");
  }

  // Network failed, try cache
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    const timestamp = cachedResponse.headers.get("sw-cache-timestamp");
    const age = timestamp ? Date.now() - parseInt(timestamp) : Infinity;

    if (age < maxAge) {
      return cachedResponse;
    }
  }

  throw new Error("Network failed and no valid cache available");
}

// Stale while revalidate - return cached version immediately, update in background
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);

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

  // Return cached version immediately if available
  if (cachedResponse) {
    return cachedResponse;
  }

  // No cache, wait for network
  return await networkUpdate;
}

// Update cache in background without blocking the response
function updateCacheInBackground(request, cache) {
  fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
    })
    .catch(() => {
      // Ignore network errors in background updates
    });
}

// Helper functions
function isStaticAsset(pathname) {
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
    );
  }
});

async function handleBackgroundSync() {
  // Implementation for handling offline actions
  console.log("Service Worker: Background sync triggered");

  // Example: retry failed API requests
  const cache = await caches.open(DYNAMIC_CACHE);
  const requests = await cache.keys();

  for (const request of requests) {
    if (request.url.includes("failed-request")) {
      try {
        await fetch(request);
        await cache.delete(request);
      } catch (error) {
        console.log("Service Worker: Retry failed for", request.url);
      }
    }
  }
}

// Push notification handling
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
    );
  }
});

// Notification click handling
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  if (event.action) {
    // Handle action clicks
    console.log("Service Worker: Notification action clicked", event.action);
  } else {
    // Handle notification click
    event.waitUntil(clients.openWindow(event.notification.data.url || "/"));
  }
});

// Performance monitoring
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
    }).catch(() => {
      // Ignore analytics errors
    });
  }
});
