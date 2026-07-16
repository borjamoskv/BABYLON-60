import{r as i,j as m}from"./vendor-BPWtllH_.js";import{J as U,aa as V,d as K,ab as L,ac as $,ad as W}from"./index-faGPXfWw.js";import{H as J}from"./HtmlPreview-yTeYvEkc.js";import"./rects-C9PWJszb.js";const Q=`
(function() {
  if (window.__selectorGenInitialized) return;
  window.__selectorGenInitialized = true;

  var SCORING = {
    TERM_PENALTY: -2,
    SEMANTIC_CLASS: 4,
    RANDOM_CLASS: -2,
    ID: 10,
    SEMANTIC_ATTR: 6,
    RANDOM_ATTR: -1,
    NTH_CHILD: 0,
    SEMANTIC_TAG: 1,
    RANDOM_TAG: -1,
    TAG_GROUP: 3
  };

  var SEMANTIC_TAGS = ['a','button','input','select','textarea','label','form','nav','header','footer','main','section','article','aside','h1','h2','h3','h4','h5','h6'];

  var TAG_GROUPS = [
    { tags: ['h1','h2','h3','h4','h5','h6'],                                         score: SCORING.TAG_GROUP },
    { tags: ['h1','h2'],                                                              score: SCORING.TAG_GROUP },
    { tags: ['h1','h2','h3','h4','h5','h6','p','li','dt','dd','blockquote','figcaption','label','span','a','em','strong','small','td','th','caption'], score: SCORING.TAG_GROUP },
    { tags: ['img','video'],                                                          score: SCORING.TAG_GROUP },
    { tags: ['button','input','textarea'],                                            score: SCORING.TAG_GROUP }
  ];

  function scoreForTag(tag) {
    return SEMANTIC_TAGS.indexOf(tag.toLowerCase()) >= 0 ? SCORING.SEMANTIC_TAG : SCORING.RANDOM_TAG;
  }

  function scoreForAttr(name, hasValue) {
    if (hasValue && (name === 'role' || name === 'aria-role' || name === 'aria-label')) {
      return SCORING.SEMANTIC_ATTR;
    }
    return SCORING.RANDOM_ATTR;
  }

  function scoreForClassName(className) {
    if (className.length < 2) return SCORING.RANDOM_CLASS;
    if (/^(btn|button|nav|menu|header|footer|main|content|container|wrapper|row|col|column|title|heading|label|input|form|card|panel|section|item|list|link|icon|img|image|bg|background|text|font|color|size|flex|grid|layout|margin|padding|border|active|disabled|hidden|visible|selected|hover|focus)/.test(className)) {
      return SCORING.SEMANTIC_CLASS;
    }
    if (/^[a-z]+(-[a-z]+)*$/.test(className)) return SCORING.SEMANTIC_CLASS;
    if (/^[a-z][a-zA-Z0-9]*$/.test(className)) return SCORING.SEMANTIC_CLASS;
    if (/^[a-zA-Z0-9]{5,}$/.test(className)) return SCORING.RANDOM_CLASS;
    if (/^_[a-zA-Z0-9]+_[a-zA-Z0-9]+/.test(className)) return SCORING.RANDOM_CLASS;
    if (/[0-9a-f]{4,}/.test(className)) return SCORING.RANDOM_CLASS;
    return 0;
  }

  function termToString(term) {
    var parts = [];
    if (term.directChild) parts.push('>');
    if (term.tagGroup) {
      parts.push(':is(' + term.tagGroup.join(',') + ')');
    } else if (term.tag) {
      parts.push(term.tag);
    } else if (!term.className && !term.id && !term.hasAttr) {
      parts.push('*');
    }
    if (term.id) parts.push('#' + CSS.escape(term.id));
    if (term.className) parts.push('.' + CSS.escape(term.className));
    if (term.hasAttr) {
      if (term.attrVal) {
        var av = String(term.attrVal).replace(/\\\\/g, '\\\\\\\\').replace(/"/g, '\\\\"');
        parts.push('[' + term.hasAttr + '="' + av + '"]');
      } else {
        parts.push('[' + term.hasAttr + ']');
      }
    }
    if (term.nthChild) {
      parts.push(':nth-child(' + term.nthChild + ')');
    } else if (term.lastChild) {
      parts.push(':last-child');
    }
    return parts.join('');
  }

  function candidateToString(cand) {
    return cand.terms.map(termToString).join(' ');
  }

  function matchCount(terms) {
    var sel = terms.map(termToString).join(' ');
    try { return document.querySelectorAll(sel).length; } catch(e) { return 9999; }
  }

  function baseCandidates(element) {
    var candidates = [];
    function addCandidate(terms, score) {
      candidates.push({ terms: terms, topMatch: element, score: score + SCORING.TERM_PENALTY, matchCount: matchCount(terms) });
    }
    if (element.tagName === 'BODY') {
      addCandidate([{ tag: 'body' }], scoreForTag('body'));
      return candidates;
    }
    if (element.tagName) {
      var tag = element.tagName.toLowerCase();
      var tagTerm = { tag: tag };
      addCandidate([tagTerm], 1);
      var siblingCount = element.parentElement ? element.parentElement.children.length : 0;
      var siblings = element.parentElement ? Array.from(element.parentElement.children) : [];
      var nth = siblings.indexOf(element);
      if (nth !== -1) {
        var t2 = {}; for (var k in tagTerm) t2[k] = tagTerm[k];
        t2.nthChild = nth + 1;
        addCandidate([t2], SCORING.NTH_CHILD + SCORING.TERM_PENALTY + scoreForTag(tag));
        if (nth === siblingCount - 1) {
          var t3 = {}; for (var k2 in tagTerm) t3[k2] = tagTerm[k2];
          t3.lastChild = true;
          addCandidate([t3], SCORING.NTH_CHILD + SCORING.TERM_PENALTY + scoreForTag(tag));
        }
      }
      for (var gi = 0; gi < TAG_GROUPS.length; gi++) {
        var group = TAG_GROUPS[gi];
        if (group.tags.indexOf(tag) >= 0) {
          addCandidate([{ tagGroup: group.tags }], group.score);
        }
      }
    }
    if (element.id) {
      addCandidate([{ id: element.id }], SCORING.ID);
    }
    if (element.classList && element.classList.length > 0) {
      Array.from(element.classList).forEach(function(cn) {
        addCandidate([{ className: cn }], SCORING.TERM_PENALTY + scoreForClassName(cn));
      });
    }
    if (element.attributes && element.attributes.length > 0) {
      Array.from(element.attributes).filter(function(a) {
        return a.name !== 'id' && a.name !== 'class' && a.name !== 'style' && a.name !== 'contenteditable';
      }).forEach(function(attr) {
        addCandidate([{ hasAttr: attr.name }], scoreForAttr(attr.name, false));
        if (attr.value) {
          addCandidate([{ hasAttr: attr.name, attrVal: attr.value }], scoreForAttr(attr.name, true));
        }
      });
    }
    return candidates;
  }

  function reduceCandidateCount(cands, keep) {
    var maxMatch = 4000;
    var buckets = 10;
    cands = cands.filter(function(x) { return x.matchCount <= maxMatch; });
    if (cands.length <= keep) return cands;
    var maxLog = Math.log2(Math.max.apply(null, cands.map(function(c) { return Math.max(1, c.matchCount); })));
    if (maxLog <= 0) {
      cands.sort(function(a, b) { return b.score - a.score; });
      return cands.slice(0, keep);
    }
    var interval = maxLog / buckets;
    var bucketArr = [];
    for (var i = 0; i < buckets; i++) bucketArr.push([]);
    cands.forEach(function(c) {
      var lv = Math.log2(Math.max(1, c.matchCount));
      var bi = Math.min(buckets - 1, Math.floor(lv / interval));
      if (isNaN(bi) || bi < 0) bi = 0;
      bucketArr[bi].push(c);
    });
    bucketArr.forEach(function(b) { b.sort(function(a, b2) { return b2.score - a.score; }); });
    var perBucket = Math.ceil(keep / buckets);
    var result = [];
    bucketArr.forEach(function(b) { result.push.apply(result, b.slice(0, perBucket)); });
    if (result.length > keep) {
      result.sort(function(a, b2) { return b2.score - a.score; });
      return result.slice(0, keep);
    }
    return result;
  }

  function expandCandidate(candidate, seen) {
    if (candidate.terms.some(function(t) { return !!t.id; })) return [];
    var result = [];
    var currentElement = candidate.topMatch;
    var parents = [];
    var parent = currentElement.parentElement;
    for (var i = 0; i < 3; i++) {
      if (!parent) break;
      parents.push(parent);
      if (parent.tagName === 'BODY') break;
      parent = parent.parentElement;
    }
    for (var pi = 0; pi < parents.length; pi++) {
      var pCands = baseCandidates(parents[pi]);
      for (var ci = 0; ci < pCands.length; ci++) {
        var pc = pCands[ci];
        if (pc.terms[0].tag === 'body' && pi !== 0) continue;
        var newTerms = pc.terms.concat(candidate.terms.map(function(t) {
          var copy = {}; for (var k in t) copy[k] = t[k]; return copy;
        }));
        if (pi === 0) {
          newTerms[pc.terms.length] = Object.assign({}, newTerms[pc.terms.length], { directChild: true });
        }
        var newCand = { terms: newTerms, topMatch: parents[pi], score: candidate.score + pc.score, matchCount: matchCount(newTerms) };
        var sel = candidateToString(newCand);
        if (!seen[sel]) { seen[sel] = true; result.push(newCand); }
      }
    }
    return result;
  }

  function getParents(el) {
    var parents = [];
    var p = el.parentElement;
    while (p) { parents.push(p); p = p.parentElement; }
    return parents;
  }

  function removeCandidatesMatchingParents(cands, element) {
    var parents = getParents(element);
    return cands.filter(function(c) {
      try {
        var matches = document.querySelectorAll(candidateToString(c));
        return !Array.from(matches).some(function(el) {
          return parents.some(function(p) { return p === el; });
        });
      } catch(e) { return false; }
    });
  }

  window.__generateSelectorList = function(element) {
    var iterationCount = 3;
    var pool = reduceCandidateCount(baseCandidates(element), 40);
    var seen = {};
    pool.forEach(function(c) { seen[candidateToString(c)] = true; });
    var expandedIds = {};
    for (var i = 0; i < iterationCount; i++) {
      var nextPool = pool.slice();
      for (var j = 0; j < pool.length; j++) {
        var id = candidateToString(pool[j]);
        if (expandedIds[id]) continue;
        expandedIds[id] = true;
        var expansions = expandCandidate(pool[j], seen);
        nextPool.push.apply(nextPool, expansions);
      }
      var isFinal = i === iterationCount - 1;
      if (isFinal) {
        nextPool = nextPool.filter(function(c) { return c.matchCount <= 100; });
        nextPool = removeCandidatesMatchingParents(nextPool, element);
      }
      pool = reduceCandidateCount(nextPool, isFinal ? 20 : 40);
    }
    pool.sort(function(a, b) {
      if (a.matchCount === b.matchCount) return b.score - a.score;
      return a.matchCount - b.matchCount;
    });
    var byCount = {};
    var deduped = [];
    pool.forEach(function(c) {
      var sel = candidateToString(c);
      if (!byCount[c.matchCount]) {
        byCount[c.matchCount] = true;
        deduped.push({ selector: sel, matchCount: c.matchCount });
      }
    });
    return deduped;
  };
})();
`,ee=`
(function() {
  if (window.__describeEl) return;

  var LINE_MAX = 100;

  function clamp(s, n) {
    if (!s) return '';
    s = String(s).trim().replace(/\\s+/g, ' ');
    return s.length > n ? s.slice(0, n - 1) + '…' : s;
  }

  function clampMid(joined, sep, n) {
    if (joined.length <= n) return joined;
    var parts = joined.split(sep);
    var head = [parts[0]], tail = [parts[parts.length - 1]];
    var len = head[0].length + tail[0].length + sep.length + 1;
    var hi = 1, ti = parts.length - 2;
    while (hi <= ti) {
      var t = parts[ti];
      if (len + sep.length + t.length <= n) { tail.unshift(t); len += sep.length + t.length; ti--; continue; }
      var h = parts[hi];
      if (len + sep.length + h.length <= n) { head.push(h); len += sep.length + h.length; hi++; continue; }
      break;
    }
    if (hi > ti) return head.concat(tail).join(sep);
    return head.concat('…', tail).join(sep);
  }

  var _fiberKey;
  window.__reactName = function(el) {
    try {
      if (!_fiberKey) {
        for (var k in el) { if (k.indexOf('__reactFiber$') === 0) { _fiberKey = k; break; } }
      }
      var f = _fiberKey && el[_fiberKey];
      var hops = 0;
      while (f && hops < 24) {
        var t = f.type || f.elementType;
        if (typeof t === 'function') {
          var n = t.displayName || t.name;
          if (n && n.length > 1) return n;
        } else if (t && typeof t === 'object') {
          if (t.displayName) return t.displayName;
        }
        f = f.return;
        hops++;
      }
    } catch (e) {}
  };

  function domHop(el, wantIndex) {
    var s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    var cn = el.className;
    if (cn && typeof cn === 'string') {
      var cls = cn.split(' ').filter(Boolean).slice(0, 2);
      for (var i = 0; i < cls.length; i++) s += '.' + clamp(cls[i], 20);
    }
    if (wantIndex) {
      var p = el.parentElement;
      if (p && p.children.length > 1) {
        var idx = Array.prototype.indexOf.call(p.children, el);
        s += '[' + (idx + 1) + '/' + p.children.length + ']';
      }
    }
    return s;
  }

  window.__describeEl = function(el, selector) {
    var reactPath = [];
    for (var a = el; a && a.nodeType === 1 && a !== document.documentElement; a = a.parentElement) {
      var rn = window.__reactName(a);
      if (rn && rn !== reactPath[0]) reactPath.unshift(rn);
    }
    var domParts = [];
    for (var d = el; d && d.nodeType === 1 && d !== document.documentElement; d = d.parentElement) {
      domParts.unshift(domHop(d, d === el));
    }
    var textBits = [];
    var txt = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
    if (txt) textBits.push('"' + clamp(txt, 60) + '"');
    var aria = el.getAttribute('aria-label');
    if (aria) textBits.push('aria-label: "' + clamp(aria, 40) + '"');
    var alts = [];
    if (el.getAttribute('alt')) alts.push(el.getAttribute('alt'));
    var imgs = el.querySelectorAll('img[alt]');
    for (var i = 0; i < imgs.length && alts.length < 3; i++) {
      var a2 = imgs[i].getAttribute('alt');
      if (a2) alts.push(a2);
    }
    if (alts.length) textBits.push('alt: "' + clamp(alts.join(' · '), 40) + '"');
    var kids = [];
    var cn2 = el.childNodes;
    for (var k2 = 0; k2 < cn2.length; k2++) {
      var c = cn2[k2];
      if (c.nodeType === 1) kids.push(c.tagName.toLowerCase());
      else if (c.nodeType === 3 && c.textContent.trim()) kids.push('text');
    }
    var SEP = ' › ';
    var lines = ['<mentioned-element>'];
    if (reactPath.length) lines.push('react:    ' + clamp(reactPath.join(SEP), LINE_MAX));
    lines.push('dom:      ' + clampMid(domParts.join(SEP), SEP, LINE_MAX));
    if (textBits.length) lines.push('text:     ' + clamp(textBits.join(' · '), LINE_MAX));
    if (kids.length) lines.push('children: ' + clamp(kids.join(', '), LINE_MAX));
    if (selector) lines.push('selector: ' + clamp(selector, LINE_MAX));
    lines.push('</mentioned-element>');
    return lines.join('\\n');
  };
})();
`,te=`
(function() {
  if (window.__operonAnnotInit) return;
  window.__operonAnnotInit = true;

  // NB: \`__nonce\` is the outer IIFE parameter injected by
  // injectAnnotationScript() — it is NOT written to \`window\` (a head-level
  // setter trap could intercept that) and the <script> element itself is
  // scrubbed before any other code can read its textContent.

  var highlightOverlay = null;
  var highlightTarget = null; // element the hover/pick outline is parked on
  var persistentHighlights = []; // [{box, badge, selector, id}]
  var annotModeActive = false;
  // Host-applied zoom scale (the iframe element is CSS-scaled by the zoom
  // feature, which scales this fixed-size chrome with it — badges at the
  // 0.25x fit floor would be ~6px with illegible digits). Chrome counter-
  // scales by 1/hostZoom. Updated via 'operon/zoom' window messages from
  // the host (relayed by the proxy, same path as operon/remeasure); the
  // script requests the current value at startup since it may load into an
  // already-scaled iframe.
  var hostZoom = 1;
  function badgeZoomStyle(b) {
    b.style.transform = 'scale(' + (1 / hostZoom) + ')';
    // Keep the anchor point (badge center at min size, 12px in) pinned.
    b.style.transformOrigin = '12px 12px';
  }
  function boxZoomStyle(box) {
    box.style.borderWidth = (2 / hostZoom) + 'px';
  }
  function applyHostZoom() {
    if (highlightOverlay) boxZoomStyle(highlightOverlay);
    for (var i = 0; i < persistentHighlights.length; i++) {
      badgeZoomStyle(persistentHighlights[i].badge);
      boxZoomStyle(persistentHighlights[i].box);
    }
    // Re-run positioning (persistent boxes AND the hover outline) so the
    // border-width-dependent offsets update everywhere (hoisted; defined
    // below).
    repositionAll();
  }
  window.addEventListener('message', function(ev) {
    var d = ev.data;
    if (d && d.method === 'operon/zoom' && d.params && typeof d.params.scale === 'number' &&
        isFinite(d.params.scale) && d.params.scale >= 0.05 && d.params.scale <= 20) {
      hostZoom = d.params.scale;
      applyHostZoom();
    }
  });
  try {
    window.parent.postMessage({ jsonrpc: '2.0', method: 'operon/zoom-request' }, '*');
  } catch (e) {}

  function createHighlight(color) {
    color = color || '#3B82F6';
    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;pointer-events:none;border:2px solid ' + color + ';border-radius:4px;z-index:2147483646;box-shadow:0 0 0 2px rgba(255,255,255,0.7);';
    overlay.setAttribute('data-operon-overlay', '1');
    boxZoomStyle(overlay);
    document.body.appendChild(overlay);
    return overlay;
  }

  function createBadge(label) {
    var b = document.createElement('div');
    b.setAttribute('data-operon-overlay', '1');
    b.textContent = String(label);
    b.style.cssText = 'position:fixed;z-index:2147483647;min-width:24px;height:24px;padding:0 5px;box-sizing:border-box;border-radius:12px;background:#16A34A;color:#fff;font:700 12px/24px system-ui,sans-serif;text-align:center;box-shadow:0 0 0 2px #fff,0 2px 6px rgba(0,0,0,0.3);cursor:pointer;';
    badgeZoomStyle(b);
    document.body.appendChild(b);
    return b;
  }

  function positionHighlight(overlay, el) {
    var rect = el.getBoundingClientRect();
    // Offsets track the counter-scaled border width so the outline stays
    // just outside the element at any host zoom.
    var bw = 2 / hostZoom;
    overlay.style.left = (rect.left - bw) + 'px';
    overlay.style.top = (rect.top - bw) + 'px';
    overlay.style.width = (rect.width + 2 * bw) + 'px';
    overlay.style.height = (rect.height + 2 * bw) + 'px';
    overlay.style.display = 'block';
  }

  function repositionPersistent() {
    for (var i = 0; i < persistentHighlights.length; i++) {
      var item = persistentHighlights[i];
      try {
        var el = document.querySelector(item.selector);
        if (!el) { item.box.style.display = 'none'; item.badge.style.display = 'none'; continue; }
        positionHighlight(item.box, el);
        var r = el.getBoundingClientRect();
        item.badge.style.left = (r.left - 12) + 'px';
        item.badge.style.top = (r.top - 12) + 'px';
        item.badge.style.display = 'block';
      } catch (e) {}
    }
  }
  function hideHover() {
    if (highlightOverlay) highlightOverlay.style.display = 'none';
    highlightTarget = null;
  }
  // The hover/pick outline is position:fixed — re-derive it from its element
  // on every scroll/resize so it tracks the element, not the viewport (same
  // treatment the saved annotation boxes get in repositionPersistent).
  function repositionHover() {
    if (!highlightOverlay || highlightOverlay.style.display === 'none') return;
    try {
      // .isConnected (Node property) rather than document.contains() — the
      // latter is clobberable by artifact DOM (e.g. <img name="contains">)
      // through the Document named-property getter.
      if (!highlightTarget || !highlightTarget.isConnected) { hideHover(); return; }
      // Elements hidden mid-hover (display:none accordion/carousel) report a
      // zero rect — hide instead of painting a 4x4 blob at the viewport origin.
      var r = highlightTarget.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) { hideHover(); return; }
      positionHighlight(highlightOverlay, highlightTarget);
    } catch (e) { hideHover(); }
  }
  function repositionAll() {
    repositionPersistent();
    repositionHover();
  }
  window.addEventListener('scroll', repositionAll, { capture: true, passive: true });
  window.addEventListener('resize', repositionAll);

  function fallbackSelector(el) {
    if (el.id) {
      var idSel = '#' + CSS.escape(el.id);
      if (document.querySelectorAll(idSel).length === 1) return idSel;
    }
    if (el === document.body) return 'body';
    var parent = el.parentNode;
    if (!parent) return el.tagName.toLowerCase();
    var siblings = Array.from(parent.children);
    var index = siblings.indexOf(el);
    return fallbackSelector(parent) + ' > ' + el.tagName.toLowerCase() + ':nth-child(' + (index + 1) + ')';
  }

  function pickSelector(el) {
    try {
      var sels = window.__generateSelectorList ? window.__generateSelectorList(el) : [];
      if (sels.length > 0) return { selector: sels[0].selector, matchCount: sels[0].matchCount };
    } catch(e) {}
    var fb = fallbackSelector(el);
    return { selector: fb, matchCount: document.querySelectorAll(fb).length };
  }

  // ── Transport ──────────────────────────────────────────────────────────────
  var channel = new MessageChannel();
  var port = channel.port1;
  try {
    window.top.postMessage({ __OPERON_ANNOT_PORT__: true, nonce: __nonce }, '*', [channel.port2]);
  } catch (e) {}

  port.onmessage = function(ev) {
    var msg = ev.data || {};
    if (msg.kind === 'set-mode') {
      annotModeActive = !!msg.on;
      if (document.body) document.body.style.cursor = annotModeActive ? 'crosshair' : '';
      if (!annotModeActive) hideHover();
    } else if (msg.kind === 'highlight') {
      // Replace the full set — host sends the current annotation list, not
      // incremental adds. Clear then rebuild so deleted annotations vanish.
      persistentHighlights.forEach(function(h) { h.box.remove(); h.badge.remove(); });
      persistentHighlights = [];
      var bgc = msg.badgeColor || '#16A34A';
      for (var i = 0; i < msg.items.length; i++) {
        (function(it) {
          try {
            var el = document.querySelector(it.selector);
            if (!el) return;
            var box = createHighlight('#FACC15');
            var badge = createBadge(it.label);
            badge.style.background = bgc;
            badge.title = it.text || '';
            badge.addEventListener('click', function(ev) {
              ev.stopPropagation();
              var r = el.getBoundingClientRect();
              port.postMessage({
                kind: 'badge-click',
                id: it.id,
                rect: { x: r.left, y: r.top, width: r.width, height: r.height,
                        vw: window.innerWidth, vh: window.innerHeight },
              });
            });
            persistentHighlights.push({ box: box, badge: badge, selector: it.selector, id: it.id });
          } catch (e) {}
        })(msg.items[i]);
      }
      repositionPersistent();
    } else if (msg.kind === 'clear-highlights') {
      persistentHighlights.forEach(function(h) { h.box.remove(); h.badge.remove(); });
      persistentHighlights = [];
    }
  };
  port.start();

  // ── Hover highlight ────────────────────────────────────────────────────────
  document.addEventListener('mousemove', function(e) {
    if (!annotModeActive) return;
    var el = document.elementFromPoint(e.clientX, e.clientY);
    if (!el || el.hasAttribute('data-operon-overlay')) return;
    if (!highlightOverlay) highlightOverlay = createHighlight();
    highlightTarget = el;
    positionHighlight(highlightOverlay, el);
  });
  document.addEventListener('mouseleave', function() {
    hideHover();
  });

  // ── Click capture ──────────────────────────────────────────────────────────
  document.addEventListener('click', function(e) {
    var t = e.target;
    var onOverlay = t && t.closest ? !!t.closest('[data-operon-overlay]') : false;
    if (!annotModeActive) {
      // Clicks on our own badges/overlays are handled by their own listeners
      // (which post badge-click). Any other click inside the iframe tells the
      // host to dismiss an open view popover — cross-origin iframes don't
      // bubble clicks to the host, so AnnotationPopover's outside-click can't
      // see them.
      if (!onOverlay) port.postMessage({ kind: 'dismiss' });
      return;
    }
    e.preventDefault();
    e.stopPropagation();
    // Prefer the element the hover outline is parked on: after a scroll with
    // the cursor stationary, elementFromPoint resolves whatever slid under the
    // pointer, not the element the outline visibly wraps — and the outline is
    // the promise of what a click annotates. Only honor the tracked element
    // while that promise is actually visible:
    //   - non-zero rect, at least partly in the viewport;
    //   - the painted outline still sits on the element's current rect (a pure
    //     layout shift — image-load reflow, accordion expand — moves the
    //     element without firing scroll/resize, leaving the outline stale);
    //   - the element is really visible at its own location (not clipped away
    //     by an overflow ancestor or occluded by a modal): hit-test the center
    //     of the viewport-visible part of its rect.
    // Otherwise fall back to whatever is under the cursor.
    var useTracked = false;
    if (highlightTarget && highlightTarget.isConnected && highlightOverlay) {
      try {
        var tr = highlightTarget.getBoundingClientRect();
        var vw0 = window.innerWidth || 0, vh0 = window.innerHeight || 0;
        var visible = (tr.width > 0 || tr.height > 0) &&
          tr.bottom > 0 && tr.right > 0 && tr.top < vh0 && tr.left < vw0;
        if (visible) {
          // Compare against the same counter-scaled offset positionHighlight
          // paints with — a hardcoded 2 would make this gate always-false
          // below ~0.571x host zoom (routine under the fit default).
          var mbw = 2 / hostZoom;
          var matchesPaint =
            Math.abs(parseFloat(highlightOverlay.style.left) - (tr.left - mbw)) < 1.5 &&
            Math.abs(parseFloat(highlightOverlay.style.top) - (tr.top - mbw)) < 1.5;
          var cx = (Math.max(tr.left, 0) + Math.min(tr.right, vw0)) / 2;
          var cy = (Math.max(tr.top, 0) + Math.min(tr.bottom, vh0)) / 2;
          var hit = document.elementFromPoint(cx, cy);
          var hitCompatible = !!hit && (hit === highlightTarget ||
            highlightTarget.contains(hit) || hit.contains(highlightTarget));
          useTracked = matchesPaint && hitCompatible;
        }
      } catch (err) {}
    }
    var el = useTracked ? highlightTarget : document.elementFromPoint(e.clientX, e.clientY);
    if (!el || onOverlay) return;
    hideHover();
    var picked = pickSelector(el);
    var descriptor = window.__describeEl ? window.__describeEl(el, picked.selector) : '';
    // Visible text of the clicked element — travels as the annotation's anchor
    // (selection_text) so the agent gets the actual content, not just a CSS
    // selector. innerText only (no textContent fallback): textContent would
    // pull in CSS-hidden children the user never saw, which must not reach
    // the agent as "what the user flagged". Trimmed + capped.
    var elementText = '';
    try {
      elementText = String(el.innerText || '').trim();
      if (elementText.length > 2000) {
        elementText = elementText.slice(0, 2000);
        var lastCode = elementText.charCodeAt(elementText.length - 1);
        if (lastCode >= 0xD800 && lastCode <= 0xDBFF) elementText = elementText.slice(0, -1);
      }
    } catch (errText) {}
    var r = el.getBoundingClientRect();
    var vw = window.innerWidth || 1, vh = window.innerHeight || 1;
    port.postMessage({
      kind: 'selected',
      selector: picked.selector,
      descriptor: descriptor,
      elementText: elementText,
      rect: { x: r.x, y: r.y, width: r.width, height: r.height, vw: vw, vh: vh }
    });
  }, true);
})();
`,ne=Q+ee+te;function re(t,r){const s='<script data-operon-annot="1">(function(__nonce){try{var s=document.currentScript;if(s){s.textContent="";s.remove();}}catch(e){}'+ne+"})("+JSON.stringify(r)+");<\/script>";return/<head\b[^>]*>/i.test(t)?t.replace(/<head\b[^>]*>/i,l=>l+s):/<body\b[^>]*>/i.test(t)?t.replace(/(<body\b[^>]*>)/i,l=>l+s):s+t}const H=new Map,F=new Set;function ae(t){let r=H.get(t);return r||(r=crypto.randomUUID(),H.set(t,r),F.add(r)),r}const x=new Map;function D(t){for(const r of t.subs)r()}function w(t){let r=x.get(t);return r||(r={port:null,mode:!1,refCount:0,subs:new Set,onFrame:[]},x.set(t,r)),r}let j=!1;function ie(){j||(j=!0,window.addEventListener("message",t=>{var b;if(!t.data||t.data.__OPERON_ANNOT_PORT__!==!0)return;if(t.origin!=="null"){console.warn("operon: annotation handshake from non-opaque origin",t.origin,"— sandbox proxy not honouring params.sandbox (M52)?");return}const r=String(t.data.nonce??"");if(!F.has(r))return;const s=t.ports[0];if(!s)return;const l=w(r);(b=l.port)==null||b.close(),l.port=s,s.onmessage=y=>{const h=l.onFrame[l.onFrame.length-1];h==null||h(y.data)},s.start(),l.mode&&s.postMessage({kind:"set-mode",on:!0}),D(l)}))}function oe(t,r){const s=i.useRef(r);s.current=r,i.useEffect(()=>{ie();const n=w(t);n.refCount++;const a=o=>s.current(o);return n.onFrame.push(a),()=>{var g;const o=n.onFrame.lastIndexOf(a);o!==-1&&n.onFrame.splice(o,1),n.refCount--,n.refCount<=0&&((g=n.port)==null||g.close(),x.delete(t))}},[t]);const l=i.useSyncExternalStore(i.useCallback(n=>{const a=w(t);return a.subs.add(n),()=>a.subs.delete(n)},[t]),()=>{const n=x.get(t);return n?(n.port?2:0)|(n.mode?1:0):0}),b=(l&2)!==0,y=(l&1)!==0,h=i.useCallback(n=>{var a,o;return(o=(a=x.get(t))==null?void 0:a.port)==null?void 0:o.postMessage(n)},[t]),d=i.useCallback(n=>{var o;const a=w(t);a.mode!==n&&(a.mode=n,(o=a.port)==null||o.postMessage({kind:"set-mode",on:n}),D(a))},[t]);return{portReady:b,mode:y,setMode:d,post:h}}function he({artifactId:t,versionId:r,annotations:s,onAddAnnotation:l,onDeleteAnnotation:b,onUpdateAnnotation:y}){const h=i.useRef(null),[d,n]=i.useState(null),[a,o]=i.useState(null),g=U(),N=i.useRef(g);N.current=g,i.useEffect(()=>{g||(n(null),o(null))},[g]);const T=ae(r),z=i.useCallback(e=>re(e,T),[T]),k=i.useRef(s);k.current=s;const B=i.useCallback(e=>{var I;if(!N.current)return;if(e.kind==="dismiss"){o(null);return}const c=(I=h.current)==null?void 0:I.getBoundingClientRect();if(!c)return;const f=c.width/(e.rect.vw||c.width),M=c.height/(e.rect.vh||c.height);if(e.kind==="badge-click"){const v=k.current.find(u=>u.id===e.id);if(!v)return;n(null),o(u=>(u==null?void 0:u.annotation.id)===e.id?null:{annotation:v,anchorX:c.left+e.rect.x*f,anchorY:c.top+e.rect.y*M});return}if(e.kind!=="selected")return;const X=c.left+(e.rect.x+e.rect.width/2)*f,q=c.top+(e.rect.y+e.rect.height)*M,_=(v,u)=>{let p=String(v??"");if(p.length<=u)return p;p=p.slice(0,u);const G=p.charCodeAt(p.length-1);return G>=55296&&G<=56319?p.slice(0,-1):p},P=v=>Number.isFinite(v)?Math.min(100,Math.max(0,v)):50;o(null),n({selector:_(e.selector,4096),descriptor:_(e.descriptor,4096),elementText:_(e.elementText,2e3),anchorX:X,anchorY:q,x_percent:P((e.rect.x+e.rect.width/2)/(e.rect.vw||1)*100),y_percent:P((e.rect.y+e.rect.height/2)/(e.rect.vh||1)*100)})},[]),{portReady:S,mode:C,setMode:O,post:E}=oe(T,B);i.useEffect(()=>{if(!a)return;const e=c=>{$(c.target)||W(c.target)||o(null)};return document.addEventListener("mousedown",e),()=>document.removeEventListener("mousedown",e)},[a]);const A=i.useRef(null);if(A.current===null){const e=getComputedStyle(document.querySelector(".cds-root")??document.documentElement).getPropertyValue("--cds-fill-accent").trim();A.current=e||"#2a78d6"}i.useEffect(()=>{S&&E({kind:"highlight",badgeColor:A.current??void 0,items:s.filter(e=>e.type==="html_element"&&e.element_selector).map(e=>({id:e.id,selector:e.element_selector,label:V(e.label),text:e.text}))})},[S,s,E]);const Z=i.useCallback(()=>{const e=!C;O(e),e||n(null)},[C,O]),Y=i.useCallback(e=>{d&&(l({element_selector:d.selector,element_descriptor:d.descriptor,selection_text:d.elementText||null,x_percent:d.x_percent,y_percent:d.y_percent,text:e}),n(null))},[d,l]),R=i.useCallback(()=>{n(null),o(null)},[]);return m.jsxs("div",{ref:h,className:"relative h-full w-full",children:[m.jsx(J,{artifactId:t,versionId:r,transformHtml:z,overlay:m.jsx(m.Fragment,{children:m.jsxs("button",{type:"button",onClick:Z,disabled:!S,title:C?"Exit annotate mode":"Annotate element",className:`pointer-events-auto absolute top-2 right-2 flex items-center gap-1.5 px-2 py-1 text-xs rounded-md border shadow-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${C?"bg-fill-accent text-oncolor-100 border-accent":"bg-bg-000 text-text-200 border-border-200 hover:bg-bg-200"}`,children:[m.jsx(K,{size:12}),C?"Annotating…":"Annotate"]})})}),d&&m.jsx(L,{anchorX:d.anchorX,anchorY:d.anchorY,mode:"create",onSave:Y,onCancel:R}),a&&m.jsx(L,{anchorX:a.anchorX,anchorY:a.anchorY,mode:"view",annotation:a.annotation,onDelete:e=>{b(e),o(null)},onSaveEdit:y?(e,c)=>{y(e,c),o(f=>f&&{...f,annotation:{...f.annotation,text:c}})}:void 0,onCancel:R})]})}export{he as HtmlAnnotationOverlay};
