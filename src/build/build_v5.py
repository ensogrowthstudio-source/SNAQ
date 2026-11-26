#!/usr/bin/env python3
"""A4 · build_v5.py — integreaza A2 (ux/v5.template.html + produse), A3 (type.css, motion.css, motion.js, GSAP)
si A1 (imagini) intr-un singur HTML autonom (CSS, JS, fonturi base64 inline) + imagini/video ca fisiere alaturate.

  python3 build/build_v5.py            # imagini (daca lipsesc/sunt vechi) + html + dist/
  python3 build/build_v5.py --images   # forteaza regenerarea imaginilor

Iesiri:  build/snaq-demo-v5.html   (acelasi fisier ca dist/index.html)
         build/dist/index.html, build/dist/img/**, build/dist/media/*.mp4
Ordinea transformarilor: 1) placeholdere A2 (taburi, produse, platforme, meniu)  2) CSS/JS inline  3) regex pe cai de imagini
                         4) harta JSON a straturilor (la final, ca regex-urile sa n-o atinga).
Fiecare inlocuire e verificata cu assert pe numarul de aparitii."""
import base64, html, json, re, shutil, subprocess, sys
from pathlib import Path

B = Path(__file__).resolve().parent
ROOT = B.parent
UX, MO = ROOT / "ux", ROOT / "motion"
FONTS = ROOT / "src/site/src/fonts"
IMG = B / "img"
DIST = B / "dist"
E = lambda s: html.escape(str(s), quote=True)

# ------------------------------------------------------------------ utilitare
def sub1(text, old, new, count=1, label=""):
    n = text.count(old)
    assert n == count, f"[{label or old[:50]!r}] asteptat {count} aparitii, gasit {n}"
    return text.replace(old, new)

def rx(text, pattern, new, count, flags=re.S, label=""):
    out, n = re.subn(pattern, new, text, flags=flags)
    assert n == count, f"[{label or pattern[:50]!r}] regex: asteptat {count}, gasit {n}"
    return out

def b64(path, mime):
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()

# ------------------------------------------------------------------ imagini
if "--images" in sys.argv or not (IMG / "meta.json").exists():
    subprocess.run([sys.executable, str(B / "tools/make_images.py")], check=True)
meta = json.loads((IMG / "meta.json").read_text())
P = json.loads((B / "products.v5.json").read_text(encoding="utf-8"))
loops = json.loads((B / "media/loops.json").read_text())
products, N = P["products"], len(P["products"])

def fm(x): return f"{x:.2f}".replace(".", ",")

HERO_SIZES = "(min-width:900px) 52vw, 100vw"
LAYER_SIZES = "(min-width:900px) 30vw, 72vw"

SVG_PLUS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>'
SVG_PAUSE = '<svg class="i-pause" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg><svg class="i-play" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4l13 8-13 8z"/></svg>'
SVG_ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'

def hero_srcset(slug, ext):
    return f"img/{slug}/hero-600.{ext} 600w, img/{slug}/hero-1000.{ext} 1000w"

