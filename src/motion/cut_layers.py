#!/usr/bin/env python3
"""
cut_layers.py — taie un `exploded.png` (straturi separate vertical, goluri de fundal)
in PNG/WebP-uri transparente, cate unul per strat.

Utilizare:
    python3 motion/cut_layers.py <slug>              # assets/gen/<slug>/exploded.png -> motion/layers/<slug>/
    python3 motion/cut_layers.py _placeholder        # assets/placeholder/g1_v1.png -> motion/layers/_placeholder/
    python3 motion/cut_layers.py --src x.png --out dir

Pasi: 1) detectie benzi pe randuri (diferenta fata de culoarea fundalului local, cu toleranta)
      2) decupare banda (+ padding in gol)  3) scoatere fundal: rembg (u2net) daca modelul se
      poate descarca, altfel chroma-key moale pe culoarea fundalului  4) defringe (estimare
      culoare prim-plan, nu semitransparenta murdara)  5) crop la bbox, resize <=900px, WebP q82
      6) layers.json + contact sheets (_sheet_dark.png / _sheet_light.png) pentru verificare.
"""
import argparse, json, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
MOTION = Path(__file__).resolve().parent

MAX_W = 900
WEBP_Q = 82
CHOKE = 2   # px de eroziune a alpha-ului


# ---------------------------------------------------------------- detectie benzi
def bg_per_row(arr, edge=48):
    """culoarea fundalului pe fiecare rand: mediana pixelilor din marginea stanga+dreapta."""
    h, w, _ = arr.shape
    left = arr[:, :edge, :].reshape(h, -1, 3)
    right = arr[:, -edge:, :].reshape(h, -1, 3)
    both = np.concatenate([left, right], axis=1)
    return np.median(both, axis=1)  # (h,3)


def content_mask(arr, thr=34):
    bg = bg_per_row(arr)
    diff = np.abs(arr.astype(np.int16) - bg[:, None, :].astype(np.int16)).max(axis=2)
    return diff > thr, bg


def find_bands(arr, thr=34, min_px_frac=0.006, min_gap=18, min_h=40, split_frac=0.16, thr_hard=70, hard_frac=0.03):
    mask, bg = content_mask(arr, thr)
    h, w = mask.shape
    # un rand e "continut" daca are destui pixeli diferiti (aburul slab nu trece)
    rows = mask.sum(axis=1) >= max(6, int(w * min_px_frac))
    bands, start = [], None
    for y in range(h):
        if rows[y] and start is None:
            start = y
        elif not rows[y] and start is not None:
            bands.append([start, y - 1]); start = None
    if start is not None:
        bands.append([start, h - 1])
    # uneste benzile separate de goluri mai mici de min_gap
    merged = []
    for b in bands:
        if merged and b[0] - merged[-1][1] < min_gap:
            merged[-1][1] = b[1]
        else:
            merged.append(b)
    merged = [b for b in merged if b[1] - b[0] + 1 >= min_h]
    # a doua trecere: benzi foarte inalte = probabil straturi lipite (zvonuri de abur, picaturi de branza).
    # Re-taie cu prag mare de contrast, ignorand abur/umbra slaba si randuri aproape goale.
    split_h = int(h * split_frac)
    hard, _ = content_mask(arr, thr_hard)
    out = []
    for y0, y1 in merged:
        if y1 - y0 + 1 <= split_h:
            out.append([y0, y1]); continue
        cnt = hard[y0:y1 + 1].sum(axis=1)
        low = cnt < max(8, int(w * hard_frac))
        parts, st = [], None
        for k in range(len(cnt)):
            if not low[k] and st is None: st = k
            elif low[k] and st is not None: parts.append([y0 + st, y0 + k - 1]); st = None
        if st is not None: parts.append([y0 + st, y1])
        mg = []
        for b in parts:
            if mg and b[0] - mg[-1][1] < 6: mg[-1][1] = b[1]
            else: mg.append(b)
        mg = [b for b in mg if b[1] - b[0] + 1 >= min_h]
        out.extend(mg if len(mg) > 1 else [[y0, y1]])
    return out, bg


