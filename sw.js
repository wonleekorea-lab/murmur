/* アプリシェルのオフライン保持。データは localStorage 側にあり、ここでは扱わない。
 *
 * ページ本体（HTML）はネットワーク優先。キャッシュ優先にすると直したものが端末に届かず、
 * 古い <link rel="apple-touch-icon"> を掴み続ける事故が起きる。
 * 画像などファイル名が変わらないものだけキャッシュ優先にする。 */
var CACHE = 'journaling-v10';
var SHELL = ['./', './index.html', './manifest.json',
             './icon-180-v2.png', './icon-192-v2.png', './icon-512-v2.png'];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      return Promise.all(SHELL.map(function (u) {
        return fetch(u, { cache: 'reload' })
          .then(function (r) { return r.ok ? c.put(u, r) : null; })
          .catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) { return k === CACHE ? null : caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  // Claude API への呼び出しは絶対に触らない
  if (new URL(req.url).origin !== self.location.origin) return;

  var wantsHtml = req.mode === 'navigate' ||
                  (req.headers.get('accept') || '').indexOf('text/html') !== -1;

  if (wantsHtml) {
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () {
        return caches.match(req).then(function (hit) {
          return hit || caches.match('./index.html');
        });
      })
    );
    return;
  }

  e.respondWith(
    caches.match(req).then(function (hit) {
      if (hit) return hit;
      return fetch(req).then(function (res) {
        if (res && res.status === 200 && res.type === 'basic') {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      });
    })
  );
});