tabs, prods = [], []
for i, p in enumerate(products):
    slug = p["slug"]; first = i == 0
    a, b = p["name_split"]
    tabs.append(
        f'    <button role="tab" class="hero__tab" id="tab-{i}" data-i="{i}" aria-selected="{"true" if first else "false"}" aria-controls="panel-{i}" tabindex="{0 if first else -1}">'
        f'<span class="w" data-n="{i+1:02d}">{E(a)}</span> <span class="w">{E(b)}</span></button>')
    hm = meta["hero"][slug]
    # produsul activ: srcset real (preload scanner); celelalte: data-srcset, hidratate dupa intro (glue.js)
    at = "srcset" if first else "data-srcset"
    sz = "sizes" if first else "data-sizes"
    hero_pic = (f'<picture><source type="image/avif" {at}="{hero_srcset(slug, "avif")}" {sz}="{HERO_SIZES}">'
                f'<img class="prod__hero" alt="{E(p["alt"])}" width="{hm["w"]}" height="{hm["h"]}" decoding="async" '
                f'{at}="{hero_srcset(slug, "webp")}" {sz}="{HERO_SIZES}"'
                f'{" fetchpriority=\"high\"" if first else ""}></picture>')
    layers = []
    for l in meta["layers"][slug]:
        k = l["k"]
        def ss(ext): return f"img/{slug}/layer_{k:02d}-s.{ext} {l['ws']}w, img/{slug}/layer_{k:02d}.{ext} {l['w']}w"
        layers.append(
            f'<picture><source type="image/avif" data-srcset="{ss("avif")}" data-sizes="{LAYER_SIZES}">'
            f'<img class="layer" data-layer="{k}" alt="" width="{l["w"]}" height="{l["h"]}" decoding="async" '
            f'data-srcset="{ss("webp")}" data-sizes="{LAYER_SIZES}"></picture>')
    assert len(layers) == len(p["layers"]), f"{slug}: {len(layers)} straturi reale vs {len(p['layers'])} etichete"
    labels = [f'<li data-layer="{k}"><span>{E(l["label"])}</span></li>' for k, l in enumerate(p["layers"])]
    lc = loops[slug]["css"]
    loop = (f'<div class="prod__loopwrap"><div class="prod__loopin" style="{";".join(f"{k}:{v}" for k, v in lc.items())}"><video class="prod__loop" muted playsinline loop preload="none" aria-hidden="true" tabindex="-1" '
            f'data-src="media/{slug}.mp4" data-poster="img/{slug}/hero-1000.avif"></video></div></div>\n'
            f'        <button class="prod__pause" type="button" aria-label="Pune pe pauză animația" aria-pressed="false" hidden>{SVG_PAUSE}</button>')
    fit = p.get("hero_fit", {"trim": .14, "bottom": .85})
    vis_style = f"--img-trim:{fit['trim']};--burger-bottom:{fit['bottom']}"
    prods.append(f'''    <article class="prod{' is-active' if first else ''}" id="panel-{i}" data-i="{i}" data-slug="{E(slug)}" role="tabpanel" aria-labelledby="tab-{i}"{'' if first else ' inert aria-hidden="true"'}>
      <div class="prod__visual" data-name="{E(p['name'])}" style="{vis_style}">
        {hero_pic}
        {loop}
        <div class="prod__layers" aria-hidden="true">
          {chr(10).join('          ' + x for x in layers).strip()}
        </div>
        <ul class="prod__labels" aria-label="Ce are {E(p['name'])}">
          {chr(10).join('          ' + x for x in labels).strip()}
        </ul>
      </div>
      <div class="prod__info">
        <span class="badge">{E(p['badge'])}</span><span class="prod__prime">{E(P['meta']['prime_line'])}</span><span class="prod__idx" aria-hidden="true">{i+1:02d} / {N:02d}</span>
        <h2 class="prod__name">{E(p['name'])}</h2>
        <p class="prod__desc">{E(p['desc'])}</p>
        <p class="prod__price" data-price="{E(fm(p['offer']['price']))}"><span class="now">{E(fm(p['offer']['price']))} <small>lei</small></span> <s class="was" aria-label="preț întreg">{E(fm(p['offer']['was']))} lei</s></p>
        <button class="prod__explode" type="button" aria-pressed="false">{SVG_PLUS}Ce are?</button>
        <p class="sr">Ingrediente: {E(p['wolt_ingredients'])}.</p>
      </div>
    </article>''')

plats = []
for slug, name in [("glovo", "Glovo"), ("wolt", "Wolt"), ("bolt", "Bolt")]:
    link = P["meta"].get("links", {}).get(slug, "")
    plats.append(f'      <a class="plat" data-platform="{slug}" href="{E(link)}" data-href="{E(link)}" target="_blank" rel="noopener noreferrer" aria-label="Comandă pe {name}"><span>{name}</span>{SVG_ARROW}</a>')

