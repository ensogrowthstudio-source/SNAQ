/* ============================================================
   SNAQ v5 · motion.js (A3)
   window.SNAQMotion = { init(root), change(from,to,dir), explode(i,open), refresh(), destroy() }
   Doar animatie. Nu tine stare (index activ, swipe, ARIA = A2). Necesita window.gsap (+ ScrollTrigger optional).
   Contractul DOM si toti tokenii: vezi MOTION-SPEC.md.
   ============================================================ */
(function () {
  'use strict';
  var g = window.gsap;
  if (!g) { if (window.console) console.warn('[SNAQMotion] gsap lipseste, site-ul merge fara animatii'); return; }
  if (window.ScrollTrigger) g.registerPlugin(window.ScrollTrigger);

  /* ---------- tokeni (plan-v5 §6) ---------- */
  var T = { fast: 0.18, mid: 0.4, slow: 0.65, stagger: 0.06 };
  var E = { fast: 'power2.out', mid: 'power3.out', slow: 'expo.out' };

  /* ---------- stare interna (doar de animatie) ---------- */
  var root, doc, wordWrap, wordSpan, tabs = [], stage, cta, prods = [], active = 0;
  var reduced = false, saveData = false, slowNet = false, inView = true, inited = false;
  var tlIntro = null, tlChange = null, idle = null, idleEls = null, scrollTl = null, io = null, ro = null;
  var cleanups = [], lastCall = {};

  function noop() {}
  function qs(el, sel) { return el.querySelector(sel); }
  function qa(el, sel) { return Array.prototype.slice.call(el.querySelectorAll(sel)); }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function wc(list, on) {
    (Array.isArray(list) ? list : [list]).forEach(function (el) { if (el) el.style.willChange = on ? 'transform, opacity' : ''; });
  }
  function dedupe(key, ms) {
    var now = performance.now();
    if (lastCall[key.k] === key.v && now - (lastCall[key.k + 't'] || 0) < (ms || 60)) return true;
    lastCall[key.k] = key.v; lastCall[key.k + 't'] = now; return false;
  }

  /* ---------- masca roll-up ---------- */
  function wrapRoll(el) {
    if (!el) return null;
    var mask = qs(el, ':scope > .mx-mask');
    if (mask) return mask.firstElementChild;
    mask = doc.createElement('span'); mask.className = 'mx-mask';
    var roll = doc.createElement('span'); roll.className = 'mx-roll';
    while (el.firstChild) roll.appendChild(el.firstChild);
    mask.appendChild(roll); el.appendChild(mask);
    return roll;
  }

  /* ---------- model produs ---------- */
  function buildProd(el) {
    var p = { el: el, i: +el.dataset.i };
    p.visual = qs(el, '.prod__visual');
    p.hero = qs(el, '.prod__hero');
    p.loop = qs(el, '.prod__loop');
    p.layersWrap = qs(el, '.prod__layers');
    p.layerEls = p.layersWrap ? qa(p.layersWrap, '.layer').sort(function (a, b) { return +a.dataset.layer - +b.dataset.layer; }) : [];
    p.labelsUl = qs(el, '.prod__labels');
    p.labelEls = p.labelsUl ? qa(p.labelsUl, 'li').sort(function (a, b) { return +a.dataset.layer - +b.dataset.layer; }) : [];
    p.info = qs(el, '.prod__info');
    p.infoItems = p.info ? Array.prototype.slice.call(p.info.children) : [];
    p.nameEl = qs(el, '.prod__name'); p.priceEl = qs(el, '.prod__price');
    p.nameRoll = wrapRoll(p.nameEl); p.priceRoll = wrapRoll(p.priceEl);
    p.open = false; p.tl = null; p.geom = null; p._ready = null;
    p.labelEls.forEach(function (li) {
      if (!qs(li, ':scope > .mx-line')) {
        var ln = doc.createElement('i'); ln.className = 'mx-line'; ln.setAttribute('aria-hidden', 'true');
        li.insertBefore(ln, li.firstChild);
      }
      li._line = qs(li, ':scope > .mx-line');
    });
    if (p.loop) g.set(p.loop, { opacity: 0 });
    return p;
  }

  /* ============================================================
     GEOMETRIE STRATURI
     Prioritate: atribute pe .layer (data-cx, data-ey, data-w, data-h, fractiuni din cutia vizuala)
              > window.SNAQ_LAYERS[slug] (continutul lui layers.json)
              > fetch(.prod__layers[data-json])
              > fallback egal distribuit dupa dimensiunile naturale.
     ============================================================ */
  function ready(p) {
    if (p._ready) return p._ready;
    var ps = [];
    p.layerEls.forEach(function (img) {
      if (!img.getAttribute('src') && img.dataset.src) img.src = img.dataset.src;
      img.loading = 'eager';
      if (img.decode) ps.push(img.decode().catch(noop));
      else ps.push(new Promise(function (r) { if (img.complete) r(); else { img.onload = img.onerror = r; } }));
    });
    var js = p.layersWrap && p.layersWrap.dataset.json;
    if (js && !(window.SNAQ_LAYERS && window.SNAQ_LAYERS[p.el.dataset.slug]) && window.fetch) {
      ps.push(fetch(js).then(function (r) { return r.json(); }).then(function (j) {
        window.SNAQ_LAYERS = window.SNAQ_LAYERS || {}; window.SNAQ_LAYERS[p.el.dataset.slug] = j;
      }).catch(noop));
    }
    var to = new Promise(function (r) { setTimeout(r, 1200); });
    p._ready = Promise.race([Promise.all(ps), to]);
    return p._ready;
  }

  function compute(p) {
    var els = p.layerEls, n = els.length;
    var Wb = p.visual.offsetWidth, Hb = p.visual.offsetHeight;
    var json = window.SNAQ_LAYERS && window.SNAQ_LAYERS[p.el.dataset.slug];
    var jl = json && json.layers;
    var data = els.map(function (el, k) {
      var d = el.dataset, ex = jl && jl[k] && jl[k].exploded;
      if (d.w && d.ey && d.cx && d.h) return { cx: +d.cx, cy: +d.ey, w: +d.w, h: +d.h, ay: d.ay ? +d.ay : null };
      if (ex) return { cx: ex.cx, cy: ex.cy, w: ex.w, h: ex.h, ay: null };
      var nw = el.naturalWidth || 1, nh = el.naturalHeight || 1;
      var w = 0.5, h = w * (nh / nw) * (Wb / Math.max(Hb, 1));
      return { cx: 0.5, cy: 0.12 + (n > 1 ? k * (0.76 / (n - 1)) : 0.38), w: w, h: h, ay: null };
    });
    var maxW = Math.max.apply(null, data.map(function (d) { return d.w; })) || 0.5;
    var heroW = parseFloat(p.layersWrap.dataset.heroW) || 0.78;
    var heroCy = parseFloat(p.layersWrap.dataset.heroCy) || 0.58;
    var labelX = parseFloat(p.layersWrap.dataset.labelX) || 0.62;
    var A = clamp(heroW / maxW, 1, 1.9);
    var Xc = (labelX - 0.04) / 2 + 0.01;               // centrul coloanei de straturi (stanga de coloana de etichete)
    var s = Math.min(1, (labelX - 0.06) / maxW);
    var y = 0, pos = data.map(function (d) { var h = d.h * A, r = { top: y, h: h }; y += h * 0.7; return r; });
    var last = pos[pos.length - 1], mid = (pos[0].top + last.top + last.h) / 2, shift = heroCy - mid;
    data.forEach(function (d, k) {
      var ay = d.ay != null ? d.ay : pos[k].top + pos[k].h / 2 + shift;
      d.ay = ay;
      d.baseX = 0.5 + (d.cx - 0.5) * A;                // fractie din Wb, pozitia 'left' in starea asamblata
      d.tx = (Xc + (d.cx - 0.5) * s - d.baseX) * Wb;   // px de translatat pana in coloana explodata
      d.ty = (d.cy - ay) * Hb;
      d.right = Xc + (d.cx - 0.5) * s + d.w * s / 2;   // marginea dreapta a stratului (fractie din Wb) in starea explodata
    });
    return { data: data, A: A, s: s, Wb: Wb, Hb: Hb, labelX: labelX };
  }

  function place(p) {            // pune straturile in starea asamblata (invizibile pana la explode)
    p.geom = compute(p);
    p.layerEls.forEach(function (el, k) {
      var d = p.geom.data[k];
      g.set(el, { left: d.baseX * 100 + '%', top: d.ay * 100 + '%', width: d.w * 100 + '%', xPercent: -50, yPercent: -50, x: 0, y: 0, scale: p.geom.A, opacity: 1, zIndex: p.layerEls.length - k });
    });
  }

  function placeLabels(p) {      // pozitii etichete (stanga/sus) + lungimea firului
    var m = p.labelEls.length, G = p.geom, hasLayers = G && p.layerEls.length > 0;
    p.labelEls.forEach(function (li, k) {
      var d = hasLayers && G.data[k];
      var top, left, line = 0;
      if (d) {
        top = d.cy; left = G.labelX;
        line = Math.max(10, (left - d.right) * G.Wb - 4);
        li.classList.remove('mx-noline');
      } else {
        top = 0.16 + (m > 1 ? k * (0.68 / (m - 1)) : 0.34); left = 0.14;
        li.classList.add('mx-noline');
      }
      li.style.top = top * 100 + '%'; li.style.left = left * 100 + '%';
      var r = p.visual.getBoundingClientRect(), vw = doc.documentElement.clientWidth;
      li.style.maxWidth = Math.max(80, Math.round(vw - (r.left + left * r.width) - 10)) + 'px';
      li.style.setProperty('--mx-line', line + 'px');
      g.set(li, { yPercent: -50 });
    });
  }

  /* ============================================================
     IDLE (respiratie) + VIDEO
     ============================================================ */
  function stopIdle() {
    if (idle) { idle.kill(); idle = null; }
    if (idleEls) { g.set(idleEls, { y: 0 }); idleEls = null; }
  }
  function startIdle() {
    stopIdle();
    if (reduced) return;
    var p = prods[active]; if (!p || p.open || tlChange || tlIntro) return;
    var els = [p.hero, p.loop].filter(Boolean); if (!els.length) return;
    idleEls = els;
    idle = g.to(els, {
      y: -4, duration: 1, ease: 'sine.inOut',
      onComplete: function () {
        idle = g.to(els, { y: 4, duration: 2, ease: 'sine.inOut', yoyo: true, repeat: -1 });
        if (!inView) idle.pause();
      }
    });
    if (!inView) idle.pause();
  }

  function netOk() {
    var c = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    saveData = !!(c && c.saveData);
    slowNet = !!(c && c.effectiveType && /(^|-)(2g|3g)$/.test(c.effectiveType));
    return !saveData && !slowNet && !reduced;
  }
  function videoPrepare(p) {
    var v = p && p.loop; if (!v || !netOk()) return;
    if (!v.getAttribute('src') && v.dataset.src) { v.preload = 'metadata'; v.src = v.dataset.src; v.load(); }
  }
  function videoPlay(p) {
    var v = p && p.loop; if (!v || !netOk() || !inView || p.open) return;
    videoPrepare(p);
    if (!v.getAttribute('src')) return;
    var pr; try { pr = v.play(); } catch (e) { return; }
    if (pr && pr.then) pr.then(function () { g.to(v, { opacity: 1, duration: T.mid, ease: E.mid, overwrite: 'auto' }); }).catch(noop);
  }
  function videoPause(p) { var v = p && p.loop; if (v && !v.paused) v.pause(); }
  function videoStopAll() { prods.forEach(videoPause); }

  /* ============================================================
     INTRO
     ============================================================ */
  function introInfoTargets(p) {
    var plain = [], rolls = [];
    p.infoItems.forEach(function (it) {
      if (it === p.nameEl) rolls.push({ box: it, roll: p.nameRoll });
      else if (it === p.priceEl) rolls.push({ box: it, roll: p.priceRoll });
      else plain.push(it);
    });
    return { plain: plain, rolls: rolls };
  }

  function intro() {
    var p = prods[active]; if (!p) return;
    var H = window.innerHeight;
    var tl = g.timeline({ onComplete: introDone });
    tlIntro = tl;
    var setl = [wordSpan, p.visual].concat(tabs, cta, p.infoItems).filter(Boolean);
    wc(setl, true);

    g.set(wordSpan, { transformOrigin: '50% 100%', scaleY: 1.6, opacity: 0 });
    g.set(p.visual, { transformOrigin: '50% 94%', y: -Math.round(H * 0.55), opacity: 0 });
    g.set(tabs, { y: 14, opacity: 0 });
    var it = introInfoTargets(p);
    g.set(it.plain, { y: 14, opacity: 0 });
    it.rolls.forEach(function (r) { g.set(r.box, { opacity: 1 }); g.set(r.roll, { yPercent: 108 }); });
    if (cta) g.set(cta, { y: 14, opacity: 0 });
    doc.documentElement.classList.remove('mx-pre');       // acelasi tick: nu clipeste

    // SMASH: presa pe plita
    tl.to(wordSpan, { opacity: 1, duration: 0.14, ease: 'none' }, 0)
      .to(wordSpan, { scaleY: 1, duration: 0.46, ease: 'back.out(2.4)' }, 0);
    // burgerul cade si aterizeaza cu squash
    tl.to(p.visual, { opacity: 1, duration: 0.1, ease: 'none' }, 0.12)
      .to(p.visual, { y: 0, duration: 0.36, ease: 'power3.in' }, 0.12)
      .to(p.visual, { scaleY: 0.93, scaleX: 1.045, duration: 0.07, ease: 'power2.out' }, 0.48)
      .to(p.visual, { scaleY: 1, scaleX: 1, duration: 0.36, ease: 'back.out(3.2)' }, 0.55)
      .to(wordSpan, { scaleY: 0.955, duration: 0.07, ease: 'power2.out' }, 0.48)
      .to(wordSpan, { scaleY: 1, duration: 0.32, ease: 'back.out(3)' }, 0.55);
    // tab-uri si informatii, stagger 60 ms
    tl.to(tabs, { y: 0, opacity: 1, duration: T.mid, ease: E.mid, stagger: T.stagger }, 0.42);
    var t = 0.54;
    it.plain.forEach(function (el, k) { tl.to(el, { y: 0, opacity: 1, duration: T.mid, ease: E.mid }, t + k * T.stagger); });
    it.rolls.forEach(function (r, k) {
      var idx = p.infoItems.indexOf(r.box);
      tl.to(r.roll, { yPercent: 0, duration: 0.5, ease: E.slow }, t + idx * T.stagger);
    });
    if (cta) tl.to(cta, { y: 0, opacity: 1, duration: T.mid, ease: E.mid }, t + p.infoItems.length * T.stagger);
  }
  function introDone() {
    var p = prods[active];
    var list = [wordSpan, p && p.visual].concat(tabs, cta, p ? p.infoItems : []).filter(Boolean);
    g.set(list, { clearProps: 'transform,opacity,willChange,transformOrigin' });
    if (p) { g.set(p.nameRoll, { clearProps: 'transform' }); g.set(p.priceRoll, { clearProps: 'transform' }); }
    tlIntro = null;
    startIdle(); videoPlay(p); warm();
  }

  /* ============================================================
     CHANGE
     ============================================================ */
  function settle() {
    if (tlIntro) { tlIntro.progress(1); }
    if (tlChange) { tlChange.progress(1); }
  }
  function closeNow(p) {
    if (!p || (!p.open && !p.tl)) return;
    if (p.tl) { p.tl.kill(); p.tl = null; }
    p.open = false;
    if (p.layersWrap) g.set(p.layersWrap, { autoAlpha: 0 });
    p.labelEls.forEach(function (li) { g.set(li, { opacity: 0, visibility: 'hidden', x: 0 }); if (li._line) g.set(li._line, { scaleX: 0 }); });
    var heroEls = [p.hero].filter(Boolean);
    g.set(heroEls, { clearProps: 'opacity' });
    g.set(p.visual, { clearProps: 'transform,transformOrigin' });
    wc(heroEls, false);
  }

  function resetProd(p) {
    if (!p) return;
    var list = [p.visual].concat(p.infoItems);
    g.set(list, { clearProps: 'transform,opacity,willChange,transformOrigin' });
    g.set(p.el, { clearProps: 'opacity,willChange' });
    g.set(p.nameRoll, { clearProps: 'transform' }); g.set(p.priceRoll, { clearProps: 'transform' });
    p.el.classList.remove('is-leaving', 'is-entering');
  }

  function change(from, to, dir) {
    from = +from; to = +to;
    if (!inited || from === to) return;
    if (dedupe({ k: 'change', v: from + '>' + to }, 80)) return;
    var A = byIndex(from), B = byIndex(to); if (!A || !B) return;
    if (!dir) dir = to > from ? 1 : -1;
    dir = dir > 0 ? 1 : -1;
    settle(); closeNow(A); closeNow(B);
    stopIdle(); videoStopAll();
    active = to;
    if (A.el === B.el) return;

    if (reduced) { crossfade(A, B); return; }

    A.el.classList.add('is-leaving'); B.el.classList.add('is-entering');
    var W = (stage && stage.offsetWidth) || window.innerWidth;
    var tl = g.timeline({ onComplete: function () { endChange(A, B); } });
    tlChange = tl;
    wc([A.visual, B.visual, wordSpan].concat(A.infoItems, B.infoItems), true);

    // vechi: iese in directia swipe-ului
    g.set(A.visual, { transformOrigin: '50% 90%' }); g.set(B.visual, { transformOrigin: '50% 90%' });
    tl.to(A.visual, { x: -dir * W * 0.55, rotation: -dir * 9, scale: 0.9, duration: 0.36, ease: 'power2.in' }, 0)
      .to(A.visual, { opacity: 0, duration: 0.24, ease: 'power1.in' }, 0.06)
      .to(A.infoItems, { opacity: 0, y: -10, duration: T.fast, ease: E.fast }, 0);

    // nou: intra din partea opusa cu un mic bounce
    g.set(B.visual, { x: dir * W * 0.6, rotation: dir * 8, scale: 0.92, opacity: 0 });
    var it = introInfoTargets(B);
    g.set(it.plain, { y: 14, opacity: 0 });
    it.rolls.forEach(function (r) { g.set(r.box, { opacity: 1 }); g.set(r.roll, { yPercent: 108 }); });
    tl.to(B.visual, { opacity: 1, duration: 0.2, ease: 'power1.out' }, 0.16)
      .to(B.visual, { x: 0, rotation: 0, scale: 1, duration: 0.49, ease: 'back.out(1.5)' }, 0.16);

    // SMASH din spate: thump + parallax
    g.set(wordSpan, { transformOrigin: '50% 100%' });
    tl.fromTo(wordSpan, { x: dir * 34 }, { x: 0, duration: T.slow, ease: E.slow }, 0.08)
      .to(wordSpan, { scaleY: 0.92, duration: 0.07, ease: 'power2.out' }, 0.3)
      .to(wordSpan, { scaleY: 1, duration: 0.4, ease: 'back.out(2.6)' }, 0.37);

    // roll-up nume/pret + restul informatiilor, stagger 60 ms
    var t0 = 0.14;
    it.plain.forEach(function (el) {
      var idx = B.infoItems.indexOf(el);
      tl.to(el, { y: 0, opacity: 1, duration: T.mid, ease: E.mid }, t0 + idx * T.stagger);
    });
    it.rolls.forEach(function (r) {
      var idx = B.infoItems.indexOf(r.box);
      tl.to(r.roll, { yPercent: 0, duration: 0.45, ease: E.slow }, t0 + idx * T.stagger);
    });
  }
  function endChange(A, B) {
    tlChange = null;
    resetProd(A); resetProd(B);
    g.set(wordSpan, { clearProps: 'transform,willChange,transformOrigin' });
    startIdle(); videoPlay(B);
  }
  function crossfade(A, B) {
    A.el.classList.add('is-leaving'); B.el.classList.add('is-entering');
    var tl = g.timeline({ onComplete: function () { tlChange = null; resetProd(A); resetProd(B); startIdle(); videoPlay(B); } });
    tlChange = tl;
    g.set(B.el, { opacity: 0 });
    tl.to(A.el, { opacity: 0, duration: 0.15, ease: 'none' }, 0).to(B.el, { opacity: 1, duration: 0.15, ease: 'none' }, 0);
  }
  function byIndex(i) { for (var k = 0; k < prods.length; k++) if (prods[k].i === i) return prods[k]; return null; }

  /* ============================================================
     EXPLODE ("Ce are?")
     ============================================================ */
  function explode(i, open) {
    i = +i; open = !!open;
    if (!inited) return;
    if (dedupe({ k: 'explode', v: i + ':' + open }, 80)) return;
    var p = byIndex(i); if (!p || p.open === open) return;
    if (tlChange) tlChange.progress(1);
    if (open) { openIt(p); } else { closeIt(p); }
  }

  function openIt(p) {
    p.open = true;
    stopIdle(); videoPause(p);
    if (p.tl) { p.tl.kill(); p.tl = null; }
    var hasLayers = p.layerEls.length > 0;
    var go = function () {
      if (!p.open) return;                                    // inchis intre timp
      if (hasLayers && (!p.geom || p.geom.Wb !== p.visual.offsetWidth)) { place(p); }
      if (!hasLayers) p.geom = null;
      placeLabels(p);
      var G = p.geom, heroEls = [p.hero, p.loop].filter(Boolean);
      var tl = g.timeline({ onComplete: function () { p.tl = null; wc(p.layerEls, false); } });
      p.tl = tl;
      wc(p.layerEls.concat(heroEls), true);
      g.set(p.labelEls, { visibility: 'visible' });

      if (reduced) {
        if (hasLayers) {
          g.set(p.layersWrap, { autoAlpha: 1 });
          p.layerEls.forEach(function (el, k) { g.set(el, { x: G.data[k].tx, y: G.data[k].ty, scale: G.s }); });
          g.set(heroEls, { opacity: 0 });
        } else g.set(heroEls, { opacity: 0.28 });
        g.set(p.labelEls, { opacity: 1, x: 0, visibility: 'visible' });
        p.labelEls.forEach(function (li) { if (li._line) g.set(li._line, { scaleX: 1 }); });
        p.tl = null; return;
      }

      if (hasLayers) {
        tl.to(p.layersWrap, { autoAlpha: 1, duration: 0.12, ease: 'none' }, 0)
          .to(heroEls, { opacity: 0, duration: 0.16, ease: 'power1.out' }, 0.06);
        p.layerEls.forEach(function (el, k) {
          var d = G.data[k];
          tl.to(el, { x: d.tx, y: d.ty, scale: G.s, duration: T.slow + 0.1, ease: 'expo.out' }, 0.14 + k * T.stagger);
        });
      } else {
        tl.to(heroEls, { opacity: 0.28, duration: T.mid, ease: E.mid }, 0);
      }
      var base = hasLayers ? 0.38 : 0.1;
      p.labelEls.forEach(function (li, k) {
        var t = base + k * T.stagger;
        tl.fromTo(li, { opacity: 0, x: -8 }, { opacity: 1, x: 0, duration: T.mid, ease: E.mid }, t);
        if (li._line) tl.fromTo(li._line, { scaleX: 0 }, { scaleX: 1, duration: T.mid, ease: E.mid }, t);
      });
    };
    if (hasLayers) ready(p).then(go); else go();
  }

  function closeIt(p) {
    p.open = false;
    if (p.tl) { p.tl.kill(); p.tl = null; }
    var hasLayers = p.layerEls.length > 0, G = p.geom, heroEls = [p.hero, p.loop].filter(Boolean);
    if (reduced) {
      closeNow(p); g.set(p.labelEls, { clearProps: 'x' }); startIdle(); videoPlay(p); return;
    }
    var tl = g.timeline({ onComplete: function () { p.tl = null; closeNow(p); wc(p.layerEls, false); startIdle(); videoPlay(p); } });
    p.tl = tl;
    wc(heroEls.concat(p.visual), true);
    // etichetele se sting repede, de jos in sus
    tl.to(p.labelEls, { opacity: 0, duration: 0.16, ease: 'power1.in', stagger: { each: 0.025, from: 'end' } }, 0);
    if (p.labelEls.length) tl.to(qa(p.labelsUl, '.mx-line'), { scaleX: 0, duration: 0.16, ease: 'power1.in' }, 0);
    var T0 = 0.06, TE;
    if (hasLayers && G) {
      var n = p.layerEls.length;
      p.layerEls.forEach(function (el, k) {   // reasamblare de jos in sus
        tl.to(el, { x: 0, y: 0, scale: G.A, duration: 0.5, ease: 'power3.inOut' }, T0 + (n - 1 - k) * T.stagger);
      });
      TE = T0 + (n - 1) * T.stagger + 0.5;
      // crossfade spre imaginea asamblata chiar inainte de slam
      tl.to(heroEls, { opacity: 1, duration: 0.14, ease: 'power1.out' }, TE - 0.12)
        .to(p.layersWrap, { autoAlpha: 0, duration: 0.1, ease: 'none' }, TE);
    } else {
      TE = 0.3;
      tl.to(heroEls, { opacity: 1, duration: T.mid, ease: E.mid }, 0);
    }
    // slam final: squash mic pe plita
    g.set(p.visual, { transformOrigin: '50% 92%' });
    tl.to(p.visual, { scaleY: 0.94, scaleX: 1.03, duration: 0.08, ease: 'power2.out' }, TE - 0.04)
      .to(p.visual, { scaleY: 1, scaleX: 1, duration: 0.42, ease: 'back.out(3.2)' }, TE + 0.04);
  }

  /* ============================================================
     PRELOAD (liniste, dupa intro)
     ============================================================ */
  function warm() {
    if (!netOk()) return;
    var idl = window.requestIdleCallback || function (f) { return setTimeout(f, 400); };
    idl(function () {
      var p = prods[active]; if (p) { ready(p); }
      setTimeout(function () { prods.forEach(function (q) { if (q !== p) ready(q); }); }, 1500);
    });
  }

  /* ============================================================
     SCROLL: un singur efect discret + reveal-uri o singura data
     ============================================================ */
  function setupScroll() {
    if (reduced || !window.ScrollTrigger) return;
    scrollTl = g.timeline({
      defaults: { ease: 'none' },
      scrollTrigger: { trigger: root, start: 'top top', end: 'bottom top', scrub: 0.5, invalidateOnRefresh: true }
    });
    if (stage) scrollTl.to(stage, { scale: 0.86, y: -24, transformOrigin: '50% 35%' }, 0);
    if (wordWrap) scrollTl.to(wordWrap, { y: function () { return root.offsetHeight * 0.14; }, opacity: 0.35 }, 0);
  }
  function setupReveals() {
    if (reduced || !window.ScrollTrigger) return;
    var sel = '[data-reveal], main > section:not(#hero), body > section:not(#hero)';
    var vh = window.innerHeight;
    qa(doc, sel).forEach(function (el) {
      if (root.contains(el) || el.dataset.mxDone) return;
      el.dataset.mxDone = '1';
      var kids = el.dataset.reveal === 'stagger' ? Array.prototype.slice.call(el.children) : [el];
      var top = el.getBoundingClientRect().top;
      if (top < vh * 0.9) return;                              // deja vizibil: nu-l ascundem
      g.set(kids, { y: 24, opacity: 0 });
      window.ScrollTrigger.create({
        trigger: el, start: 'top 88%', once: true,
        onEnter: function () {
          g.to(kids, { y: 0, opacity: 1, duration: T.mid, ease: E.mid, stagger: T.stagger, clearProps: 'transform,opacity' });
        }
      });
    });
  }

  /* ============================================================
     INIT
     ============================================================ */
  function on(target, ev, fn, opt) { target.addEventListener(ev, fn, opt); cleanups.push(function () { target.removeEventListener(ev, fn, opt); }); }

  function init(r) {
    if (inited) return;
    root = r || document.getElementById('hero');
    if (!root) return;
    doc = root.ownerDocument;
    var mq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
    reduced = !!(mq && mq.matches);
    if (mq) {
      var mqf = function (e) {
        reduced = e.matches;
        if (reduced) { settle(); stopIdle(); videoStopAll(); if (scrollTl) { scrollTl.scrollTrigger && scrollTl.scrollTrigger.kill(); scrollTl.kill(); scrollTl = null; g.set([stage, wordWrap], { clearProps: 'transform,opacity' }); } }
        else { startIdle(); }
      };
      if (mq.addEventListener) mq.addEventListener('change', mqf); else if (mq.addListener) mq.addListener(mqf);
    }
    netOk();

    wordWrap = qs(root, '.hero__word'); wordSpan = wordWrap && qs(wordWrap, 'span');
    tabs = qa(root, '.hero__tab'); stage = qs(root, '.hero__stage'); cta = qs(root, '.hero__cta');
    prods = qa(root, '.prod').map(buildProd);
    active = +(root.dataset.active || 0);
    var isActiveEl = qs(root, '.prod.is-active'); if (isActiveEl) active = +isActiveEl.dataset.i;
    inited = true;

    // hero in viewport? (idle + video doar cand se vede)
    if ('IntersectionObserver' in window) {
      io = new IntersectionObserver(function (es) {
        inView = es[0].isIntersecting;
        if (inView) { if (idle) idle.resume(); else startIdle(); videoPlay(prods.filter(function (q) { return q.i === active; })[0]); }
        else { if (idle) idle.pause(); videoStopAll(); }
      }, { threshold: 0.15 });
      io.observe(root);
    }
    // resize: straturile deschise isi recalculeaza pozitiile
    if ('ResizeObserver' in window) {
      var raf = 0;
      ro = new ResizeObserver(function () {
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(function () {
          prods.forEach(function (p) {
            if (!p.open || p.tl || !p.layerEls.length || !p.geom) return;
            place(p); placeLabels(p);
            p.layerEls.forEach(function (el, k) { g.set(el, { x: p.geom.data[k].tx, y: p.geom.data[k].ty, scale: p.geom.s }); });
            g.set(p.layersWrap, { autoAlpha: 1 });
          });
        });
      });
      prods.forEach(function (p) { if (p.visual) ro.observe(p.visual); });
    }

    // evenimentele din contract (A2 le emite) — dedupe protejeaza daca A2 apeleaza si API-ul direct
    on(root, 'hero:change', function (e) {
      var d = e.detail || {}; var from = +d.from, to = +d.to, n = prods.length, dir = d.dir;
      if (!dir) { dir = to > from ? 1 : -1; if (n > 2 && Math.abs(to - from) === n - 1) dir = -dir; }
      change(from, to, dir);
    });
    on(root, 'hero:explode', function (e) { var d = e.detail || {}; explode(d.i, d.open); });
    on(doc, 'visibilitychange', function () { if (doc.hidden) videoStopAll(); else videoPlay(byIndex(active)); });

    var fresh = (window.scrollY || 0) < 200;
    if (reduced || !fresh) {
      doc.documentElement.classList.remove('mx-pre');
      startIdle(); warm();
    } else {
      intro();
    }
    videoPrepare(byIndex(active));
    setupScroll(); setupReveals();
    if (window.ScrollTrigger) window.addEventListener('load', function () { window.ScrollTrigger.refresh(); });
  }

  function refresh() { if (window.ScrollTrigger) window.ScrollTrigger.refresh(); }
  function destroy() {
    settle(); stopIdle(); videoStopAll();
    cleanups.forEach(function (f) { f(); }); cleanups = [];
    if (io) io.disconnect(); if (ro) ro.disconnect();
    if (scrollTl) { scrollTl.scrollTrigger && scrollTl.scrollTrigger.kill(); scrollTl.kill(); }
    prods.forEach(closeNow); inited = false;
  }

  window.SNAQMotion = { init: init, change: change, explode: explode, refresh: refresh, destroy: destroy, version: '1.0.0' };
})();