# ---------------------------------------------------------------- scoatere fundal
_rembg_session = None
_rembg_failed = False


def rembg_alpha(img_rgb):
    global _rembg_session, _rembg_failed
    if _rembg_failed:
        return None
    try:
        from rembg import remove, new_session
        if _rembg_session is None:
            _rembg_session = new_session("u2net")
        out = remove(img_rgb, session=_rembg_session, only_mask=True)
        return np.asarray(out, dtype=np.float32) / 255.0
    except Exception as e:  # model indisponibil / retea
        print(f"  [rembg indisponibil: {type(e).__name__}] -> chroma-key", file=sys.stderr)
        _rembg_failed = True
        return None


def chroma_alpha(arr, bg_rows, lo=14, hi=46):
    """alpha moale din distanta fata de fundalul local; lo..hi rampa."""
    diff = np.abs(arr.astype(np.float32) - bg_rows[:, None, :].astype(np.float32)).max(axis=2)
    a = np.clip((diff - lo) / (hi - lo), 0, 1)
    return a


def refine_alpha(a, arr, bg_rows):
    """combina rembg cu chroma: pastreaza forma rembg, dar taie halourile unde pixelul e egal cu fundalul,
    umple gaurile mici; apoi margine moale (blur mic + curba)."""
    chroma = chroma_alpha(arr, bg_rows, lo=10, hi=30)
    # umple: unde chroma spune clar 'continut' si rembg e nesigur -> ia max din zona dilatata
    m = Image.fromarray((a * 255).astype(np.uint8))
    m_d = np.asarray(m.filter(ImageFilter.MaxFilter(9)), dtype=np.float32) / 255.0
    # in zona dilatata, alpha = max(rembg, chroma) limitat ; in rest rembg
    out = np.where(m_d > 0.5, np.maximum(a, chroma * (m_d > 0.5)), a)
    # elimina halou: unde pixelul e practic fundal si rembg e mic
    out = np.where((chroma < 0.04) & (a < 0.6), 0, out)
    # choke: strange marginea ~2px ca sa dispara rama intunecata (fundal care a scapat in alpha)
    im0 = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    for _ in range(CHOKE):
        im0 = im0.filter(ImageFilter.MinFilter(3))
    # margine moale
    im = im0.filter(ImageFilter.GaussianBlur(1.0))
    out = np.asarray(im, dtype=np.float32) / 255.0
    # curba usor contrastata ca marginea sa nu fie ceata
    out = np.clip((out - 0.06) / 0.88, 0, 1)
    out = out * out * (3 - 2 * out)
    return out


def keep_main_blob(a, min_frac=0.02):
    """pastreaza componentele conexe mari (scoate scantei/praf izolat); foloseste scipy daca exista."""
    try:
        from scipy import ndimage
    except Exception:
        return a
    lab, n = ndimage.label(a > 0.15)
    if n <= 1:
        return a
    sizes = ndimage.sum(np.ones_like(a), lab, index=range(1, n + 1))
    keep = np.zeros(n + 1, dtype=bool)
    big = sizes.max()
    for i, s in enumerate(sizes, start=1):
        if s >= big * min_frac:
            keep[i] = True
    return a * keep[lab]