promo = {p["name"]: p for p in products}
mtabs, mpanels = [], []
for k, c in enumerate(P["menu"]):
    on = k == 0
    mtabs.append(f'      <button class="mtab" role="tab" id="mtab-{k}" aria-selected="{"true" if on else "false"}" aria-controls="mlist-{k}" tabindex="{0 if on else -1}">{E(c["cat"])}</button>')
    rows = []
    for name, price in c["items"]:
        pr = promo.get(name) if c["cat"] in ("Burgeri", "Double", "Rolls") else None
        tag = '<span class="tag">-20% Glovo</span>' if pr else ""
        ing = f'\n          <p class="mrow__i">{E(pr["menu_line"])}</p>' if pr else ""
        rows.append(f'        <li class="mrow"><span class="mrow__n">{E(name)}{tag}</span><span class="mrow__p">{E(price)}<small>lei</small></span>{ing}</li>')
    mpanels.append(f'    <div class="mlist" role="tabpanel" id="mlist-{k}" aria-labelledby="mtab-{k}"{"" if on else " hidden"}>\n      <ul class="mlist__ul">\n' + "\n".join(rows) + "\n      </ul>\n    </div>")

# ------------------------------------------------------------------ 1) placeholdere A2
t = (UX / "v5.template.html").read_text(encoding="utf-8")
t = sub1(t, "%%HERO_TABS%%", "\n".join(tabs), 1, "tabs")
t = sub1(t, "%%HERO_PRODS%%", "\n".join(prods), 1, "prods")
t = sub1(t, "%%PLATS%%", "\n".join(plats), 2, "plats")
t = sub1(t, "%%MENU_TABS%%", "\n".join(mtabs), 1, "menu tabs")
t = sub1(t, "%%MENU_PANELS%%", "\n".join(mpanels), 1, "menu panels")
t = sub1(t, "%%CONCEPT%%", E(P["meta"]["concept_line"]), 1, "concept")
assert "%%" not in t

# SMASH intra in .hero__stage (primul copil): doar asa mix-blend-mode al video-ului il "vede" (stage e un stacking context: container-type:size)
WORD = '  <div class="hero__word" aria-hidden="true"><span>SMASH</span></div>\n'
t = sub1(t, WORD, "", 1, "word scos din hero")
t = sub1(t, '  <div class="hero__stage">\n', '  <div class="hero__stage">\n' + WORD, 1, "word in stage")

# ------------------------------------------------------------------ CSS A2: ce se scoate / se inlocuieste
# fonturile A2 (cai relative) ies; fonturile vin din type.css, base64
t = rx(t, r'@font-face\{font-family:"(?:Anton|Archivo)";src:url\("\.\./src/site/src/fonts/[^"]+"\)[^}]*\}\n', "", 3, label="@font-face A2")
# straturi + etichete A2 (clip-path pe exploded.png): inlocuite de straturile WebP decupate ale lui A3 (motion.css le aranjeaza)
t = rx(t, r"/\* straturi: starea de baza.*?\.prod__labels li span\{display:block\}\n", "/* straturi + etichete: motion.css (A3) */\n", 1, label="bloc straturi/etichete A2")
# imaginea hero e acum decupata, fara masca de margini; masca ramane doar pe video (dreptunghi)
t = sub1(t, ".prod__hero,.prod__loop{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;\n  -webkit-mask-image:linear-gradient(90deg,transparent,#000 12%,#000 88%,transparent),linear-gradient(180deg,transparent,#000 14%,#000 86%,transparent);\n  -webkit-mask-composite:source-in;mask-image:linear-gradient(90deg,transparent,#000 12%,#000 88%,transparent),linear-gradient(180deg,transparent,#000 14%,#000 86%,transparent);mask-composite:intersect}\n.prod__loop{opacity:0;pointer-events:none}\n.prod__loop.is-ready{opacity:1}\n",
         ".prod__hero{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}\n", 1, "reguli hero/loop A2")
