const CACHE = 'moex-v2';
const ASSETS = [
  'index.html',
  'js/moex.js',
  'js/indicators.js',
  'js/alerts.js',
  'vendor/lightweight-charts.standalone.production.js',
  'vendor/lightweight-charts-drawing.umd.js',
  'vendor/echarts.min.js',
  'vendor/split.min.js',
  'vendor/tabulator.min.js',
  'vendor/tabulator_midnight.min.css',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.hostname !== self.location.hostname) return;
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(resp => {
    if (resp.ok && e.request.method === 'GET') {
      const clone = resp.clone();
      caches.open(CACHE).then(c => c.put(e.request, clone));
    }
    return resp;
  })));
});
