const CACHE="rezeptroulette-v3-3";
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

  // Legacy frontend compatibility: generated recipe images already carry a
  // root-relative URL, but older UI code prefixes /static/images/ again.
  if(
    url.pathname.startsWith("/static/images//generated-images/") ||
    url.pathname.startsWith("/static/images/generated-images/")
  ){
    const marker="generated-images/";
    const filename=url.pathname.slice(url.pathname.indexOf(marker)+marker.length);
    event.respondWith(fetch(`/generated-images/${filename}`,{credentials:"same-origin",cache:"no-store"}));
    return;
  }

  // Imported PDF recipes historically live in /bilder while the legacy UI
  // requests their bare filename below /static/images. Route those requests to
  // the real repository location instead of returning a broken image.
  if(url.pathname.startsWith("/static/images/")){
    let filename=url.pathname.slice("/static/images/".length).replace(/^\/+/,"");

    if(filename.startsWith("bilder/")){
      filename=filename.slice("bilder/".length);
      event.respondWith(fetch(`/bilder/${filename}`,{credentials:"same-origin",cache:"no-store"}));
      return;
    }

    if(filename.startsWith("pdf_")){
      event.respondWith(fetch(`/bilder/${filename}`,{credentials:"same-origin",cache:"no-store"}));
      return;
    }
  }

  // Personalized/account data is deliberately never cached.
  if(PRIVATE_PREFIXES.some(prefix=>url.pathname.startsWith(prefix)))return;

  // Recipe image requests should prefer the network so replaced higher-quality
  // images become visible immediately after a deployment.
  if(url.pathname.startsWith("/generated-images/")||url.pathname.startsWith("/bilder/")){
    event.respondWith(fetch(request,{cache:"no-store"}).catch(()=>caches.match(request)));
    return;
  }

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