# desktop: etichetele alternante A2 (A3 pozitioneaza etichetele din JS)
t = rx(t, r"  \.prod__labels li\{left:calc\(var\(--ex-left\).*?\n  \.prod__labels li:nth-child\(even\)::after\{[^\n]*\}\n", "", 1, label="etichete desktop A2")
# variabilele --ex-* nu mai sunt folosite
t = sub1(t, "  --ex-left:14px;          /* straturile „Ce are?\": stanga cutiei; eticheta vine in dreapta lor */\n", "", 1, label="--ex-left")
t = rx(t, r"\n  --ex-top:calc\(6px - var\(--vtop\)\);\n  --ex-hgt:calc\(100cqh - var\(--info-h\) - 12px\);\n  --ex-w:calc\(var\(--ex-hgt\) \* var\(--ex-ar,\.4\)\);", "", 1, label="--ex mobil")
t = rx(t, r"--ex-hgt:calc\(100cqh - 24px\);--ex-top:calc\(12px - var\(--vtop\)\);--ex-w:calc\(var\(--ex-hgt\) \* var\(--ex-ar,\.4\)\);--ex-left:calc\(\(var\(--vh\) \* \.8 - var\(--ex-w\)\) / 2\);\n    ", "", 1, label="--ex desktop")

# ------------------------------------------------------------------ JS A2: ce se corecteaza
js_a2_video_old = t[t.index("/* ---------- video bucla"):t.index("/* ---------- modale")]
js_a2_video_new = """/* ---------- video bucla: redarea o face motion.js (poarta dupa intro, retea, viewport); aici doar butonul de pauza ---------- */
var userPaused=false;
function syncVideo(){}
$$('.prod__loop',hero).forEach(function(v){
  var pb=$('.prod__pause',v.closest('.prod__visual'));
  v.addEventListener('playing',function(){ if(userPaused){v.pause();return} if(pb) pb.hidden=false });
  v.addEventListener('play',function(){ if(userPaused) v.pause() });
  v.addEventListener('error',function(){ if(pb) pb.hidden=true });
});
$$('.prod__pause',hero).forEach(function(b){b.addEventListener('click',function(){
  userPaused=!userPaused; $$('.prod__pause',hero).forEach(function(x){x.setAttribute('aria-pressed',userPaused?'true':'false');x.setAttribute('aria-label',userPaused?'Pornește animația':'Pune pe pauză animația')});
  var v=$('.prod__loop',prods[active]);
  if(v){ if(userPaused) v.pause(); else if(v.getAttribute('src')&&!prods[active].classList.contains('is-exploded')){var pr=v.play(); if(pr&&pr.catch) pr.catch(function(){})} }
})});

"""
t = sub1(t, js_a2_video_old, js_a2_video_new, 1, "video A2")
# A3.change() nu returneaza promise: A2 nu are voie sa scoata imediat is-leaving (A3 il scoate la sfarsitul tranzitiei)
t = sub1(t, "  if(r && typeof r.then==='function'){ try{r.then(finish,finish)}catch(e){finish()} setTimeout(finish,1600) } else finish();",
         "  if(r && typeof r.then==='function'){ try{r.then(finish,finish)}catch(e){finish()} setTimeout(finish,1600) } else if(!motion()) finish(); else setTimeout(finish,1700);", 1, "go() finish")

# swipe tactil: nu urmeaza niciun click, deci `swiped` ramanea true si inghitea primul tap de dupa swipe (ex. "Ce are?")
t = sub1(t, "if(Math.abs(dx)>=40&&Math.abs(dx)>Math.abs(dy)*1.3){swiped=true;if(dx<0) next(); else prev();}",
         "if(Math.abs(dx)>=40&&Math.abs(dx)>Math.abs(dy)*1.3){swiped=true;setTimeout(function(){swiped=false},350);if(dx<0) next(); else prev();}", 1, "swiped reset")

# ------------------------------------------------------------------ 2) CSS/JS inline
def read(p): return Path(p).read_text(encoding="utf-8")

type_css = read(MO / "type.css")
for n in ("anton-400", "archivo-400", "archivo-700"):
    type_css = sub1(type_css, f'url("../src/site/src/fonts/{n}.woff2")', f'url({b64(FONTS / (n + ".woff2"), "font/woff2")})', 1, f"font {n}")
type_css = sub1(type_css, "font-display:swap", "font-display:block", 3, "font-display")   # inline: se incarca instant, fara flash de fallback

