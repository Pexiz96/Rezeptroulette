const CACHE="rezeptroulette-v3-2";
const SHELL=[
  "/",
  "/static/index-v3.html",
  "/static/v3.css",
  "/static/v3.js",
  "/static/manifest.json",
  "/static/images/Rezeptroulette.png"
];
const PRIVATE_PREFIXES=[
  "/auth/","/user-state","/profile/","/favorites","/ratings","/pantry","/at-home",
  "/eaten","/recipe-notes","/household","/wochenplan","/einkaufsliste","/food-rescue","/roulette"
];

self.addEventListener("install",event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting()));
});

self.addEventListener("activate",event=>{
  event.waitUntil(
    caches.keys()
      .then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key))))
      .then(()=>self.clients.claim())
  );
});

self.addEventListener("fetch",event=>{
  const request=event.request;
  if(request.method!=="GET")return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin)return;

  // Compatibility fix for the legacy frontend: imageUrl() currently prefixes
  // every non-http image with /static/images/. New curated recipes already use
  // /generated-images/<file>.jpg, which otherwise becomes the invalid path
  // /static/images//generated-images/<file>.jpg. Rewrite that request to the
  // real FastAPI image endpoint until the legacy frontend is retired.
  if(
    url.pathname.startsWith("/static/images//generated-images/") ||
    url.pathname.startsWith("/static/images/generated-images/")
  ){
    const marker="generated-images/";
    const filename=url.pathname.slice(url.pathname.indexOf(marker)+marker.length);
    const corrected=new URL(`/generated-images/${filename}`,self.location.origin);
    event.respondWith(fetch(corrected.toString(),{credentials:"same-origin"}));
    return;
  }

  // Personalized/account data is deliberately never cached. This prevents one
  // user's allergies, pantry, household or account data from being served stale
  // or exposed to a later session in the same browser cache.
  if(PRIVATE_PREFIXES.some(prefix=>url.pathname.startsWith(prefix)))return;

  if(url.pathname.startsWith("/static/")){
    event.respondWith(
      caches.match(request).then(cached=>{
        const network=fetch(request).then(response=>{
          if(response.ok)caches.open(CACHE).then(cache=>cache.put(request,response.clone()));
          return response;
        }).catch(()=>cached);
        return cached||network;
      })
    );
    return;
  }

  if(url.pathname==="/"){
    event.respondWith(
      fetch(request)
        .then(response=>response)
        .catch(()=>caches.match("/").then(cached=>cached||caches.match("/static/index-v3.html")))
    );
  }
});
