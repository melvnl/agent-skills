# Web frontend performance

Framework-neutral first; framework notes at the end. Check the framework version before applying any framework-specific advice: caching and rendering defaults change between major versions.

## Measure

- **Field data decides**: Core Web Vitals at p75 per page type and device class, from RUM (`web-vitals` library, the framework's reporting hook, an analytics or APM RUM product) or CrUX. Lab tools (Lighthouse, DevTools, WebPageTest) diagnose; they don't prove user impact.
- Lab runs: production build, mobile emulation with CPU and network throttling, cold cache, several runs, median reported.
- INP needs real interactions; Lighthouse can't measure it. Use field data or a DevTools recording of the actual interaction, and look for long tasks (> 50 ms).

## LCP (largest contentful paint)

Break it into four parts and fix the largest:

| Part | Common cause | Fix |
|---|---|---|
| TTFB | slow server render, uncached data, redirects | backend fixes (`performance-engineering` main table), static or cached rendering, CDN |
| Resource load delay | LCP image found late (CSS background, JS-inserted, `loading="lazy"`) | put it in the HTML as `<img>`, never lazy-load it, `fetchpriority="high"` or the framework's priority flag, `preload` if it must come from CSS |
| Resource load duration | oversized image | responsive `srcset`/`sizes`, modern formats (AVIF/WebP), CDN image resizing |
| Render delay | render-blocking CSS/JS, client-only rendering, fonts | inline critical CSS, defer non-critical scripts, server-render the LCP element |

## INP (interaction to next paint)

- Long tasks on the main thread: large hydration, heavy event handlers, synchronous state updates re-rendering large trees, third-party scripts.
- Fixes: yield to the main thread (`scheduler.yield()` where supported, or `setTimeout`/`requestAnimationFrame` splitting), show feedback first and defer the expensive work, reduce re-render scope (memoization, smaller state, transitions), virtualize long lists, move work to a Web Worker, delay or remove third-party scripts.

## CLS (cumulative layout shift)

- Always reserve space: `width`/`height` or `aspect-ratio` on images, video and embeds; fixed slots for ads, banners, cookie notices and late-loading content.
- Fonts: `font-display: optional` or `swap` with size-adjusted fallbacks (framework font helpers do this); preload only the fonts above the fold.
- Don't insert content above existing content after load, except in response to a user action.

## JavaScript cost

- Measure with a bundle analyzer per route; budget first-load JS for key pages.
- Ship less: server-render or statically render what doesn't need interactivity; split by route and by interaction (`import()` on demand); remove heavy dependencies (date, lodash-style, icon packs imported whole); check for duplicated packages.
- Third-party scripts (tag managers, chat, analytics) load after interaction or idle, through the framework's script loader strategy, and each one has an owner and a reason.

## Caching and delivery

- Fingerprinted static assets: `Cache-Control: public, max-age=31536000, immutable`.
- HTML and data: explicit per page; anything user-specific (cart, account, customer-group prices) is `private` or `no-store`, never in a shared cache (`caching-and-coordination`).
- Compression (Brotli/gzip), HTTP/2 or 3, a CDN close to users, `preconnect` only to origins needed early.

## Server-rendering frameworks (Next.js and similar)

- **Server/client boundary**: keep components server-rendered by default; mark only interactive leaves as client components. A client directive high in the tree pulls every child into the JS bundle.
- **Data fetching**: fetch in parallel on the server (start independent requests together, then await), not in client `useEffect` chains that waterfall after hydration.
- **Streaming**: wrap slow sections in `Suspense` boundaries so the shell and LCP element render without waiting for them.
- **Caching and revalidation**: know the installed version's defaults. Next.js changed fetch and route caching defaults between major versions (13/14 cached by default; 15 made fetch uncached by default). State the intended mode per route (static, revalidate on an interval or tag, dynamic) and verify it in the build output.
- **Images, fonts, scripts**: use the framework's image component with real `sizes` and `priority` on the LCP image only; the font helper for self-hosted fonts with fallback metrics; the script component with a deferred strategy for third parties.
- **Middleware runs on every matched request**: keep it light and its matcher narrow.
- Check `next build` output (route types, first-load JS per route) before and after a change.