motion_css = read(MO / "motion.css")
motion_js = read(MO / "motion.js")
# --- patch-uri minime in motion.js (documentate in HANDOFF): poarta de video, hidratare straturi, warm doar produsul activ
motion_js = sub1(motion_js, "function ready(p) {\n    if (p._ready) return p._ready;\n",
                 "function ready(p) {\n    if (p._ready) return p._ready;\n    if (window.SNAQHydrate) window.SNAQHydrate(p.el, 'layers');\n", 1, "ready()")
motion_js = sub1(motion_js, "  function videoPrepare(p) {\n    var v = p && p.loop; if (!v || !netOk()) return;\n    if (!v.getAttribute('src') && v.dataset.src) { v.preload = 'metadata'; v.src = v.dataset.src; v.load(); }",
                 "  var videoGate = false;   /* A4: videoul nu se cere inainte de sfarsitul intro-ului (prima zona fara video) */\n  function videoPrepare(p) {\n    var v = p && p.loop; if (!v || !videoGate || !netOk()) return;\n    if (!v.getAttribute('src') && v.dataset.src) { if (v.dataset.poster) v.poster = v.dataset.poster; v.preload = 'auto'; v.src = v.dataset.src; v.load(); }", 1, "videoPrepare")
motion_js = sub1(motion_js, "var v = p && p.loop; if (!v || !netOk() || !inView || p.open) return;",
                 "var v = p && p.loop; if (!v || !videoGate || !netOk() || !inView || p.open) return;", 1, "videoPlay")
motion_js = sub1(motion_js, "    tlIntro = null;\n    startIdle(); videoPlay(p); warm();",
                 "    tlIntro = null;\n    videoGate = true; document.dispatchEvent(new CustomEvent('snaq:intro-done'));\n    startIdle(); videoPlay(p); warm();", 1, "introDone")
motion_js = sub1(motion_js, "      doc.documentElement.classList.remove('mx-pre');\n      startIdle(); warm();",
                 "      doc.documentElement.classList.remove('mx-pre');\n      videoGate = true; document.dispatchEvent(new CustomEvent('snaq:intro-done'));\n      startIdle(); warm();", 1, "init fara intro")
motion_js = sub1(motion_js, "      var p = prods[active]; if (p) { ready(p); }\n      setTimeout(function () { prods.forEach(function (q) { if (q !== p) ready(q); }); }, 1500);",
                 "      var p = prods[active]; if (p) { ready(p); }   /* A4: restul produselor isi incarca straturile cand devin active */", 1, "warm()")
motion_js = sub1(motion_js, "    videoPrepare(byIndex(active));\n    setupScroll();", "    setupScroll();", 1, "videoPrepare init")
# schimbarea produsului: straturile noului produs se pregatesc dupa tranzitie
motion_js = sub1(motion_js, "    startIdle(); videoPlay(B);\n  }\n  function crossfade",
                 "    startIdle(); videoPlay(B);\n    if (netOk()) { var idl2 = window.requestIdleCallback || function (f) { return setTimeout(f, 300); }; idl2(function () { ready(B); }); }\n  }\n  function crossfade", 1, "endChange")

# ecrane scurte: stiva explodata se comprima vertical sa incapa intre tab-uri si info (mobil); altfel depasea (360x640)
motion_js = sub1(motion_js, "    var s = Math.min(1, (labelX - 0.06) / maxW);\n",
"""    var s = Math.min(1, (labelX - 0.06) / maxW);
    var fq = 1, cyShift = null;
    if (window.matchMedia && window.matchMedia('(max-width: 899px)').matches && p.info && stage) {
      var vr = p.visual.getBoundingClientRect(), sr = stage.getBoundingClientRect(), ir = p.info.getBoundingClientRect();
      var top0 = sr.top + 6, bot0 = ir.top - 8, av = bot0 - top0, cmin = 9, cmax = -9;
      data.forEach(function (d, k) { var e = els[k], ph = d.w * Wb * ((e.naturalHeight || 1) / (e.naturalWidth || 1)) * s / Hb; cmin = Math.min(cmin, d.cy - ph / 2); cmax = Math.max(cmax, d.cy + ph / 2); });
      var need = (cmax - cmin) * Hb;
      if (need > av && av > 120) { fq = Math.max(0.5, av / need); cyShift = { c0: (cmin + cmax) / 2, target: ((top0 + bot0) / 2 - vr.top) / Hb }; }
    }
    s = s * fq;
""", 1, "compute fit")
motion_js = sub1(motion_js, "      d.ty = (d.cy - ay) * Hb;", "      if (cyShift) d.cy = cyShift.target + (d.cy - cyShift.c0) * fq;\n      d.ty = (d.cy - ay) * Hb;", 1, "compute ty")

