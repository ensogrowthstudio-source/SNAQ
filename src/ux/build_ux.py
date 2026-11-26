#!/usr/bin/env python3
"""Genereaza ux/v5.html din ux/v5.template.html + ux/products.json.
Date de produs, meniu, benzi (bands) pentru straturi: totul in products.json.
Daca fisierele din assets/gen/<slug>/ nu exista inca, pagina foloseste placeholder-ele
direct (fara 404 in consola). Dupa ce A1 le livreaza, rulezi din nou scriptul.
  python3 ux/build_ux.py            # autodetect
  python3 ux/build_ux.py --force-gen  # pune mereu caile gen/ (placeholder doar ca fallback onerror)
"""
import json, html, sys, pathlib

UX = pathlib.Path(__file__).resolve().parent
ROOT = UX.parent
FORCE = "--force-gen" in sys.argv
d = json.loads((UX / "products.json").read_text(encoding="utf-8"))
E = lambda s: html.escape(str(s), quote=True)

fb = d["meta"]["fallback"]
products = d["products"]
N = len(products)

def exists(rel):  # rel e relativ la ux/
    return (UX / rel).resolve().exists()

def fm(x):
    return f"{x:.2f}".replace(".", ",")

def eq_bands(n):
    step = 100 / n
    return [[round(i * step, 2), round((i + 1) * step, 2)] for i in range(n)]

SVG_PLUS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>'
SVG_PAUSE = '<svg class="i-pause" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg><svg class="i-play" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4l13 8-13 8z"/></svg>'
SVG_ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'

tabs, prods = [], []
for i, p in enumerate(products):
    slug = p["slug"]
    sel = "true" if i == 0 else "false"
    a, b = p["name_split"]
    tabs.append(
        f'    <button role="tab" class="hero__tab" id="tab-{i}" data-i="{i}" aria-selected="{sel}" aria-controls="panel-{i}" tabindex="{0 if i == 0 else -1}">'
        f'<span class="w" data-n="{i+1:02d}">{E(a)}</span> <span class="w">{E(b)}</span></button>')

    hero_src, exp_src = p["images"]["hero"], p["images"]["exploded"]
    hero_fb, exp_fb = fb["hero"][i], fb["exploded"]
    use_hero = hero_src if (FORCE or exists(hero_src)) else hero_fb
    use_exp = exp_src if (FORCE or exists(exp_src)) else exp_fb
    exp_is_fb = use_exp == exp_fb
    n_layers = len(p["layers"])
    real_bands = [l.get("band") for l in p["layers"]]
    if any(b is None for b in real_bands):
        real_bands = eq_bands(n_layers)
    fb_bands = fb.get("exploded_bands")
    if not fb_bands or len(fb_bands) != n_layers:
        fb_bands = eq_bands(n_layers)  # placeholder-ul are 7 straturi; altfel benzi egale
    cur = fb_bands if exp_is_fb else real_bands
    loop_rel = p["images"].get("loop")
    has_loop = bool(loop_rel) and (FORCE or exists(loop_rel))

    layers = []
    for k in range(n_layers):
        t, bt = cur[k]
        ft, fbt = fb_bands[k]
        layers.append(
            f'<img class="layer" data-layer="{k}" src="{E(use_exp)}" alt="" width="1600" height="2000" loading="lazy" decoding="async" '
            f'data-fallback="{E(exp_fb)}" data-fb-band="{ft},{fbt}" data-band="{t},{bt}" style="--t:{t}%;--b:{round(100-bt,2)}%">')
    labels = []
    for k, l in enumerate(p["layers"]):
        t, bt = cur[k]
        ft, fbt = fb_bands[k]
        labels.append(f'<li data-layer="{k}" data-fb-band="{ft},{fbt}" style="--t:{t}%;--h:{round(bt-t,2)}%"><span>{E(l["label"])}</span></li>')

    loop = ""
    if p["images"].get("loop"):
        ds = f' data-src="{E(loop_rel)}"' if has_loop else ""
        loop = (f'<video class="prod__loop" muted playsinline loop preload="none" aria-hidden="true" tabindex="-1"{ds}></video>\n'
                f'        <button class="prod__pause" type="button" aria-label="Pune pe pauză animația" aria-pressed="false" hidden>{SVG_PAUSE}</button>')
    first = i == 0
    fit = p.get("hero_fit", {"trim": .14, "bottom": .85})
    vis_style = f"--img-trim:{fit['trim']};--burger-bottom:{fit['bottom']};--ex-ar:{p.get('exploded_ar', .44)}"
    prods.append(f'''    <article class="prod{' is-active' if first else ''}" id="panel-{i}" data-i="{i}" data-slug="{E(slug)}" role="tabpanel" aria-labelledby="tab-{i}"{'' if first else ' inert aria-hidden="true"'}>
      <div class="prod__visual" data-name="{E(p['name'])}" style="{vis_style}">
        <img class="prod__hero" src="{E(use_hero)}" alt="{E(p['alt'])}" width="1600" height="2000" decoding="async"{' fetchpriority="high"' if first else ' loading="lazy"'} data-fallback="{E(hero_fb)}">
        {loop}
        <div class="prod__layers" aria-hidden="true">
          {chr(10).join('          ' + x for x in layers).strip()}
        </div>
        <ul class="prod__labels" aria-label="Ce are {E(p['name'])}">
          {chr(10).join('          ' + x for x in labels).strip()}
        </ul>
      </div>
      <div class="prod__info">
        <span class="badge">{E(p['badge'])}</span><span class="prod__prime">{E(d['meta']['prime_line'])}</span><span class="prod__idx" aria-hidden="true">{i+1:02d} / {N:02d}</span>
        <h2 class="prod__name">{E(p['name'])}</h2>
        <p class="prod__desc">{E(p['desc'])}</p>
        <p class="prod__price" data-price="{E(fm(p['offer']['price']))}"><span class="now">{E(fm(p['offer']['price']))} <small>lei</small></span> <s class="was" aria-label="preț întreg">{E(fm(p['offer']['was']))} lei</s></p>
        <button class="prod__explode" type="button" aria-pressed="false">{SVG_PLUS}Ce are?</button>
        <p class="sr">Ingrediente: {E(p['wolt_ingredients'])}.</p>
      </div>
    </article>''')

