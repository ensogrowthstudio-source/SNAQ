import os, pathlib
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH","/opt/pw-browsers")
from playwright.sync_api import sync_playwright
UX=pathlib.Path(__file__).resolve().parent.parent
URL=(UX/"v5.html").as_uri()
def ok(k,v): print(("OK   " if v else "FAIL ")+k)
with sync_playwright() as pw:
    br=pw.chromium.launch()
    ctx=br.new_context(viewport={"width":390,"height":844},has_touch=True,is_mobile=True)
    pg=ctx.new_page(); errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("console",lambda m:errs.append(m.text) if m.type=="error" else None)
    ev=[]; pg.goto(URL); pg.wait_for_timeout(300)
    pg.evaluate("window.__ev=[];['hero:change','hero:explode'].forEach(n=>document.addEventListener(n,e=>__ev.push([n,e.detail])))")
    act=lambda: pg.evaluate("SNAQHero.active")
    # swipe via CDP touch
    cdp=ctx.new_cdp_session(pg)
    def swipe(x1,x2,y=400,dy=0):
        cdp.send("Input.dispatchTouchEvent",{"type":"touchStart","touchPoints":[{"x":x1,"y":y}]})
        for i in range(1,9):
            cdp.send("Input.dispatchTouchEvent",{"type":"touchMove","touchPoints":[{"x":x1+(x2-x1)*i/8,"y":y+dy*i/8}]})
        cdp.send("Input.dispatchTouchEvent",{"type":"touchEnd","touchPoints":[]}); pg.wait_for_timeout(200)
    swipe(300,120); ok("swipe left -> next",act()==1)
    swipe(100,300); ok("swipe right -> prev",act()==0)
    swipe(200,215); ok("small drag (<40px) ignored",act()==0)
    ok("events emitted",len(pg.evaluate("__ev"))>=2)
    pg.focus('.hero__tab[aria-selected="true"]'); pg.keyboard.press("ArrowRight"); ok("ArrowRight on tab",act()==1 and pg.evaluate("document.activeElement.dataset.i")=="1")
    pg.keyboard.press("ArrowLeft"); pg.keyboard.press("ArrowLeft"); ok("ArrowLeft wraps to last",act()==2)
    ok("aria-selected sync",pg.evaluate("[...document.querySelectorAll('.hero__tab')].map(t=>t.getAttribute('aria-selected')).join()")=="false,false,true")
    ok("inactive panels inert",pg.evaluate("document.querySelectorAll('.prod[inert]').length")==2)
    # focus trap
    pg.click('.hero__cta'); pg.wait_for_timeout(350)
    for _ in range(8): pg.keyboard.press("Tab")
    ok("focus stays in sheet",pg.evaluate("document.getElementById('order').contains(document.activeElement)"))
    ok("background inert",pg.evaluate("document.getElementById('top').hasAttribute('inert')"))
    ok("glovo has href",pg.evaluate("document.querySelector('#order .plat').getAttribute('href').includes('glovoapp')"))
    pg.mouse.click(200,60); pg.wait_for_timeout(350); ok("backdrop closes",not pg.is_visible('#order'))
    # burger menu
    pg.click('#burger'); pg.wait_for_timeout(350); ok("menu opens",pg.is_visible('#menu-panel') and pg.get_attribute('#burger','aria-expanded')=="true")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(350); ok("menu Esc + focus back",pg.evaluate("document.activeElement.id")=="burger")
    # menu tabs
    pg.click('#mtab-2'); ok("menu tab switch",pg.is_visible('#mlist-2') and not pg.is_visible('#mlist-0'))
    # dock
    pg.evaluate("window.scrollTo(0,1400)"); pg.wait_for_timeout(500); ok("dock shows after hero",pg.evaluate("document.getElementById('dock').classList.contains('is-shown')"))
    # tap targets
    small=pg.evaluate("""[...document.querySelectorAll('button,a[href],.plat')].filter(e=>e.offsetParent&&!e.closest('[hidden]')).map(e=>[e,e.getBoundingClientRect()]).filter(([e,r])=>r.width>0&&(r.height<44||r.width<44)&&!e.classList.contains('skip')).map(([e,r])=>e.className+' '+Math.round(r.width)+'x'+Math.round(r.height))""")
    ok("targets >=44px "+str(small),not small)
    ctx.close()
    # reduced motion + fallback + 360 small
    ctx=br.new_context(viewport={"width":360,"height":640},reduced_motion="reduce")
    pg=ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(300)
    pg.click('.prod.is-active .prod__explode'); ok("reduced-motion explode works",pg.evaluate("document.querySelector('.prod.is-active').classList.contains('is-exploded')"))
    ok("reduced-motion: video not playing",pg.evaluate("[...document.querySelectorAll('.prod__loop')].every(v=>!v.getAttribute('src'))"))
    ctx.close()
    # broken image: force-gen build to missing path
    html=(UX/"v5.html").read_text().replace("../assets/gen/double-bacon/hero.png","../assets/gen/NOPE/hero.png")
    t=UX/"_t.html"; t.write_text(html)
    ctx=br.new_context(viewport={"width":360,"height":640}); pg=ctx.new_page(); pg.goto(t.as_uri()); pg.wait_for_timeout(500)
    ok("broken hero falls back",pg.evaluate("document.querySelector('.prod__hero').src.includes('placeholder')"))
    html=html.replace("../assets/placeholder/h1_classic.png","../assets/NOPE.png"); t.write_text(html)
    pg.goto(t.as_uri()); pg.wait_for_timeout(500); ok("both broken -> is-broken",pg.evaluate("document.querySelector('.prod__visual').classList.contains('is-broken')"))
    pg.screenshot(path=str(UX/"shots/360x640_07_broken.png")); t.unlink(); ctx.close()
    br.close()
print("errors:",[e for e in errs])
