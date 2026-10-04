/* ==========================================================================
   {{BRAND_NAME}} — {{p}}-mark.js
   Renders the vector mark from mark-data.js (window.{{G}}_MARK), the lettering from
   wordmark-data.js (window.{{G}}_WORDMARK) and exposes the design DNA (window.{{G}}_DNA).
   Classic script (works from file:// and any server).
     <script src="…/SOURCE/JS/mark-data.js"></script>
     <script src="…/SOURCE/JS/wordmark-data.js"></script>   (optional)
     <script src="…/SOURCE/JS/dna-data.js"></script>        (optional)
     <script src="…/SOURCE/JS/{{p}}-mark.js"></script>
   {{G}}.wordmarkSVG(name, { color, label })  → SVG string   (names: lettering · stacked · line · line_1 · monogram · descriptor …)
   {{G}}.markSVG({ level:'master'|'simplified', variant, color, label, decorative, facetClass })  → SVG string
   <{{p}}-mark level="master" variant="on-dark" label="{{BRAND_NAME}}"></{{p}}-mark>
   Variants: color · on-dark · brand · tonal-dark · tonal-light · mono · outline · silhouette
   Also: {{G}}.rng(seed) (mulberry32) · {{G}}.hash(str) · {{G}}.mix(a,b,t) · {{G}}.reducedMotion()
   ========================================================================== */