def defringe(arr, alpha, bg_rows):
    """estimeaza culoarea prim-planului ca marginile semitransparente sa nu poarte nuanta fundalului."""
    try:
        from pymatting import estimate_foreground_ml
        img = arr.astype(np.float64) / 255.0
        fg = estimate_foreground_ml(img, alpha.astype(np.float64))
        return np.clip(fg * 255, 0, 255).astype(np.uint8)
    except Exception:
        a = np.clip(alpha, 0.05, 1)[..., None]
        bgc = bg_rows[:, None, :].astype(np.float32)
        fg = (arr.astype(np.float32) - (1 - a) * bgc) / a
        return np.clip(fg, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- pipeline
def cut(src: Path, out: Path, thr=34, pad_max=60, verbose=True):
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("layer_*.webp"):
        f.unlink()
    img = Image.open(src).convert("RGB")
    arr = np.asarray(img)
    H, W, _ = arr.shape
    bands, bg = find_bands(arr, thr=thr)
    if verbose:
        print(f"{src.name}: {W}x{H}, {len(bands)} benzi: {bands}")
    if not bands:
        raise SystemExit("nu am gasit benzi; scade pragul (thr)")

    layers = []
    for i, (y0, y1) in enumerate(bands):
        prev_end = bands[i - 1][1] if i > 0 else -10**9
        next_start = bands[i + 1][0] if i + 1 < len(bands) else 10**9
        top = max(0, y0 - min(pad_max, (y0 - prev_end) // 2))
        bot = min(H - 1, y1 + min(pad_max, (next_start - y1) // 2))
        crop = arr[top:bot + 1]
        bgc = bg[top:bot + 1]
        a = rembg_alpha(Image.fromarray(crop))
        if a is None:
            a = chroma_alpha(crop, bgc)
            a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float32) / 255.0
        else:
            a = refine_alpha(a, crop, bgc)
        a = keep_main_blob(a)
        fg = defringe(crop, a, bgc)
        rgba = np.dstack([fg, (a * 255).astype(np.uint8)])
        im = Image.fromarray(rgba, "RGBA")
        bbox = Image.fromarray((a * 255).astype(np.uint8)).point(lambda v: 255 if v > 10 else 0).getbbox()
        if not bbox:
            print(f"  strat {i}: gol dupa decupare, sar", file=sys.stderr)
            continue
        x0, ty0, x1, ty1 = bbox
        im = im.crop(bbox)
        gx0, gy0 = x0, top + ty0        # pozitia in imaginea sursa
        gx1, gy1 = x1, top + ty1
        w0, h0 = im.size
        scale = min(1.0, MAX_W / w0)
        if scale < 1:
            im = im.resize((round(w0 * scale), round(h0 * scale)), Image.LANCZOS)
        name = f"layer_{len(layers):02d}.webp"
        im.save(out / name, "WEBP", quality=WEBP_Q, method=6, alpha_quality=90)
        layers.append(dict(
            index=len(layers), file=name,
            src_box=[gx0, gy0, gx1, gy1],
            w_px=im.size[0], h_px=im.size[1],
            bytes=(out / name).stat().st_size,
        ))
        if verbose:
            print(f"  {name}: src y {gy0}-{gy1}, {im.size[0]}x{im.size[1]}, {layers[-1]['bytes']//1024} KB")

    # ---- pozitii in fractiuni din imaginea sursa (exploded) si estimare compozitie asamblata
    for L in layers:
        x0, y0, x1, y1 = L["src_box"]
        L["exploded"] = dict(cx=round((x0 + x1) / 2 / W, 4), cy=round((y0 + y1) / 2 / H, 4),
                             w=round((x1 - x0) / W, 4), h=round((y1 - y0) / H, 4))
    # asamblat: straturi suprapuse strans (suprapunere ~38% din inaltime), centrate vertical la ~0.55 H
    overlap = 0.38
    hs = [L["exploded"]["h"] for L in layers]
    total = sum(hs) - overlap * sum(hs[1:]) * 0.5 - overlap * sum(hs[:-1]) * 0.5
    total = max(total, 0.1)
    y = 0.55 - total / 2
    for k, L in enumerate(layers):
        h = L["exploded"]["h"]
        L["assembled"] = dict(cx=0.5, cy=round(y + h / 2, 4), w=L["exploded"]["w"], h=h)
        y += h - overlap * h * 0.5 - (overlap * hs[k + 1] * 0.5 if k + 1 < len(hs) else 0)
    meta = dict(source=str(src.relative_to(ROOT)) if src.is_relative_to(ROOT) else str(src),
                src_size=[W, H], aspect=round(W / H, 4), method="rembg-u2net" if not _rembg_failed else "chroma-key",
                order="0 = sus (chifla), crescator in jos; coordonate = fractiuni din imaginea sursa (centru)",
                layers=layers)
    (out / "layers.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    contact_sheets(out, layers)
    if verbose:
        tot = sum(L["bytes"] for L in layers)
        print(f"-> {out} ({len(layers)} straturi, {tot//1024} KB total, metoda {meta['method']})")
    return meta


def cut_hero(src: Path, dst: Path, max_w=1000):
    """Produsul asamblat decupat (fundal transparent) ca SMASH-ul din spate sa se vada in jurul lui.
    Pastreaza cadrul intreg (nu taie la bbox) ca sa se potriveasca 1:1 cu .prod__hero / .prod__visual."""
    img = Image.open(src).convert("RGB")
    arr = np.asarray(img)
    bg = bg_per_row(arr)
    a = rembg_alpha(img)
    if a is None:
        a = chroma_alpha(arr, bg, lo=18, hi=50)
    else:
        a = refine_alpha(a, arr, bg)
    a = keep_main_blob(a, 0.05)
    fg = defringe(arr, a, bg)
    im = Image.fromarray(np.dstack([fg, (a * 255).astype(np.uint8)]), "RGBA")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "WEBP", quality=WEBP_Q, method=6, alpha_quality=90)
    print(f"  hero decupat: {dst.name} {im.size[0]}x{im.size[1]} {dst.stat().st_size//1024} KB")


def contact_sheets(out: Path, layers):
    ims = [Image.open(out / L["file"]).convert("RGBA") for L in layers]
    th = 260
    thumbs = []
    for im in ims:
        r = th / im.height
        thumbs.append(im.resize((max(1, round(im.width * r)), th), Image.LANCZOS))
    cols = 3
    cw = max(t.width for t in thumbs) + 24
    rows = (len(thumbs) + cols - 1) // cols
    for tag, col in (("dark", (13, 11, 9, 255)), ("light", (238, 238, 232, 255))):
        sheet = Image.new("RGBA", (cw * cols, (th + 24) * rows), col)
        for k, t in enumerate(thumbs):
            x = (k % cols) * cw + (cw - t.width) // 2
            y = (k // cols) * (th + 24) + 12
            sheet.alpha_composite(t, (x, y))
        sheet.convert("RGB").save(out / f"_sheet_{tag}.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--src")
    ap.add_argument("--out")
    ap.add_argument("--thr", type=int, default=34)
    ap.add_argument("--no-hero", action="store_true", help="nu decupa si hero.png")
    a = ap.parse_args()
    if a.src:
        src = Path(a.src); out = Path(a.out or MOTION / "layers" / src.stem)
    elif a.slug == "_placeholder":
        src = ROOT / "assets/placeholder/g1_v1.png"; out = MOTION / "layers/_placeholder"
    elif a.slug:
        src = ROOT / "assets/gen" / a.slug / "exploded.png"; out = MOTION / "layers" / a.slug
    else:
        ap.error("da un slug")
    if not src.exists():
        raise SystemExit(f"nu exista {src}")
    cut(src, out, thr=a.thr)
    if not a.no_hero:
        if a.slug == "_placeholder":
            for tag, f in (("h1", "h1_classic.png"), ("h3", "h3_double.png")):
                cut_hero(ROOT / "assets/placeholder" / f, out / f"hero_cut_{tag}.webp")
        else:
            h = src.parent / "hero.png"
            if h.exists():
                cut_hero(h, out / "hero_cut.webp")


if __name__ == "__main__":
    main()
