# Do It — Project Lessons Learned

This is an ongoing single-file PWA (`index.html` + `sw.js` + `manifest.json`) hosted on GitHub Pages.
Before making changes, treat the following as standing rules derived from bugs we already hit and fixed.

---

## JavaScript & DOM

**Always place HTML elements before the `<script>` tag that references them.**
`document.getElementById()` returns `null` for elements that appear *after* the closing `</script>`.
A single null reference calling `.addEventListener()` throws a TypeError that silently kills all
remaining JS initialisation — nothing else in the script runs. Symptom: unrelated features
(add task, theme picker) stop working entirely.

**Wrap all `localStorage` calls in try-catch.**
Sandboxed iframes and certain browser contexts throw a `SecurityError` on any `localStorage` access.
Without the try-catch, `render()` never runs and the UI appears broken with no console error visible.

**Never use the `hidden` attribute for CSS accordion animations.**
`max-height` / `opacity` transitions don't animate on elements with `hidden` set.
Use `classList.toggle('open')` with a closed state of `max-height: 0; opacity: 0; pointer-events: none`
and an open state that sets real values.

---

## Web Audio API (Android / iOS)

**AudioContext starts suspended on mobile — always call `ctx.resume().then(doPlay)`.**
Never call oscillator methods directly. On Android and iOS the AudioContext is suspended until
a user gesture. Pattern:
```js
if (ctx.state === 'suspended') ctx.resume().then(doPlay);
else doPlay();
```

**Unlock AudioContext on first touch with a silent buffer.**
Add a one-time `touchstart` listener that creates and plays a zero-duration silent buffer.
Without this, `ctx.resume()` on the first real interaction may still fail on some Android devices.

---

## Service Worker & Caching

**Bump the `CACHE` constant in `sw.js` on every deploy, not just major changes.**
The SW uses cache-first — users never see new files unless the SW itself changes.
Always increment (e.g. `doit-v1` → `doit-v2`) and always push `sw.js` alongside
`index.html` in the same commit.

**GitHub Pages has CDN propagation lag (30–60 s).**
After `git push`, fetching from the server may still return the old file.
Wait ~60 s and test with a no-cache header before concluding a deploy failed.

**Renaming a file is the only reliable way to bust the browser icon cache.**
Chrome caches PWA icons aggressively. If an icon change doesn't appear, rename the file
(e.g. `icon.svg` → `icon2.svg`) and update all references in `manifest.json`.

---

## Mobile / PWA

**Set `font-size: 1rem` (16px minimum) on all `<input>` elements.**
iOS Safari auto-zooms the viewport when focusing an input with `font-size < 16px`.
This cannot be overridden with `touch-action` or viewport meta tags alone.

**Hover-only UI never works on touch screens. Use `@media (pointer: coarse)` instead.**
Any pattern like `.item:hover .button { opacity: 1 }` is invisible on mobile — hover doesn't exist.
For touch devices, always show action buttons at a resting opacity and full opacity when active.
Apply via `@media (pointer: coarse)`.

**Use `env(safe-area-inset-*)` for body and fixed-position bottom sheets.**
Without it, content underlaps the home indicator (iPhone) or navigation bar (Android).
Apply to `padding-bottom` on `body` and on every `position: fixed; bottom: 0` element:
```css
padding-bottom: calc(36px + env(safe-area-inset-bottom));
```

**Use `100dvh` not `100vh` for full-height layouts on mobile.**
`100vh` includes the browser chrome (address bar), causing overflow on mobile.
`100dvh` (dynamic viewport height) tracks the actual visible area.

**Add `-webkit-tap-highlight-color: transparent` to all interactive elements.**
Omitting it causes an ugly blue flash on every tap on Android/iOS.

**Self-signed HTTPS certificates do not create a WebAPK on Android.**
The PWA install prompt on Android only produces a proper standalone WebAPK (no address bar)
when served from a real trusted HTTPS origin. GitHub Pages provides this for free.
Local dev with a self-signed cert gives only a shortcut, not a true PWA install.

---

## Git & GitHub

**When pushing to a remote that already has unrelated commits, use:**
```
git pull origin main --allow-unrelated-histories -X ours
```
Then push normally. This happens when files were uploaded manually to GitHub before
`git init` was run locally.

**Windows: use `py` not `python` for the Python launcher.**
`python` on Windows 11 is a Microsoft Store stub that opens the Store instead of running Python.
The `py` launcher (`py server.py`, `py -m pip install ...`) always resolves correctly.
