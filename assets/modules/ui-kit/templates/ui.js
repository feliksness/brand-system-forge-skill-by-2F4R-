/* ==========================================================================
   {{BRAND_NAME}} — {{p}}-ui.js · accessible behaviours for {{p}}-ui.css
   Classic script, no dependencies, works from file:// and any server.
     <script src="…/SOURCE/JS/{{p}}-icons.js"></script>   (optional — {{G}}.icon)
     <script src="…/SOURCE/JS/{{p}}-ui.js"></script>
   Auto-initialises on DOMContentLoaded; call {{G}}.ui.init(root) after inserting markup.
   Declarative hooks (WAI-ARIA Authoring Practices):
     [data-{{p}}-icon="name"] [data-{{p}}-ui-icon]  fills the span with an icon (brand set first, built-in fallback)
     [data-{{p}}-theme-switch] (radio group)    light / dark / contrast / auto, persisted (localStorage, try/catch)
     [data-{{p}}-theme-toggle]                  button cycling light → dark → contrast
     [data-{{p}}-menu-toggle][aria-controls]    mobile menu: focus trap, Esc, inert page, scroll lock, focus return
     [data-{{p}}-tabs] (="manual")              tabs: ← → (↑ ↓ vertical) Home End, roving tabindex
     [data-{{p}}-accordion] (="single")         disclosure buttons; ↑ ↓ Home End between headers
     [data-{{p}}-modal-open="id"]               <dialog class="{{p}}-modal|{{p}}-drawer">: focus trap, Esc, backdrop, focus return
     [data-{{p}}-modal-close]                   closes the enclosing dialog
     [data-{{p}}-tooltip="id"]                  tooltip on hover + focus, Esc dismisses, hoverable (WCAG 1.4.13)
     [data-{{p}}-popover="id"]                  click toggles, Esc / outside click closes, focus returns
     [data-{{p}}-dismiss]                       hides the enclosing .{{p}}-alert / .{{p}}-banner / [data-{{p}}-dismissible]
     [data-{{p}}-toast='{"title":"…","tone":"success"}']   button that shows a toast
     form[data-{{p}}-validate]                  inline messages + error summary + focus management
     [data-{{p}}-count] (textarea/input)        live character counter (.{{p}}-field__count)
     table[data-{{p}}-sort]                     sortable columns (th > .{{p}}-table__sort), aria-sort
     [data-{{p}}-file]                          drop zone: file list, drag & drop
     [data-{{p}}-range]                         range fill + <output> sync
     [data-{{p}}-search]                        clear button for search inputs
     [data-{{p}}-header]                        sticky header condenses on scroll
     [data-{{p}}-copy="#target"]                copies the target's text
   JS API: {{G}}.ui.theme.set('dark') · {{G}}.ui.toast({title, text, tone, timeout}) · {{G}}.ui.modal.open(id) ·
           {{G}}.ui.menu.open(id) · {{G}}.ui.tabs.select(tab) · {{G}}.ui.accordion.toggle(trigger) · {{G}}.ui.icon(name, {size, label})
   ========================================================================== */