# etichete: de-coliziune verticala (etichetele pe 2 randuri se suprapuneau cu vecinele cand stratul e subtire / stiva comprimata)
motion_js = sub1(motion_js, "    return { data: data, A: A, s: s, Wb: Wb, Hb: Hb, labelX: labelX };",
                 "    return { data: data, A: A, s: s, Wb: Wb, Hb: Hb, labelX: labelX, bot: (bot0 !== undefined && vr) ? bot0 - vr.top : Hb * 0.97 };", 1, "compute return")
motion_js = sub1(motion_js, "      g.set(li, { yPercent: -50 });\n    });\n",
"""      g.set(li, { yPercent: -50 });
    });
    if (hasLayers && m > 1) {
      var gp = 4, its = p.labelEls.map(function (li, k) { var h = li.offsetHeight || 16, c = G.data[k].cy * G.Hb; return { li: li, h: h, top: c - h / 2 }; }), n2 = its.length, pass;
      for (pass = 0; pass < 2; pass++) {
        for (var a = 1; a < n2; a++) if (its[a].top < its[a - 1].top + its[a - 1].h + gp) its[a].top = its[a - 1].top + its[a - 1].h + gp;
        for (var b = n2 - 1; b >= 0; b--) { var lim = b === n2 - 1 ? G.bot : its[b + 1].top - gp; if (its[b].top + its[b].h > lim) its[b].top = lim - its[b].h; }
      }
      its.forEach(function (it) { it.li.style.top = ((it.top + it.h / 2) / G.Hb * 100) + '%'; });
    }
""", 1, "placeLabels decoliziune")

# closeIt(): closeNow() are garda (!open && !tl) si iesea fara sa curete dupa inchidere => transform/will-change ramaneau pe .prod__visual
# (stacking context permanent = mix-blend-mode al video-ului nu mai vedea SMASH) si, in reduced-motion, hero ramanea cu opacity 0
motion_js = sub1(motion_js, "closeNow(p); g.set(p.labelEls, { clearProps: 'x' }); startIdle(); videoPlay(p); return;",
                 "p.open = true; closeNow(p); g.set(p.labelEls, { clearProps: 'x' }); startIdle(); videoPlay(p); return;", 1, "closeIt RM")
motion_js = sub1(motion_js, "onComplete: function () { p.tl = null; closeNow(p); wc(p.layerEls, false); startIdle(); videoPlay(p); }",
                 "onComplete: function () { p.tl = null; p.open = true; closeNow(p); g.set(p.visual, { clearProps: 'willChange' }); wc(p.layerEls, false); startIdle(); videoPlay(p); }", 1, "closeIt complete")

# LCP: imaginea hero cadea de sus (-55% din viewport) => prima pictare avea doar o fractiune din arie (candidat LCP mic), apoi SMASH (text) si video-ul
# devineau candidate mai mari, tarziu (2.7 s / 4.6 s sub 4G+CPU 4x). Caderea porneste acum din interiorul viewport-ului: aria completa de la prima pictare.
motion_js = sub1(motion_js, "y: -Math.round(H * 0.55), opacity: 0", "y: -Math.round(H * 0.13), opacity: 0", 1, "intro drop")

gsap_js = read(MO / "node_modules/gsap/dist/gsap.min.js")
st_js = read(MO / "node_modules/gsap/dist/ScrollTrigger.min.js")
glue_js = read(B / "snippets/glue.js")
overrides_css = read(B / "snippets/overrides.css")
head_pre = "<script>document.documentElement.classList.add('mx-pre')</script>\n"

layers_map = {}
for slug in [p["slug"] for p in products]:
    lj = json.loads((MO / "layers" / slug / "layers.json").read_text())
    layers_map[slug] = {"layers": [{"index": l["index"], "exploded": l["exploded"], "assembled": l["assembled"]} for l in lj["layers"]]}

