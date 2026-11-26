#!/usr/bin/env python3
"""Capturi + teste pentru ux/v5.html. PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 ux/tools/shots.py [pagina.html]"""
import os, sys, json, pathlib
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
from playwright.sync_api import sync_playwright

UX = pathlib.Path(__file__).resolve().parent.parent
page_name = sys.argv[1] if len(sys.argv) > 1 else "v5.html"
URL = (UX / page_name).as_uri()
SHOTS = UX / "shots"; SHOTS.mkdir(exist_ok=True)
VPS = [("360x640", 360, 640, True), ("390x844", 390, 844, True), ("1440x900", 1440, 900, False)]
res = {"errors": [], "checks": {}}

def log(k, v):
    res["checks"][k] = v
    print(("OK   " if v is True else "FAIL " if v is False else "     ") + k, "" if v is True else v)

with sync_playwright() as pw:
    br = pw.chromium.launch()
    for name, w, h, mobile in VPS:
        ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2 if mobile else 1, has_touch=mobile, is_mobile=mobile)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e, n=name: errs.append(f"[{n}] pageerror: {e}"))
        pg.on("console", lambda m, n=name: errs.append(f"[{n}] console.{m.type}: {m.text}") if m.type in ("error",) else None)
        pg.goto(URL); pg.wait_for_load_state("load"); pg.wait_for_timeout(500)
        pg.screenshot(path=str(SHOTS / f"{name}_01_hero.png"))
        # tab 2
        pg.click('.hero__tab[data-i="1"]'); pg.wait_for_timeout(200)
        pg.screenshot(path=str(SHOTS / f"{name}_02_tab2.png"))
        pg.click('.hero__tab[data-i="2"]'); pg.wait_for_timeout(200)
        pg.screenshot(path=str(SHOTS / f"{name}_03_tab3.png"))
        pg.click('.hero__tab[data-i="0"]'); pg.wait_for_timeout(100)
        # explode
        pg.click('.prod.is-active .prod__explode'); pg.wait_for_timeout(300)
        pg.screenshot(path=str(SHOTS / f"{name}_04_explode.png"))
        log(f"{name} explode aria-pressed", pg.get_attribute('.prod.is-active .prod__explode', 'aria-pressed') == "true")
        pg.click('.prod.is-active .prod__explode'); pg.wait_for_timeout(100)
        # sheet
        pg.click('.hero__cta'); pg.wait_for_timeout(400)
        pg.screenshot(path=str(SHOTS / f"{name}_05_sheet.png"))
        log(f"{name} sheet open", pg.is_visible('#order') and pg.evaluate("document.activeElement.classList.contains('plat')"))
        pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
        log(f"{name} sheet closed by Esc", not pg.is_visible('#order'))
        log(f"{name} focus returned to CTA", pg.evaluate("document.activeElement.classList.contains('hero__cta')"))
        log(f"{name} scroll unlocked", pg.evaluate("!document.documentElement.classList.contains('is-locked')"))
        # overflow orizontal
        ov = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        log(f"{name} no horizontal overflow", ov <= 0)
        # full page
        pg.screenshot(path=str(SHOTS / f"{name}_06_full.png"), full_page=True)
        res["errors"] += errs
        ctx.close()
    br.close()
print("ERRORS:", len(res["errors"]))
for e in res["errors"]: print("  ", e)
(SHOTS / "results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