(function (global) {
  'use strict';
  var NS = global.{{G}} || {};
  function hex2rgb(h) { h = h.replace('#', ''); return [0, 2, 4].map(function (i) { return parseInt(h.substr(i, 2), 16); }); }
  function rgb2hex(c) { return '#' + c.map(function (v) { return ('0' + Math.round(v).toString(16)).slice(-2); }).join('').toUpperCase(); }
  function mix(a, b, t) { var x = hex2rgb(a), y = hex2rgb(b); return rgb2hex(x.map(function (v, i) { return v + (y[i] - v) * t; })); }
  NS.mix = mix;

  function data() { var D = global.{{G}}_MARK; if (!D) throw new Error('mark-data.js must be loaded before {{p}}-mark.js'); return D; }
  function colourFn(variant, facets, D) {
    var lums = facets.map(function (f) { return f.l; }).slice().sort(function (a, b) { return a - b; });
    var ramp = D.ramp || [];
    switch (variant) {
      case 'on-dark': return function (f) {
        if (f.od) return f.od;
        if (f.l < 0.012) return mix(f.c, D.lift, 0.55);
        if (f.l < 0.03) return mix(f.c, D.lift, 0.42);
        if (f.l < 0.06) return mix(f.c, D.lift, 0.28);
        return f.c;
      };
      case 'brand': return function (f) { var r = lums.indexOf(f.l) / Math.max(1, lums.length - 1); return ramp[Math.min(ramp.length - 1, Math.floor(r * ramp.length))] || D.primary; };
      case 'tonal-dark': return function (f) { return mix(D.foundation, D.paper, Math.min(1, Math.sqrt(f.l) / 0.85) * 0.9); };
      case 'tonal-light': return function (f) { return mix(mix(D.foundation, '#FFFFFF', 0.25), '#FFFFFF', Math.min(1, Math.sqrt(f.l) / 0.85) * 0.9); };
      default: return function (f) { return f.c; };
    }
  }
  function shape(f, attrs) {
    if (f.p) return '<polygon points="' + f.p.map(function (q) { return q[0] + ',' + q[1]; }).join(' ') + '"' + attrs + '/>';
    var tr = (f.tx || f.ty) ? ' transform="translate(' + (f.tx || 0) + ',' + (f.ty || 0) + ')"' : '';
    return '<path fill-rule="evenodd" d="' + f.d + '"' + tr + attrs + '/>';
  }
  NS.markSVG = function (o) {
    o = o || {}; var D = data(), level = o.level || 'master', variant = o.variant || 'color';
    var facets = D[level], W = D.viewBox[2], H = D.viewBox[3], col = o.color || 'currentColor';
    var silD = D.silhouetteD || ('M' + D.silhouette.map(function (q) { return q[0] + ',' + q[1]; }).join(' L') + 'Z');
    var a11y = o.decorative ? ' aria-hidden="true" focusable="false"' : ' role="img" aria-label="' + String(o.label || '{{BRAND_NAME}}').replace(/"/g, '&quot;') + '"';
    var cls = o.className ? ' class="' + o.className + '"' : '', fc = o.facetClass ? ' class="' + o.facetClass + '"' : '';
    var body = '', vb = '0 0 ' + W + ' ' + H;
    if (variant === 'silhouette') body = '<path fill-rule="evenodd" d="' + silD + '" fill="' + col + '"/>';
    else if (variant === 'outline') {
      var sw = o.strokeWidth || (level === 'master' ? W / 400 : W / 190); vb = (-6) + ' ' + (-6) + ' ' + (W + 12) + ' ' + (H + 12);
      body = '<g fill="none" stroke="' + col + '" stroke-width="' + sw + '" stroke-linejoin="round">' + facets.map(function (f) { return shape(f, fc + ' data-facet="' + f.id + '"'); }).join('') + '</g>';
    } else if (variant === 'mono') {
      var id = '{{p}}m' + Math.random().toString(36).slice(2, 8), lw = o.lineWidth || (level === 'master' ? W / 240 : W / 95);
      var all = facets.map(function (f) { return shape(f, ''); }).join('');
      body = '<defs><mask id="' + id + '" maskUnits="userSpaceOnUse" x="0" y="0" width="' + W + '" height="' + H + '"><g fill="#fff" stroke="#000" stroke-width="' + lw + '" stroke-linejoin="round">' + all + '</g></mask></defs>' +
        '<g mask="url(#' + id + ')" fill="' + col + '"><path fill-rule="evenodd" d="' + silD + '"/>' + all + '</g>';
    } else {
      var fn = colourFn(variant, facets, D);
      body = facets.map(function (f) { var c = fn(f); return shape(f, fc + ' data-facet="' + f.id + '" fill="' + c + '"' + (D.seam ? ' stroke="' + c + '" stroke-width="0.75" stroke-linejoin="round"' : '')); }).join('');
    }
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + vb + '"' + cls + a11y + '>' + body + '</svg>';
  };
  NS.wordmarkSVG = function (name, o) {
    o = o || {}; var W = global.{{G}}_WORDMARK; if (!W || !W.items[name]) return '';
    var it = W.items[name], col = o.color || 'currentColor';
    var body = name === 'lettering' && !o.color ? it.body : '<g fill="' + col + '">' + it.body.replace(/fill="#[0-9A-Fa-f]{3,8}"/g, 'fill="' + col + '"') + '</g>';
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + it.vb + '" role="img" aria-label="' + String(o.label || '{{BRAND_NAME}}').replace(/"/g, '&quot;') + '">' + body + '</svg>';
  };
  NS.dna = global.{{G}}_DNA || null;
  NS.hash = function (s) { s = String(s); var h = 1779033703 ^ s.length; for (var i = 0; i < s.length; i++) { h = Math.imul(h ^ s.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); } return h >>> 0; };
  NS.rng = function (seed) { var a = (typeof seed === 'number' ? seed : NS.hash(seed)) >>> 0; return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; var t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; };
  NS.reducedMotion = function () { return !!(global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches); };

  if (global.customElements && !global.customElements.get('{{p}}-mark')) {
    var Base = global.HTMLElement;
    var El = function () { return Reflect.construct(Base, [], El); };
    El.prototype = Object.create(Base.prototype); El.prototype.constructor = El; Object.setPrototypeOf(El, Base);
    El.observedAttributes = ['level', 'variant', 'label', 'color'];
    El.prototype.connectedCallback = function () { this.render(); };
    El.prototype.attributeChangedCallback = function () { if (this.isConnected) this.render(); };
    El.prototype.render = function () {
      this.style.display = this.style.display || 'inline-block';
      this.innerHTML = NS.markSVG({ level: this.getAttribute('level') || 'master', variant: this.getAttribute('variant') || 'color',
        label: this.getAttribute('label') || undefined, decorative: this.hasAttribute('decorative'), color: this.getAttribute('color') || undefined,
        facetClass: this.getAttribute('facet-class') || undefined });
      var svg = this.firstChild; if (svg) { svg.style.width = '100%'; svg.style.height = '100%'; }
    };
    global.customElements.define('{{p}}-mark', El);
  }
  global.{{G}} = NS;
})(window);