# preload pentru LCP: imaginea produsului activ (acelasi srcset/sizes ca <source>)
preload = (f'<link rel="preload" as="image" type="image/avif" imagesrcset="{hero_srcset(products[0]["slug"], "avif")}" '
           f'imagesizes="{HERO_SIZES}" fetchpriority="high">\n')

# <head>: mx-pre, preload, apoi type.css, motion.css, CSS A2, overrides (ordinea ceruta de A3 + overrides la final)
t = sub1(t, '<meta name="theme-color" content="#0D0B09">\n',
         '<meta name="theme-color" content="#0D0B09">\n' + head_pre + preload + f"<style>\n{type_css}\n{motion_css}\n</style>\n", 1, "head")
t = sub1(t, "</style>\n</head>", f"{overrides_css}\n</style>\n</head>", 1, "overrides")
# scripturi la sfarsitul body: GSAP, ScrollTrigger, motion.js, glue (hidratare), apoi scriptul de stare A2 (care cheama SNAQMotion.init)
a2_script_start = t.index("<script>\n(function(){\n'use strict';")
t = t[:a2_script_start] + (
    f"<script>{gsap_js}</script>\n<script>{st_js}</script>\n<script>\n{motion_js}\n</script>\n<script>\n{glue_js}\n</script>\n") + t[a2_script_start:]

# ------------------------------------------------------------------ 3) cai de imagini (regex), logo inline
logo_uri = b64(IMG / "logo-108.webp", "image/webp")
t = sub1(t, 'src="../src/site/src/img/logo.png"', f'src="{logo_uri}"', 2, "logo")
t = sub1(t, "../src/site/src/img/press.jpg", "img/press.webp", 2, "press")
t = sub1(t, "../src/site/src/img/assemble.jpg", "img/assemble.webp", 1, "assemble")
t = sub1(t, "../src/site/src/img/local.jpg", "img/local.webp", 1, "local")
assert "../src" not in t and "../assets" not in t, "cai relative ramase"
t = sub1(t, 'width="150" height="150" alt=""', 'width="108" height="108" alt=""', 1, "logo dim") if 'width="150" height="150" alt=""' in t else t

# favicon inline (fara 404 la /favicon.ico)
from PIL import Image as _I
import io as _io
_b = _io.BytesIO(); _I.open(IMG / "logo-108.webp").convert("RGBA").resize((48, 48)).save(_b, "PNG", optimize=True)
t = sub1(t, '<meta name="theme-color" content="#0D0B09">\n', '<meta name="theme-color" content="#0D0B09">\n<link rel="icon" type="image/png" href="data:image/png;base64,' + base64.b64encode(_b.getvalue()).decode() + '">\n', 1, "favicon")

# ------------------------------------------------------------------ 4) harta JSON a straturilor (la final)
t = sub1(t, "<script>" + gsap_js[:40], "<script>window.SNAQ_LAYERS=" + json.dumps(layers_map, separators=(",", ":")) + ";</script>\n<script>" + gsap_js[:40], 1, "SNAQ_LAYERS")

# ------------------------------------------------------------------ iesiri
out = B / "snaq-demo-v5.html"
out.write_text(t, encoding="utf-8")
if DIST.exists(): shutil.rmtree(DIST)
(DIST / "media").mkdir(parents=True)
shutil.copy(out, DIST / "index.html")
for s in [p["slug"] for p in products]:
    shutil.copytree(IMG / s, DIST / "img" / s, ignore=shutil.ignore_patterns("*.json"))
    shutil.copy(B / "media" / f"{s}.mp4", DIST / "media" / f"{s}.mp4")
for n in ("press", "assemble", "local"):
    shutil.copy(IMG / f"{n}.webp", DIST / "img" / f"{n}.webp")
size = lambda p: sum(f.stat().st_size for f in Path(p).rglob("*") if f.is_file())
print(f"html {len(t)/1024:.0f} KB | dist img {size(DIST/'img')/1024:.0f} KB | media {size(DIST/'media')/1024:.0f} KB")
