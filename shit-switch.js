/* shit-switch.js — the universal "don't like this" overlay.
 *
 * Drop it into any HTML page with a single tag:
 *   <script defer src="shit-switch.js"></script>
 *   (or "../shit-switch.js" from a subfolder)
 *
 * Behaviour:
 *   - Injects a small round × button in the bottom-right of every page.
 *   - Tap it → "dislike mode" on. Crosshair cursor. Tap any element to mark it
 *     with a red translucent overlay, a pencil-streak diagonal, and a red ✕.
 *   - Tap the button again → mode off. Marks persist forever (localStorage).
 *   - Long-press a mark to remove it.
 *   - Tap-and-hold the switch (≥600ms) opens a tiny menu: Clear all / Export JSON.
 *
 * State lives per page under: hub.dislike.<location.pathname>
 * Nothing leaves the device. No network.
 */
(function () {
  'use strict';
  if (window.__shitSwitchLoaded) return;
  window.__shitSwitchLoaded = true;

  var KEY = 'hub.dislike.' + location.pathname;

  // ─── styles
  var css =
    '.__ss-btn{position:fixed;right:14px;bottom:14px;z-index:2147483640;' +
    'width:40px;height:40px;border-radius:50%;border:1.5px solid #e84c1e;' +
    'background:rgba(14,15,18,0.82);color:#e84c1e;font:700 18px/1 ' +
    'ui-monospace,Menlo,monospace;cursor:pointer;-webkit-tap-highlight-color:transparent;' +
    'display:flex;align-items:center;justify-content:center;backdrop-filter:blur(6px);' +
    'box-shadow:0 2px 8px rgba(0,0,0,0.4);transition:transform .12s,background .15s}' +
    '.__ss-btn:hover{background:#e84c1e;color:#fff}' +
    '.__ss-btn.on{background:#e84c1e;color:#fff;animation:__ss-pulse 1.4s infinite}' +
    '@keyframes __ss-pulse{0%{box-shadow:0 0 0 0 rgba(232,76,30,0.7)}' +
    '70%{box-shadow:0 0 0 10px rgba(232,76,30,0)}' +
    '100%{box-shadow:0 0 0 0 rgba(232,76,30,0)}}' +
    '.__ss-menu{position:fixed;right:14px;bottom:60px;z-index:2147483640;' +
    'background:rgba(14,15,18,0.92);border:1px solid #e84c1e;border-radius:8px;' +
    'padding:6px;display:none;flex-direction:column;gap:4px;backdrop-filter:blur(6px)}' +
    '.__ss-menu.on{display:flex}' +
    '.__ss-menu button{font:11px/1 ui-monospace,Menlo,monospace;letter-spacing:.1em;' +
    'text-transform:uppercase;background:transparent;color:#e8e6e0;border:0;' +
    'padding:8px 12px;cursor:pointer;text-align:left;border-radius:4px}' +
    '.__ss-menu button:hover{background:#e84c1e;color:#fff}' +
    '.__ss-hint{position:fixed;left:14px;bottom:14px;z-index:2147483640;' +
    'background:rgba(232,76,30,0.92);color:#fff;font:600 11px/1.4 ui-monospace,Menlo,monospace;' +
    'letter-spacing:.08em;padding:8px 12px;border-radius:6px;max-width:62vw;' +
    'pointer-events:none;transition:opacity .2s;opacity:0}' +
    '.__ss-hint.on{opacity:1}' +
    'body.__ss-picking,body.__ss-picking *{cursor:crosshair !important}' +
    '.__ss-mark{position:relative !important}' +
    '.__ss-mark::before{content:"";position:absolute;inset:0;background:rgba(232,76,30,0.35);' +
    'border:1.5px dashed #e84c1e;pointer-events:none;z-index:2147483600;border-radius:inherit}' +
    '.__ss-mark::after{content:"✕";position:absolute;top:-8px;right:-8px;' +
    'background:#e84c1e;color:#fff;width:18px;height:18px;border-radius:50%;' +
    'font:700 12px/18px ui-monospace,Menlo,monospace;text-align:center;' +
    'pointer-events:none;z-index:2147483601;box-shadow:0 1px 4px rgba(0,0,0,0.4)}' +
    // pencil streak: diagonal gradient overlay via background-image on a wrapper div
    '.__ss-streak{position:absolute;inset:0;pointer-events:none;z-index:2147483599;' +
    'background:repeating-linear-gradient(135deg,transparent 0 6px,rgba(232,76,30,0.18) 6px 8px);' +
    'border-radius:inherit}';
  var styleEl = document.createElement('style');
  styleEl.id = '__ss-style';
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  // ─── button + menu
  var btn = document.createElement('button');
  btn.className = '__ss-btn';
  btn.type = 'button';
  btn.setAttribute('aria-label', 'Dog-shit switch — mark things you don\'t like');
  btn.setAttribute('title', 'Tap to mark things · hold for menu');
  btn.textContent = '✕';
  document.body.appendChild(btn);

  var menu = document.createElement('div');
  menu.className = '__ss-menu';
  menu.innerHTML =
    '<button data-a="clear">Clear all on this page</button>' +
    '<button data-a="export">Export as JSON</button>' +
    '<button data-a="close">Close menu</button>';
  document.body.appendChild(menu);

  var hint = document.createElement('div');
  hint.className = '__ss-hint';
  document.body.appendChild(hint);

  // ─── state
  var picking = false;
  var holdTimer = null;

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; }
    catch (e) { return []; }
  }
  function save(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) {}
  }

  // Compute a reasonably stable selector for an element
  function selectorFor(el) {
    if (!el || el === document.body || el === document.documentElement) return '';
    if (el.id) return '#' + CSS.escape(el.id);
    var path = [];
    var node = el;
    while (node && node.nodeType === 1 && node !== document.body) {
      var part = node.tagName.toLowerCase();
      if (node.className && typeof node.className === 'string') {
        var c = node.className.trim().split(/\s+/).filter(function (x) {
          return x && x.indexOf('__ss-') !== 0;
        }).slice(0, 2).join('.');
        if (c) part += '.' + c;
      }
      var parent = node.parentNode;
      if (parent && parent.children) {
        var sibs = Array.prototype.filter.call(parent.children, function (n) {
          return n.tagName === node.tagName;
        });
        if (sibs.length > 1) {
          part += ':nth-of-type(' + (sibs.indexOf(node) + 1) + ')';
        }
      }
      path.unshift(part);
      if (path.length > 5) break;
      node = parent;
    }
    return path.join(' > ');
  }

  function findBySelector(sel) {
    if (!sel) return null;
    try { return document.querySelector(sel); } catch (e) { return null; }
  }

  function applyMark(el) {
    if (!el || el.classList.contains('__ss-mark')) return;
    el.classList.add('__ss-mark');
    var streak = document.createElement('div');
    streak.className = '__ss-streak';
    // only if el can contain absolute-positioned child
    var cs = getComputedStyle(el);
    if (cs.position === 'static') el.style.position = 'relative';
    el.appendChild(streak);

    // long-press to remove
    var pressTimer = null;
    el.addEventListener('pointerdown', function (e) {
      if (picking) return;
      pressTimer = setTimeout(function () {
        if (confirm('Remove this dislike mark?')) {
          removeMark(el);
        }
      }, 700);
    });
    el.addEventListener('pointerup', function () { clearTimeout(pressTimer); });
    el.addEventListener('pointerleave', function () { clearTimeout(pressTimer); });
  }

  function removeMark(el) {
    el.classList.remove('__ss-mark');
    var streak = el.querySelector(':scope > .__ss-streak');
    if (streak) streak.remove();
    var list = load().filter(function (sel) {
      return findBySelector(sel) !== el;
    });
    save(list);
  }

  // Restore existing marks on page load
  function restore() {
    var list = load();
    list.forEach(function (sel) {
      var el = findBySelector(sel);
      if (el) applyMark(el);
    });
  }

  function showHint(text, ms) {
    hint.textContent = text;
    hint.classList.add('on');
    setTimeout(function () { hint.classList.remove('on'); }, ms || 1800);
  }

  // ─── switch behaviour
  function togglePicking() {
    picking = !picking;
    btn.classList.toggle('on', picking);
    document.body.classList.toggle('__ss-picking', picking);
    showHint(picking
      ? 'Dislike mode ON — tap anything you don\'t like. Tap the button again to finish.'
      : 'Dislike mode OFF — marks saved.', 2400);
  }

  btn.addEventListener('click', function (e) {
    if (menu.classList.contains('on')) { menu.classList.remove('on'); return; }
    togglePicking();
  });
  btn.addEventListener('pointerdown', function () {
    clearTimeout(holdTimer);
    holdTimer = setTimeout(function () {
      menu.classList.add('on');
      // prevent the click event from toggling picking
      btn.dataset.menuOpened = '1';
      setTimeout(function () { delete btn.dataset.menuOpened; }, 50);
    }, 600);
  });
  btn.addEventListener('pointerup', function () { clearTimeout(holdTimer); });
  btn.addEventListener('pointerleave', function () { clearTimeout(holdTimer); });

  menu.addEventListener('click', function (e) {
    var a = e.target.dataset && e.target.dataset.a;
    if (!a) return;
    if (a === 'clear') {
      if (confirm('Clear every dislike mark on this page?')) {
        document.querySelectorAll('.__ss-mark').forEach(function (el) {
          el.classList.remove('__ss-mark');
          var streak = el.querySelector(':scope > .__ss-streak');
          if (streak) streak.remove();
        });
        save([]);
        showHint('Cleared.', 1200);
      }
    } else if (a === 'export') {
      var data = JSON.stringify({ page: location.pathname, marks: load() }, null, 2);
      navigator.clipboard.writeText(data).then(
        function () { showHint('Copied dislike JSON to clipboard.', 1800); },
        function () {
          var pre = window.prompt('Copy this:', data);
        }
      );
    }
    menu.classList.remove('on');
  });

  // ─── click-to-mark
  document.addEventListener('click', function (e) {
    if (!picking) return;
    var t = e.target;
    if (!t || t === btn || btn.contains(t) || menu.contains(t)) return;
    // don't mark structural wrappers — find smallest meaningful element
    e.preventDefault();
    e.stopPropagation();
    var sel = selectorFor(t);
    if (!sel) return;
    applyMark(t);
    var list = load();
    if (list.indexOf(sel) === -1) { list.push(sel); save(list); }
  }, true);

  // ─── kick it off
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', restore);
  } else {
    restore();
  }
})();
