(function () {
  'use strict';
  var NS = window.{{G}};
  if (!NS || !NS.icons) return;
  var I = NS.icons, root = document.getElementById('ix-sets'), html = document.documentElement;
  var state = { q: '', set: '', variant: 'outline', size: 32 };
  var tiles = [];
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function opts(size, portable) {
    var duo = state.variant === 'duotone';
    return { size: size || state.size, variant: state.variant, tint: duo && !portable ? 'var(--ix-tint)' : null, tintOpacity: duo && !portable ? 0.75 : null };
  }
  I.sets.forEach(function (s) {
    var sec = document.createElement('section');
    sec.className = 'ix-set'; sec.setAttribute('data-set', s.key); sec.setAttribute('aria-labelledby', 'ix-h-' + s.key);
    sec.innerHTML = '<h2 class="ix-set-h" id="ix-h-' + esc(s.key) + '"><span>' + esc(s.label) + '</span><span class="ix-n"></span></h2><div class="ix-grid"></div>';
    var grid = sec.querySelector('.ix-grid');
    s.icons.forEach(function (n) {
      var m = I.meta[n], b = document.createElement('button');
      b.type = 'button'; b.className = 'ix-tile'; b.setAttribute('data-name', n); b.setAttribute('aria-label', m.label + ' — copy SVG');
      b.innerHTML = '<span class="ix-ic"></span><span class="ix-nm">' + esc(n) + '</span>';
      b._hay = [n, m.label, m.set].concat(m.keywords || [], m.aliases || []).join(' ').toLowerCase();
      grid.appendChild(b); tiles.push(b);
    });
    root.appendChild(sec);
  });
  function paint() {
    html.style.setProperty('--ix-size', state.size + 'px');
    tiles.forEach(function (b) { b.firstChild.innerHTML = NS.icon(b.getAttribute('data-name'), opts()); });
  }
  function filter() {
    var q = state.q.trim().toLowerCase(), terms = q ? q.split(/\s+/) : [], shown = 0;
    Array.prototype.forEach.call(root.children, function (sec) {
      var k = sec.getAttribute('data-set'), n = 0;
      Array.prototype.forEach.call(sec.querySelectorAll('.ix-tile'), function (b) {
        var ok = (!state.set || state.set === k) && terms.every(function (t) { return b._hay.indexOf(t) >= 0; });
        b.hidden = !ok; if (ok) n++;
      });
      sec.hidden = !n; sec.querySelector('.ix-n').textContent = n; shown += n;
    });
    document.getElementById('ix-count').textContent = shown + ' of ' + tiles.length + ' icons shown.';
    var e = document.getElementById('ix-empty'); e.hidden = !!shown; e.querySelector('span').textContent = state.q;
  }
  var toastT;
  function toast(msg) {
    var t = document.getElementById('ix-toast'); t.textContent = msg; t.classList.add('on');
    clearTimeout(toastT); toastT = setTimeout(function () { t.classList.remove('on'); }, 1800);
  }
  function copy(text, done) {
    function fallback() {
      var ta = document.createElement('textarea'); ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); var ok = false; try { ok = document.execCommand('copy'); } catch (e) {}
      document.body.removeChild(ta); done(ok);
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(function () { done(true); }, fallback); else fallback();
  }
  root.addEventListener('click', function (ev) {
    var b = ev.target.closest ? ev.target.closest('.ix-tile') : null; if (!b) return;
    var n = b.getAttribute('data-name');
    var text = ev.altKey ? n : NS.icon(n, opts(null, true));
    copy(text, function (ok) { toast(ok ? (ev.altKey ? 'Copied name “' + n + '”' : 'Copied ' + n + ' SVG (' + state.size + ' px, ' + state.variant + ')') : 'Copy failed — select the text manually'); });
  });
  var q = document.getElementById('ix-q');
  q.addEventListener('input', function () { state.q = q.value; filter(); });
  document.getElementById('ix-reset').addEventListener('click', function () { q.value = ''; state.q = ''; filter(); q.focus(); });
  var sel = document.getElementById('ix-set');
  sel.addEventListener('change', function () { state.set = sel.value; filter(); });
  Array.prototype.forEach.call(document.querySelectorAll('.ix-seg button'), function (btn, i, all) {
    btn.addEventListener('click', function () {
      Array.prototype.forEach.call(all, function (x) { x.setAttribute('aria-pressed', String(x === btn)); });
      state.variant = btn.getAttribute('data-v'); paint();
    });
  });
  var size = document.getElementById('ix-size'), out = document.getElementById('ix-size-out');
  size.addEventListener('input', function () { state.size = +size.value; out.textContent = size.value + ' px'; paint(); });
  var th = document.getElementById('ix-theme');
  function setTheme(dark) { html.setAttribute('data-theme', dark ? 'dark' : 'light'); th.setAttribute('aria-pressed', String(dark)); th.textContent = dark ? 'Light' : 'Dark'; th.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme'); }
  setTheme(html.getAttribute('data-theme') === 'dark' || (!html.getAttribute('data-theme') && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches));
  th.addEventListener('click', function () { setTheme(html.getAttribute('data-theme') !== 'dark'); });
  var hq = (location.hash || '').replace(/^#/, '');
  if (hq) { if (hq.indexOf('set=') === 0) { state.set = sel.value = hq.slice(4); } else { state.q = q.value = decodeURIComponent(hq); } }
  paint(); filter();
})();