plats = []
for slug, name in [("glovo", "Glovo"), ("wolt", "Wolt"), ("bolt", "Bolt")]:
    link = d["meta"].get("links", {}).get(slug, "")
    plats.append(f'      <a class="plat" data-platform="{slug}" href="{E(link)}" data-href="{E(link)}" target="_blank" rel="noopener noreferrer" aria-label="Comandă pe {name}"><span>{name}</span>{SVG_ARROW}</a>')

# meniu
promo = {p["name"]: p for p in products}
mtabs, mpanels = [], []
for k, c in enumerate(d["menu"]):
    on = k == 0
    mtabs.append(f'      <button class="mtab" role="tab" id="mtab-{k}" aria-selected="{"true" if on else "false"}" aria-controls="mlist-{k}" tabindex="{0 if on else -1}">{E(c["cat"])}</button>')
    rows = []
    for name, price in c["items"]:
        pr = promo.get(name) if c["cat"] in ("Burgeri", "Double", "Rolls") else None
        tag = '<span class="tag">-20% Glovo</span>' if pr else ""
        ing = f'\n          <p class="mrow__i">{E(pr["menu_line"])}</p>' if pr else ""
        rows.append(f'        <li class="mrow"><span class="mrow__n">{E(name)}{tag}</span><span class="mrow__p">{E(price)}<small>lei</small></span>{ing}</li>')
    mpanels.append(f'    <div class="mlist" role="tabpanel" id="mlist-{k}" aria-labelledby="mtab-{k}"{"" if on else " hidden"}>\n      <ul class="mlist__ul">\n' + "\n".join(rows) + "\n      </ul>\n    </div>")

t = (UX / "v5.template.html").read_text(encoding="utf-8")
for k, v in {
    "%%HERO_TABS%%": "\n".join(tabs),
    "%%HERO_PRODS%%": "\n".join(prods),
    "%%PLATS%%": "\n".join(plats),
    "%%MENU_TABS%%": "\n".join(mtabs),
    "%%MENU_PANELS%%": "\n".join(mpanels),
    "%%CONCEPT%%": E(d["meta"]["concept_line"]),
}.items():
    t = t.replace(k, v)
assert "%%" not in t
(UX / "v5.html").write_text(t, encoding="utf-8")
print("v5.html", len(t), "bytes", "(force-gen)" if FORCE else "")
