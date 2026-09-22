const CACHE = "chengyu-cards";
const ASSETS = ["./", "./index.html"];

self.addEventListener("install", function(e){
  e.waitUntil(
    caches.open(CACHE).then(function(c){ return c.addAll(ASSETS); })
      .then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.filter(function(k){ return k !== CACHE; })
                            .map(function(k){ return caches.delete(k); }));
    }).then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function(e){
  if (e.request.method !== "GET") return;
  e.respondWith(networkFirst(e.request));
});

function withTimeout(p, ms){
  return Promise.race([
    p,
    new Promise(function(_, reject){
      setTimeout(function(){ reject(new Error("timeout")); }, ms);
    })
  ]);
}

async function networkFirst(request){
  const cache = await caches.open(CACHE);
  try {
    const fresh = await withTimeout(fetch(request, { cache: "no-store" }), 4000);
    if (fresh && fresh.ok) { cache.put(request, fresh.clone()); }
    return fresh;
  } catch (err) {
    const cached = (await cache.match(request)) || (await cache.match("./index.html"));
    if (cached) return cached;
    throw err;
  }
}
