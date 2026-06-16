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

**After a deploy, users may still see the old version — the SW is serving from cache.**
Bumping the cache version causes the new SW to activate and purge the old cache, but the
browser only checks for a new SW in the background. Until it does, the old files are served.
Fix for the user: DevTools → Application → Service Workers → Update → Skip Waiting → hard refresh.
Or: clear site data for the origin in browser settings. On Android, clear cached files in
Chrome Settings → Privacy → Clear browsing data.

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

---

## Desktop / Responsive Optimisation

**Gate every desktop rule behind `@media (min-width: …)` or `@media (pointer: fine)` — never assume screen size equals input type.**
A wide monitor can still be touch-only (Surface). `pointer: fine` targets mouse/trackpad; `pointer: coarse` targets touch. Use both independently.

**Bottom sheets feel wrong with a mouse — use centered dialogs on desktop.**
Override `position: fixed; bottom: 0; left: 0; right: 0; transform: translateY(100%)` with:
```css
@media (pointer: fine) {
  .sheet {
    top: 50%; left: 50%; right: auto; bottom: auto;
    max-width: 460px; width: calc(100% - 3rem);
    border-radius: 16px; border: 1.5px solid var(--border); border-top: none;
    transform: translate(-50%, -47%) scale(.97); opacity: 0;
    transition: transform .22s cubic-bezier(.4,0,.2,1), opacity .18s;
  }
  .sheet.open { transform: translate(-50%, -50%) scale(1); opacity: 1; }
}
```
The `.open` JS toggling logic is unchanged — only the visual differs.

**Two-column layouts need `align-items: start` or the shorter column stretches.**
`display: grid; grid-template-columns: 1fr 360px; align-items: start` keeps the sidebar its natural height. Without `align-items: start` both columns match the tallest one.

**Sticky sidebars need `max-height + overflow-y: auto` or they overflow the viewport.**
`position: sticky; top: 1.5rem; max-height: calc(100vh - 3rem); overflow-y: auto` lets the sidebar scroll independently if its content is taller than the screen.

**`opacity: 0` buttons are invisible on desktop too — use a faint resting state.**
Hover-reveal buttons (`opacity: 0` → `opacity: 1` on `:hover`) are the right default for mobile (always show via `pointer: coarse`) but on desktop a resting `opacity: 0.25` is better UX — users can see the affordance without the UI feeling cluttered. Override in `@media (pointer: fine)`.

**Auto-focus inputs on desktop, never on mobile.**
`taskInput.focus()` on mobile scrolls the page and opens the software keyboard unexpectedly.
Gate it: `if (window.matchMedia('(pointer: fine)').matches) input.focus();`

---

## Recurring / Weekly Features

**Match JS class names exactly to CSS — mismatches are silent rendering failures.**
When building JS that creates DOM elements, always read the CSS before choosing class names.
Two specific traps hit in this project:
- CSS had `.task-badge-repeat` / `.task-badge-alarm`; JS accidentally used `.badge-repeat` / `.badge-alarm` (missing `task-` prefix). The badges rendered but had no styles.
- CSS had `.day-pill.on` for the active/selected state; JS used `.day-pill.active`. Pills never turned accent-coloured.
Fix: grep the CSS for the exact selector before writing `element.className = ...` in JS.

**`capture: true` on delegated click handlers fires before lower listeners — use it for priority/date intercepts.**
When adding a second delegated click handler on the same element (`taskList`), the new one must use `addEventListener('click', fn, true)` (capture phase) or it may not fire if a child's handler calls `stopPropagation`. Safer than restructuring all existing event delegation.

**Use `div` not `span` for stacked text inside a flex column.**
`span` is `display: inline` by default, so `margin-top` has no effect and two sibling spans run together on one line.
Using `div` (or adding `display: block` in CSS) is needed when you want the title and subtitle to stack vertically inside a flex container.

**`Notification.requestPermission()` should be deferred to DOMContentLoaded.**
Calling it at parse time does nothing useful — browsers require a user gesture or a loaded document context.
Always call it inside the `DOMContentLoaded` listener and only request if `Notification.permission === 'default'`.

**Schedule midnight respawn with recursive `setTimeout`, not `setInterval`.**
`setInterval(fn, 86_400_000)` drifts because it counts from when the page loaded, not from midnight.
A recursive `setTimeout` that calculates exact ms to the next `00:00:05` always fires at the right wall-clock time:
```js
function scheduleMidnightRespawn() {
  const next = new Date(); next.setHours(24, 0, 5, 0);
  setTimeout(() => { spawnRecurringTasks(); scheduleAlarms(); render(); scheduleMidnightRespawn(); }, next - Date.now());
}
```