(function (global) {
  'use strict';
  var doc = global.document;
  var NS = global.{{G}} = global.{{G}} || {};
  var UI = NS.ui = NS.ui || {};
  var P = '{{p}}';
  var FALLBACK_ICONS = {{ICONS_JSON}};
  var ICON_ALIASES = {{ICON_ALIASES}};
  var FOCUSABLE = 'a[href], area[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), iframe, [tabindex]:not([tabindex="-1"]), [contenteditable="true"], audio[controls], video[controls], summary';

  /* ------------------------------------------------------------------ utils */
  function $$(sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); }
  function on(el, type, fn, opts) { el.addEventListener(type, fn, opts || false); return function () { el.removeEventListener(type, fn, opts || false); }; }
  var uidN = 0;
  function uid(p) { uidN += 1; return (p || P) + '-' + uidN + '-' + Math.random().toString(36).slice(2, 6); }
  function ensureId(el, p) { if (!el.id) el.id = uid(p); return el.id; }
  function reduced() { return !!(global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches); }
  function visible(el) { if (!el.getClientRects().length) return false; var cs = global.getComputedStyle(el); return cs.visibility !== 'hidden' && cs.display !== 'none'; }
  function focusables(root) { return $$(FOCUSABLE, root).filter(function (el) { return !el.closest('[inert]') && !el.closest('[hidden]') && visible(el); }); }
  function emit(el, name, detail) { var ev; try { ev = new CustomEvent(name, { bubbles: true, detail: detail || {} }); } catch (e) { ev = doc.createEvent('CustomEvent'); ev.initCustomEvent(name, true, false, detail || {}); } el.dispatchEvent(ev); }
  function once(el, key) { var k = 'pui' + key; if (el.dataset[k]) return false; el.dataset[k] = '1'; return true; }
  function cssMs(name, fb) { var v = global.getComputedStyle(doc.documentElement).getPropertyValue(name).trim(); if (!v) return fb; var n = parseFloat(v); return /ms$/.test(v) ? n : (/s$/.test(v) ? n * 1000 : fb); }
  function store(key, val) { try { if (val === undefined) return global.localStorage.getItem(key); if (val === null) global.localStorage.removeItem(key); else global.localStorage.setItem(key, val); } catch (e) { /* private mode / blocked storage */ } return null; }
  function attr(name) { return 'data-' + P + '-' + name; }
  function q(name) { return '[' + attr(name) + ']'; }

  /* ------------------------------------------------------------------ icons */
  // Prefers the brand icon set ({{G}}.icon from {{p}}-icons.js); falls back to a small built-in set.
  UI.icon = function (name, o) {
    o = o || {}; var size = o.size || 24, svg = '';
    if (typeof NS.icon === 'function' && NS.icon !== UI.icon) {
      var names = [name].concat(ICON_ALIASES[name] || []), canResolve = NS.icons && typeof NS.icons.resolve === 'function';
      for (var i = 0; i < names.length && !svg; i++) {
        if (canResolve && !NS.icons.resolve(names[i])) continue;          // ask first: unknown names would log warnings
        try { var r = NS.icon(names[i], { size: size, label: o.label }); if (r && r.outerHTML) r = r.outerHTML; if (typeof r === 'string' && r.indexOf('<svg') > -1) svg = r; } catch (e) { /* unknown name */ }
      }
    }
    if (!svg) {
      var body = FALLBACK_ICONS[name] || FALLBACK_ICONS.dot;
      svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + size + '" height="' + size + '" fill="none" stroke="currentColor" stroke-width="{{STROKE_W}}" stroke-linecap="{{STROKE_CAP}}" stroke-linejoin="{{STROKE_JOIN}}"' +
        (o.label ? ' role="img" aria-label="' + String(o.label).replace(/"/g, '&quot;') + '"' : ' aria-hidden="true" focusable="false"') + '>' + body + '</svg>';
    }
    return svg;
  };
  function fillIcons(root) {
    $$(q('icon') + ',' + q('ui-icon'), root).forEach(function (el) {
      var name = el.getAttribute(attr('icon')) || el.getAttribute(attr('ui-icon'));
      if (el.firstElementChild && el.getAttribute('data-' + P + '-icon-done') === name) return;
      el.innerHTML = UI.icon(name, { size: 24, label: el.getAttribute('aria-label') && el.getAttribute('role') === 'img' ? el.getAttribute('aria-label') : '' });
      el.setAttribute('data-' + P + '-icon-done', name);
    });
  }
  function iconSpan(name) {
    var s = doc.createElement('span'), known = NS.icons && typeof NS.icons.resolve === 'function' && NS.icons.resolve(name);
    s.className = P + '-icon'; s.setAttribute(known ? attr('icon') : attr('ui-icon'), name); s.setAttribute('aria-hidden', 'true');
    s.innerHTML = UI.icon(name); s.setAttribute('data-' + P + '-icon-done', name); return s;
  }

  /* ------------------------------------------------------------- focus trap */
  UI.trapFocus = function (container) {
    return on(container, 'keydown', function (e) {
      if (e.key !== 'Tab') return;
      var f = focusables(container); if (!f.length) { e.preventDefault(); return; }
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && (doc.activeElement === first || !container.contains(doc.activeElement))) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && doc.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  };
  function inertOutside(keep) {
    var changed = [], node = keep;
    while (node && node.parentNode && node !== doc.body) {
      Array.prototype.forEach.call(node.parentNode.children, function (sib) {
        if (sib !== node && !sib.hasAttribute('inert') && !/^(SCRIPT|STYLE|LINK|TEMPLATE)$/.test(sib.tagName) && !sib.classList.contains(P + '-toaster')) { sib.setAttribute('inert', ''); changed.push(sib); }
      });
      node = node.parentNode;
    }
    return function () { changed.forEach(function (el) { el.removeAttribute('inert'); }); };
  }
  function lockScroll(lock) { doc.body.classList.toggle(P + '-scroll-lock', !!lock); }

  /* ================================================================= THEME */
  var THEMES = ['auto', 'light', 'dark', 'contrast'];
  UI.theme = {
    key: P + '-theme',
    get: function () { var t = doc.documentElement.getAttribute('data-theme'); return THEMES.indexOf(t) > 0 ? t : 'auto'; },
    effective: function () {
      var t = UI.theme.get(); if (t !== 'auto') return t;
      if (global.matchMedia && global.matchMedia('(prefers-contrast: more)').matches) return 'contrast';
      return global.matchMedia && global.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    },
    set: function (theme, opts) {
      if (THEMES.indexOf(theme) < 0) theme = 'auto';
      if (theme === 'auto') doc.documentElement.removeAttribute('data-theme'); else doc.documentElement.setAttribute('data-theme', theme);
      if (!opts || opts.persist !== false) store(UI.theme.key, theme === 'auto' ? null : theme);
      UI.theme.syncScopes(); UI.theme.syncControls();
      emit(doc.documentElement, P + ':theme', { theme: theme, effective: UI.theme.effective() });
    },
    // Nested scopes (e.g. a dark footer) follow the high-contrast theme so contrast is never lost
    syncScopes: function () {
      var contrast = UI.theme.effective() === 'contrast';
      $$('[data-theme]:not(html), [' + attr('theme-origin') + ']').forEach(function (el) {
        if (el.hasAttribute(attr('theme-fixed'))) return;
        var origin = el.getAttribute(attr('theme-origin'));
        if (contrast) { if (origin == null) el.setAttribute(attr('theme-origin'), el.getAttribute('data-theme') || ''); el.setAttribute('data-theme', 'contrast'); }
        else if (origin != null) { if (origin) el.setAttribute('data-theme', origin); else el.removeAttribute('data-theme'); el.removeAttribute(attr('theme-origin')); }
      });
    },
    syncControls: function () {
      var t = UI.theme.get();
      $$(q('theme-switch') + ' input[type="radio"]').forEach(function (r) { r.checked = (r.value === t); });
      $$(q('theme-toggle')).forEach(function (b) { b.setAttribute('aria-label', (b.getAttribute(attr('label')) || 'Theme') + ': ' + UI.theme.effective()); });
    }
  };
  (function () {   // apply before first paint as far as possible: URL ?theme= (previews) > saved choice
    var m = /[?&#]theme=(light|dark|contrast|auto)/.exec(global.location ? global.location.search + global.location.hash : '');
    var saved = m ? m[1] : store(UI.theme.key);
    if (saved && THEMES.indexOf(saved) > 0) doc.documentElement.setAttribute('data-theme', saved);
    else if (saved === 'auto') doc.documentElement.removeAttribute('data-theme');
  })();
  function initThemeSwitch(group) {
    if (!once(group, 'Theme')) return;
    $$('input[type="radio"]', group).forEach(function (r) { r.checked = (r.value === UI.theme.get()); on(r, 'change', function () { if (r.checked) UI.theme.set(r.value); }); });
  }
  function initThemeToggle(btn) {
    if (!once(btn, 'ThemeT')) return;
    on(btn, 'click', function () { var order = ['light', 'dark', 'contrast']; var i = order.indexOf(UI.theme.effective()); UI.theme.set(order[(i + 1) % order.length]); });
  }

  /* ================================================================ HEADER */
  function initHeader(h) {
    if (!once(h, 'Header')) return;
    var ticking = false, at = parseInt(h.getAttribute(attr('condense-at')) || '16', 10);
    var upd = function () { ticking = false; h.classList.toggle('is-condensed', (global.pageYOffset || doc.documentElement.scrollTop) > at); };
    on(global, 'scroll', function () { if (!ticking) { ticking = true; global.requestAnimationFrame(upd); } }, { passive: true }); upd();
  }

  /* =========================================================== MOBILE MENU */
  UI.menu = {
    open: function (menu, toggle) {
      if (typeof menu === 'string') menu = doc.getElementById(menu);
      if (!menu || menu._pMenu) return;
      var st = menu._pMenu = { toggle: toggle || doc.querySelector(q('menu-toggle') + '[aria-controls="' + menu.id + '"]'), last: doc.activeElement };
      menu.hidden = false; menu.classList.add('is-open');
      if (st.toggle) st.toggle.setAttribute('aria-expanded', 'true');
      st.unInert = inertOutside(menu); lockScroll(true); st.offTrap = UI.trapFocus(menu);
      st.offKey = on(doc, 'keydown', function (e) { if (e.key === 'Escape') { e.preventDefault(); UI.menu.close(menu); } });
      st.offClick = on(menu, 'click', function (e) {
        if (e.target === menu) { UI.menu.close(menu); return; }                                  // scrim
        var a = e.target.closest('a[href]'); if (a) UI.menu.close(menu, { restoreFocus: false });
      });
      var target = menu.querySelector('[autofocus]') || menu.querySelector(q('menu-close')) || focusables(menu)[0];
      if (target) global.setTimeout(function () { target.focus(); }, 30);
      emit(menu, P + ':menu', { open: true });
    },
    close: function (menu, opts) {
      if (typeof menu === 'string') menu = doc.getElementById(menu);
      if (!menu || !menu._pMenu) return;
      var st = menu._pMenu; menu._pMenu = null;
      st.offKey(); st.offClick(); st.offTrap(); st.unInert(); lockScroll(false);
      if (st.toggle) st.toggle.setAttribute('aria-expanded', 'false');
      menu.classList.remove('is-open'); menu.hidden = true;
      if (!opts || opts.restoreFocus !== false) { var back = st.toggle || st.last; if (back && back.focus) back.focus(); }
      emit(menu, P + ':menu', { open: false });
    },
    toggle: function (menu, toggle) { if (typeof menu === 'string') menu = doc.getElementById(menu); if (!menu) return; if (menu._pMenu) UI.menu.close(menu); else UI.menu.open(menu, toggle); }
  };
  function initMenuToggle(btn) {
    if (!once(btn, 'Menu')) return;
    var id = btn.getAttribute('aria-controls'), menu = doc.getElementById(id);
    btn.setAttribute('aria-expanded', 'false');
    on(btn, 'click', function () { UI.menu.toggle(id, btn); });
    if (menu) $$(q('menu-close'), menu).forEach(function (c) { if (once(c, 'MenuC')) on(c, 'click', function () { UI.menu.close(menu); }); });
  }

  /* ================================================================== TABS */
  UI.tabs = {
    select: function (tab, focus) {
      var list = tab.closest('[role="tablist"]'); if (!list) return;
      $$('[role="tab"]', list).forEach(function (t) {
        var sel = t === tab, panel = doc.getElementById(t.getAttribute('aria-controls'));
        t.setAttribute('aria-selected', String(sel)); t.tabIndex = sel ? 0 : -1;
        if (panel) panel.hidden = !sel;
      });
      if (focus) tab.focus();
      emit(tab, P + ':tab', { tab: tab });
    }
  };
  function initTabs(root) {
    if (!once(root, 'Tabs')) return;
    var list = root.querySelector('[role="tablist"]'); if (!list) return;
    var manual = root.getAttribute(attr('tabs')) === 'manual', vertical = list.getAttribute('aria-orientation') === 'vertical';
    var tabs = $$('[role="tab"]', list);
    tabs.forEach(function (t) { var panel = doc.getElementById(t.getAttribute('aria-controls')); if (panel) { panel.setAttribute('role', 'tabpanel'); panel.setAttribute('aria-labelledby', ensureId(t, 'tab')); if (!panel.hasAttribute('tabindex')) panel.tabIndex = 0; } });
    var cur = tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0] || tabs[0];
    if (cur) UI.tabs.select(cur, false);
    on(list, 'click', function (e) { var t = e.target.closest('[role="tab"]'); if (t && list.contains(t)) UI.tabs.select(t, true); });
    on(list, 'keydown', function (e) {
      var i = tabs.indexOf(doc.activeElement); if (i < 0) return;
      var next = { ArrowRight: !vertical ? 1 : 0, ArrowLeft: !vertical ? -1 : 0, ArrowDown: vertical ? 1 : 0, ArrowUp: vertical ? -1 : 0 }[e.key];
      var j = null;
      if (next) j = (i + next + tabs.length) % tabs.length; else if (e.key === 'Home') j = 0; else if (e.key === 'End') j = tabs.length - 1;
      else if (manual && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); UI.tabs.select(tabs[i], true); return; }
      if (j === null) return;
      e.preventDefault();
      if (manual) tabs[j].focus(); else UI.tabs.select(tabs[j], true);
    });
  }

  /* ============================================================= ACCORDION */
  UI.accordion = {
    toggle: function (trigger, force) {
      var open = force == null ? trigger.getAttribute('aria-expanded') !== 'true' : !!force;
      var root = trigger.closest(q('accordion'));
      if (open && root && root.getAttribute(attr('accordion')) === 'single') {
        $$('[aria-expanded="true"]', root).forEach(function (o) { if (o !== trigger && o.closest(q('accordion')) === root) UI.accordion.toggle(o, false); });
      }
      trigger.setAttribute('aria-expanded', String(open));
      var panel = doc.getElementById(trigger.getAttribute('aria-controls')); if (panel) panel.hidden = !open;
      emit(trigger, P + ':accordion', { open: open });
    }
  };
  function initAccordion(root) {
    if (!once(root, 'Acc')) return;
    var triggers = $$('.' + P + '-accordion__trigger', root).filter(function (t) { return t.closest(q('accordion')) === root; });
    triggers.forEach(function (t) {
      var panel = doc.getElementById(t.getAttribute('aria-controls'));
      if (panel) { panel.setAttribute('role', 'region'); panel.setAttribute('aria-labelledby', ensureId(t, 'acc')); panel.hidden = t.getAttribute('aria-expanded') !== 'true'; }
      on(t, 'click', function () { UI.accordion.toggle(t); });
      on(t, 'keydown', function (e) {
        var i = triggers.indexOf(t), j = null;
        if (e.key === 'ArrowDown') j = (i + 1) % triggers.length; else if (e.key === 'ArrowUp') j = (i - 1 + triggers.length) % triggers.length;
        else if (e.key === 'Home') j = 0; else if (e.key === 'End') j = triggers.length - 1;
        if (j !== null) { e.preventDefault(); triggers[j].focus(); }
      });
    });
  }

  /* ========================================================= MODAL · DRAWER */
  UI.modal = {
    open: function (dialog, opener) {
      if (typeof dialog === 'string') dialog = doc.getElementById(dialog);
      if (!dialog || dialog._pModal) return;
      var st = dialog._pModal = { opener: opener || doc.activeElement };
      if (typeof dialog.showModal === 'function') dialog.showModal(); else { dialog.setAttribute('open', ''); st.unInert = inertOutside(dialog); }
      lockScroll(true); st.offTrap = UI.trapFocus(dialog);
      var target = dialog.querySelector('[autofocus]') || focusables(dialog.querySelector('.' + P + '-modal__body') || dialog)[0] || dialog.querySelector(q('modal-close')) || focusables(dialog)[0];
      if (target) target.focus();
      emit(dialog, P + ':modal', { open: true });
    },
    close: function (dialog, value) {
      if (typeof dialog === 'string') dialog = doc.getElementById(dialog);
      if (!dialog || !dialog._pModal) return;
      var st = dialog._pModal; dialog._pModal = null; st.offTrap();
      var done = function () {
        dialog.classList.remove('is-closing');
        if (typeof dialog.close === 'function' && dialog.open) dialog.close(value || ''); else dialog.removeAttribute('open');
        if (st.unInert) st.unInert(); lockScroll(false);
        if (st.opener && st.opener.focus) st.opener.focus();
        emit(dialog, P + ':modal', { open: false, value: value || '' });
      };
      if (reduced()) done(); else { dialog.classList.add('is-closing'); global.setTimeout(done, cssMs('--duration-fast', 160)); }
    }
  };
  function initModal(dialog) {
    if (!once(dialog, 'Modal')) return;
    on(dialog, 'cancel', function (e) { e.preventDefault(); UI.modal.close(dialog); });                                  // Esc (native)
    on(dialog, 'keydown', function (e) { if (e.key === 'Escape' && typeof dialog.showModal !== 'function') { e.preventDefault(); UI.modal.close(dialog); } });
    on(dialog, 'click', function (e) {
      var c = e.target.closest(q('modal-close')); if (c) { UI.modal.close(dialog, c.value || ''); return; }
      if (e.target === dialog && dialog.getAttribute(attr('dismissible')) !== 'false') UI.modal.close(dialog);   // backdrop
    });
  }
  function initModalOpener(btn) {
    if (!once(btn, 'ModalO')) return;
    btn.setAttribute('aria-haspopup', 'dialog');
    on(btn, 'click', function (e) { e.preventDefault(); UI.modal.open(btn.getAttribute(attr('modal-open')), btn); });
  }

  /* =============================================================== TOOLTIP */
  var openTip = null;
  function placeFloating(trigger, el, gap) {
    var r = trigger.getBoundingClientRect(), w = el.offsetWidth, h = el.offsetHeight, vw = doc.documentElement.clientWidth;
    var top = r.top - h - (gap || 10), place = 'top';
    if (top < 8) { top = r.bottom + (gap || 10); place = 'bottom'; }
    var left = Math.max(8, Math.min(vw - w - 8, r.left + r.width / 2 - w / 2));
    el.style.top = top + 'px'; el.style.left = left + 'px'; el.setAttribute('data-placement', place);
  }
  function showTip(trigger, tip) { if (openTip && openTip.tip !== tip) hideTip(true); global.clearTimeout(tip._pHide); tip.hidden = false; placeFloating(trigger, tip); openTip = { trigger: trigger, tip: tip }; }
  function hideTip(now) {
    if (!openTip) return; var t = openTip;
    var go = function () { t.tip.hidden = true; if (openTip === t) openTip = null; };
    if (now) go(); else t.tip._pHide = global.setTimeout(go, 120);
  }
  function initTooltip(trigger) {
    if (!once(trigger, 'Tip')) return;
    var tip = doc.getElementById(trigger.getAttribute(attr('tooltip'))); if (!tip) return;
    tip.setAttribute('role', 'tooltip'); if (!tip.classList.contains(P + '-tooltip--static')) tip.hidden = true;
    var ids = (trigger.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
    if (ids.indexOf(tip.id) < 0) { ids.push(tip.id); trigger.setAttribute('aria-describedby', ids.join(' ')); }
    on(trigger, 'pointerenter', function () { showTip(trigger, tip); });
    on(trigger, 'pointerleave', function () { hideTip(false); });
    on(trigger, 'focus', function () { showTip(trigger, tip); });
    on(trigger, 'blur', function () { hideTip(true); });
    on(tip, 'pointerenter', function () { global.clearTimeout(tip._pHide); });
    on(tip, 'pointerleave', function () { hideTip(false); });
  }
  on(doc, 'keydown', function (e) { if (e.key === 'Escape' && openTip) hideTip(true); });

  /* =============================================================== POPOVER */
  var openPop = null;
  function closePop(restore) {
    if (!openPop) return; var p = openPop; openPop = null;
    p.pop.hidden = true; p.btn.setAttribute('aria-expanded', 'false'); p.off.forEach(function (f) { f(); });
    if (restore) p.btn.focus();
  }
  function initPopover(btn) {
    if (!once(btn, 'Pop')) return;
    var pop = doc.getElementById(btn.getAttribute(attr('popover'))); if (!pop) return;
    btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-controls', pop.id); pop.hidden = true;
    on(btn, 'click', function () {
      if (openPop && openPop.pop === pop) { closePop(false); return; }
      closePop(false); pop.hidden = false; btn.setAttribute('aria-expanded', 'true');
      var st = openPop = { btn: btn, pop: pop, off: [] };
      st.off.push(on(doc, 'keydown', function (e) { if (e.key === 'Escape') { e.preventDefault(); closePop(true); } }));
      st.off.push(on(doc, 'pointerdown', function (e) { if (!pop.contains(e.target) && !btn.contains(e.target)) closePop(false); }));
      var f = focusables(pop)[0]; if (f) f.focus();
    });
  }

  /* ========================================================== ALERTS · TOASTS */
  function initDismiss(btn) {
    if (!once(btn, 'Dismiss')) return;
    on(btn, 'click', function () {
      var box = btn.closest('.' + P + '-alert, .' + P + '-banner, ' + q('dismissible')); if (!box) return;
      var next = box.nextElementSibling; box.hidden = true; emit(box, P + ':dismiss', {});
      var f = next ? focusables(next)[0] : null; if (f) f.focus();
    });
  }
  function toaster() {
    var t = doc.querySelector('.' + P + '-toaster:not(.' + P + '-toaster--static)');
    if (!t) { t = doc.createElement('ol'); t.className = P + '-toaster'; t.setAttribute('aria-label', 'Notifications'); doc.body.appendChild(t); }
    if (!t.hasAttribute('aria-live')) { t.setAttribute('aria-live', 'polite'); t.setAttribute('aria-relevant', 'additions'); }
    return t;
  }
  UI.toast = function (o) {
    o = o || {}; var tone = o.tone || 'info', host = toaster(), li = doc.createElement('li');
    var timeout = o.timeout == null ? 6000 : o.timeout;
    li.className = P + '-toast ' + P + '-toast--' + tone;
    if (tone === 'error') li.setAttribute('role', 'alert');
    var icon = { info: 'info', success: 'check', warning: 'warning', error: 'error' }[tone] || 'info';
    li.innerHTML = '<span class="' + P + '-toast__icon"></span><div class="' + P + '-toast__body"><p class="' + P + '-toast__title"></p>' + (o.text ? '<p class="' + P + '-toast__text"></p>' : '') + '</div>' +
      '<button type="button" class="' + P + '-close" aria-label="' + (o.closeLabel || 'Dismiss') + '"></button>' + (timeout ? '<span class="' + P + '-toast__timer" aria-hidden="true"></span>' : '');
    li.querySelector('.' + P + '-toast__icon').appendChild(iconSpan(icon));
    li.querySelector('.' + P + '-close').appendChild(iconSpan('close'));
    li.querySelector('.' + P + '-toast__title').textContent = o.title || '';
    if (o.text) li.querySelector('.' + P + '-toast__text').textContent = o.text;
    if (timeout) li.querySelector('.' + P + '-toast__timer').style.setProperty('--_t', timeout + 'ms');
    var remove = function () { if (!li.parentNode) return; li.classList.add('is-leaving'); global.setTimeout(function () { if (li.parentNode) li.parentNode.removeChild(li); }, reduced() ? 0 : cssMs('--duration-fast', 160)); };
    li.querySelector('.' + P + '-close').addEventListener('click', remove);
    host.appendChild(li);
    if (timeout) {
      var left = timeout, started = Date.now(), timer = global.setTimeout(remove, left);
      var pause = function () { global.clearTimeout(timer); left -= Date.now() - started; };
      var resume = function () { started = Date.now(); timer = global.setTimeout(remove, Math.max(1200, left)); };
      li.addEventListener('pointerenter', pause); li.addEventListener('pointerleave', resume);
      li.addEventListener('focusin', pause); li.addEventListener('focusout', resume);
    }
    return li;
  };
  function initToastBtn(btn) {
    if (!once(btn, 'Toast')) return;
    on(btn, 'click', function () { var o = {}; try { o = JSON.parse(btn.getAttribute(attr('toast')) || '{}'); } catch (e) { o = { title: btn.getAttribute(attr('toast')) }; } UI.toast(o); });
  }

  /* ============================================================ VALIDATION */
  function fieldOf(el) { return el.closest('.' + P + '-field, .' + P + '-fieldset, .' + P + '-check, .' + P + '-switch') || el.parentNode; }
  function labelOf(el) {
    var l = el.id ? doc.querySelector('label[for="' + el.id + '"]') : null;
    if (!l) { var fs = el.closest('fieldset'); l = fs ? fs.querySelector('legend') : el.closest('label'); }
    return l ? (l.getAttribute('data-' + P + '-name') || l.firstChild && l.firstChild.textContent || l.textContent).trim().replace(/\s+/g, ' ') : (el.name || 'Field');
  }
  function messageFor(el) {
    var v = el.validity, d = el.dataset;
    if (v.valueMissing) return d.msgRequired || (el.type === 'checkbox' ? 'Tick this box to continue' : 'Enter ' + labelOf(el).toLowerCase());
    if (v.typeMismatch) return d.msgType || (el.type === 'email' ? 'Enter an email address like name@example.com' : 'Check the format');
    if (v.tooShort) return d.msgShort || ('Use at least ' + el.minLength + ' characters');
    if (v.tooLong) return d.msgLong || ('Use ' + el.maxLength + ' characters or fewer');
    if (v.patternMismatch) return d.msgPattern || 'Check the format';
    if (v.rangeUnderflow || v.rangeOverflow) return d.msgRange || ('Choose a value between ' + el.min + ' and ' + el.max);
    return el.validationMessage;
  }
  function setError(el, msg) {
    var f = fieldOf(el), id = (el.id || ensureId(el, 'f')) + '-msg', m = doc.getElementById(id);
    if (!m) {
      m = doc.createElement('p'); m.id = id; m.className = P + '-msg ' + P + '-msg--error';
      var anchor = f.querySelector('.' + P + '-field__count') || null;
      if (f.classList.contains(P + '-check') || f.classList.contains(P + '-switch')) f.parentNode.insertBefore(m, f.nextSibling); else f.insertBefore(m, anchor);
    }
    if (msg) {
      m.innerHTML = ''; m.appendChild(iconSpan('error'));
      var s = doc.createElement('span'); s.innerHTML = '<span class="sr-only">Error: </span>'; s.appendChild(doc.createTextNode(msg)); m.appendChild(s);
      m.hidden = false; el.setAttribute('aria-invalid', 'true');
      var ids = (el.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean); if (ids.indexOf(id) < 0) { ids.push(id); el.setAttribute('aria-describedby', ids.join(' ')); }
    } else { m.hidden = true; el.removeAttribute('aria-invalid'); }
  }
  function validateEl(el) { if (!el.willValidate) return true; var ok = el.checkValidity(); setError(el, ok ? '' : messageFor(el)); return ok; }
  function initValidate(form) {
    if (!once(form, 'Val')) return;
    form.setAttribute('novalidate', '');
    var summary = form.querySelector('.' + P + '-error-summary');
    var els = function () { return $$('input, select, textarea', form).filter(function (el) { return el.willValidate && el.type !== 'submit'; }); };
    els().forEach(function (el) {
      on(el, 'blur', function () { if (form.classList.contains('was-validated') || el.value) validateEl(el); });
      on(el, el.type === 'checkbox' || el.type === 'radio' || el.tagName === 'SELECT' ? 'change' : 'input', function () { if (el.getAttribute('aria-invalid') === 'true') validateEl(el); });
    });
    on(form, 'submit', function (e) {
      form.classList.add('was-validated');
      var bad = els().filter(function (el) { return !validateEl(el); });
      var seen = {}; bad = bad.filter(function (el) { var k = el.type === 'radio' ? 'r:' + el.name : el.id; if (seen[k]) return false; seen[k] = 1; return true; });
      if (bad.length) {
        e.preventDefault();
        if (summary) {
          var ul = summary.querySelector('ul'); ul.innerHTML = '';
          bad.forEach(function (el) { var li = doc.createElement('li'), a = doc.createElement('a'); a.href = '#' + ensureId(el, 'f'); a.textContent = messageFor(el); a.addEventListener('click', function (ev) { ev.preventDefault(); el.focus(); }); li.appendChild(a); ul.appendChild(li); });
          summary.hidden = false; summary.setAttribute('tabindex', '-1'); summary.focus();
        } else bad[0].focus();
        emit(form, P + ':invalid', { fields: bad });
      } else {
        if (summary) summary.hidden = true;
        if (form.hasAttribute(attr('demo'))) { e.preventDefault(); UI.toast({ title: form.getAttribute(attr('demo')) || 'Sent', tone: 'success' }); form.reset(); form.classList.remove('was-validated'); }
        emit(form, P + ':valid', {});
      }
    });
  }
  function initCount(el) {
    if (!once(el, 'Count')) return;
    var max = parseInt(el.getAttribute('maxlength') || el.getAttribute(attr('count')) || '0', 10), f = fieldOf(el);
    var out = f.querySelector('.' + P + '-field__count');
    if (!out) { out = doc.createElement('p'); out.className = P + '-field__count'; f.appendChild(out); }
    out.setAttribute('aria-live', 'polite');
    var upd = function () { var n = el.value.length; out.textContent = n + (max ? ' / ' + max : ''); out.classList.toggle('is-over', !!max && n > max); };
    on(el, 'input', upd); upd();
  }

  /* ================================================================= TABLE */
  function initSort(table) {
    if (!once(table, 'Sort')) return;
    var heads = $$('thead th', table);
    heads.forEach(function (th, col) {
      var btn = th.querySelector('.' + P + '-table__sort'); if (!btn) return;
      on(btn, 'click', function () {
        var dir = th.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';
        heads.forEach(function (h) { if (h !== th) h.removeAttribute('aria-sort'); }); th.setAttribute('aria-sort', dir);
        var body = table.tBodies[0], rows = Array.prototype.slice.call(body.rows);
        var val = function (r) {
          var c = r.cells[col], raw = c.getAttribute('data-value'), t = (raw != null ? raw : c.textContent).trim();
          var n = parseFloat(t.replace(/[^\d.-]/g, ''));
          return (/^[^A-Za-zÀ-￿]*\d/.test(t) && !isNaN(n)) ? n : t.toLowerCase();
        };
        rows.sort(function (a, b) { var x = val(a), y = val(b); var r = (typeof x === 'number' && typeof y === 'number') ? x - y : String(x).localeCompare(String(y)); return dir === 'ascending' ? r : -r; });
        rows.forEach(function (r) { body.appendChild(r); });
        var live = table.parentNode.querySelector('[aria-live]'); if (live) live.textContent = 'Sorted by ' + btn.textContent.trim() + ', ' + dir;
      });
    });
  }

  /* ====================================================== FILE · RANGE · SEARCH */
  function fmtBytes(b) { return b < 1024 ? b + ' B' : b < 1048576 ? Math.round(b / 1024) + ' KB' : (b / 1048576).toFixed(1) + ' MB'; }
  function initFile(root) {
    if (!once(root, 'File')) return;
    var input = root.querySelector('input[type="file"]'), list = root.querySelector('.' + P + '-file__list'), zone = root.querySelector('.' + P + '-file__zone');
    if (!input) return;
    var render = function (files) { if (!list) return; list.innerHTML = ''; Array.prototype.forEach.call(files, function (f) { var li = doc.createElement('li'); li.innerHTML = '<span></span><span></span>'; li.firstChild.textContent = f.name; li.lastChild.textContent = fmtBytes(f.size); list.appendChild(li); }); };
    on(input, 'change', function () { render(input.files); });
    if (zone) {
      ['dragenter', 'dragover'].forEach(function (t) { on(zone, t, function (e) { e.preventDefault(); root.classList.add('is-dragover'); }); });
      ['dragleave', 'drop'].forEach(function (t) { on(zone, t, function (e) { e.preventDefault(); root.classList.remove('is-dragover'); }); });
      on(zone, 'drop', function (e) { if (e.dataTransfer && e.dataTransfer.files) { try { input.files = e.dataTransfer.files; } catch (x) { /* read-only in old browsers */ } render(e.dataTransfer.files); } });
    }
  }
  function initRange(el) {
    if (!once(el, 'Range')) return;
    var out = el.id ? doc.querySelector('output[for~="' + el.id + '"]') : null;
    var upd = function () { var min = +el.min || 0, max = +el.max || 100, v = ((+el.value - min) / (max - min)) * 100; el.style.setProperty('--_v', v + '%'); if (out) out.textContent = el.value + (el.getAttribute(attr('unit')) || ''); };
    on(el, 'input', upd); upd();
  }
  function initSearch(root) {
    if (!once(root, 'Search')) return;
    var input = root.querySelector('input'), clear = root.querySelector('.' + P + '-search__clear'); if (!input || !clear) return;
    on(clear, 'click', function () { input.value = ''; input.dispatchEvent(new Event('input', { bubbles: true })); input.focus(); });
    on(input, 'keydown', function (e) { if (e.key === 'Escape' && input.value) { e.preventDefault(); input.value = ''; } });
  }
  function initCopy(btn) {
    if (!once(btn, 'Copy')) return;
    on(btn, 'click', function () {
      var t = doc.querySelector(btn.getAttribute(attr('copy'))); if (!t) return;
      var text = t.textContent, label = btn.textContent;
      var ok = function () { btn.textContent = btn.getAttribute(attr('copied')) || 'Copied'; global.setTimeout(function () { btn.textContent = label; }, 1400); };
      if (global.navigator.clipboard && global.isSecureContext) global.navigator.clipboard.writeText(text).then(ok, function () {});
      else { var ta = doc.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'; doc.body.appendChild(ta); ta.select(); try { doc.execCommand('copy'); ok(); } catch (e) { /* no clipboard */ } doc.body.removeChild(ta); }
    });
  }
  function initChip(btn) {
    if (!once(btn, 'Chip')) return;
    on(btn, 'click', function () { btn.setAttribute('aria-pressed', String(btn.getAttribute('aria-pressed') !== 'true')); });
  }

  /* ================================================================== INIT */
  UI.init = function (root) {
    root = root || doc;
    fillIcons(root);
    $$(q('theme-switch'), root).forEach(initThemeSwitch);
    $$(q('theme-toggle'), root).forEach(initThemeToggle);
    $$(q('header'), root).forEach(initHeader);
    $$(q('menu-toggle'), root).forEach(initMenuToggle);
    $$(q('tabs'), root).forEach(initTabs);
    $$(q('accordion'), root).forEach(initAccordion);
    $$('dialog.' + P + '-modal', root).forEach(initModal);
    $$(q('modal-open'), root).forEach(initModalOpener);
    $$(q('tooltip'), root).forEach(initTooltip);
    $$(q('popover'), root).forEach(initPopover);
    $$(q('dismiss'), root).forEach(initDismiss);
    $$(q('toast'), root).forEach(initToastBtn);
    $$('form' + q('validate'), root).forEach(initValidate);
    $$(q('count'), root).forEach(initCount);
    $$('table' + q('sort'), root).forEach(initSort);
    $$(q('file'), root).forEach(initFile);
    $$(q('range'), root).forEach(initRange);
    $$(q('search'), root).forEach(initSearch);
    $$(q('copy'), root).forEach(initCopy);
    $$('button.' + P + '-chip[aria-pressed]', root).forEach(initChip);
    UI.theme.syncScopes(); UI.theme.syncControls();
  };
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', function () { UI.init(); }); else UI.init();
})(window);
