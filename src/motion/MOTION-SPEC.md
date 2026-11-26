# SNAQ v5 · MOTION-SPEC (A3)

Concept: „Strivit pe plită". Burgerul cade, aterizează cu squash, SMASH-ul din spate e presat ca de o presă și revine. Totul animă doar `transform` și `opacity`. Banc de test: `motion/demo.html` (servit pe http, nu file://).

## 1. Tokeni

| Token | Valoare | Folosit la |
|---|---|---|
| rapid | 0.18 s, `power2.out` | stingere info la schimbare, etichete la închidere |
| mediu | 0.40 s, `power3.out` | tab-uri, info, etichete, reveal |
| lent | 0.65 s, `expo.out` | parallax SMASH, zborul straturilor (0.75 s), roll-up text (0.45-0.5 s) |
| stagger | 0.06 s | tab-uri, info, straturi, etichete, copii la reveal |
| squash aterizare | `scaleY .93 / scaleX 1.045`, 0.07 s `power2.out`, revenire 0.36 s `back.out(3.2)` | intro |
| presa SMASH | `scaleY 1.6 -> 1`, 0.46 s `back.out(2.4)`, `transform-origin: 50% 100%` | intro |
| thump SMASH | `scaleY 1 -> .92 -> 1`, 0.07 s `power2.out` + 0.4 s `back.out(2.6)` | change |
| bounce produs | 0.49 s `back.out(1.5)` | change |
| idle | `y` -4 <-> +4 px, 2 s `sine.inOut` yoyo = 4 s/ciclu | produs activ |
| slam închidere | `scaleY .94 / scaleX 1.03` 0.08 s, revenire 0.42 s `back.out(3.2)`, origin `50% 92%` | explode închis |

`will-change` se pune doar cât durează tween-ul (helper `wc()`), apoi se șterge. Fără `filter`, fără `box-shadow` animat.

## 2. Ce citește motion.js din DOM

Contractul din BRIEF.md, plus:

| Element | Citit / modificat |
|---|---|
| `#hero[data-active]` | index inițial; `.prod.is-active` are prioritate |
| `.hero__word` (părinte) | scroll: `y` + `opacity` (scrub) |
| `.hero__word span` | intro (presă), thump + parallax la change |
| `.hero__tab` | doar intro (stagger) |
| `.hero__stage` | scroll: `scale` + `y` (scrub) |
| `.prod[data-i][data-slug]` | clasele `is-leaving` / `is-entering` (le pune A3, forțează `display:block !important` cât durează tranziția) |
| `.prod__visual` | intro (cădere), change (ieșire/intrare), slam la explode |
| `.prod__hero`, `.prod__loop` | idle (`y`), crossfade la explode (`opacity`) |
| `.prod__layers` | `data-hero-w` (lățimea burgerului asamblat, implicit .78), `data-hero-cy` (.58), `data-label-x` (.62), `data-json` (URL layers.json) |
| `.layer[data-layer]` | `data-cx`, `data-ey`, `data-w`, `data-h` (opțional, vezi §5) |
| `.prod__labels li[data-layer]` | JS inserează `<i class="mx-line">` și le poziționează |
| `.prod__info > *` | fiecare copil intră cu stagger; `.prod__name` și `.prod__price` primesc mască roll-up (JS înfășoară conținutul în `.mx-mask > .mx-roll`) |
| `.prod__loop[data-src]` | video lazy (vezi §6) |
| `.hero__cta` | intro |
| `[data-reveal]`, `main > section:not(#hero)` | reveal o singură dată; `data-reveal="stagger"` = copiii, 60 ms |

Nu atinge: `is-active`, `aria-*`, `hidden`, tab-index, swipe, tastatură, order sheet. Asta e A2.

## 3. Coregrafie (timp în secunde de la start)

### Intro (~1.25 s, o singură dată, nu blochează nimic)
```
0.00  SMASH   opacity 0->1 (0.14) | scaleY 1.6->1 back.out(2.4) (0.46)        origin jos
0.12  burger  opacity 0->1 (0.10) | y -55% viewport -> 0 power3.in (0.36)
0.42  tab-uri y 14->0, opacity, stagger 0.06 (0.4 power3.out)
0.48  burger  squash aterizare (0.07)  ->  0.55 revenire back.out(3.2) (0.36)
0.48  SMASH   thump scaleY .955 (0.07) -> 1 back.out(3) (0.32)
0.54  info    badge, nume (roll-up 0.5 expo.out), desc, pret (roll-up), buton, stagger 0.06
0.54+n·0.06  CTA
```
Dacă userul schimbă produsul în timpul intro-ului, intro-ul se termină instant (`progress(1)`) și change pornește curat.
Se sare peste intro dacă `scrollY >= 200` la init (pagină restaurată) sau reduced-motion.

### Change (`change(from, to, dir)`, ~0.65 s principal, ~0.78 s cu coada info)
`dir = +1` = produs următor (conținutul pleacă spre stânga), `-1` = anterior.
```
0.00  vechi   x 0 -> -dir·0.55·W, rotation -dir·9°, scale .9 (0.36 power2.in) | opacity ->0 (0.24 de la 0.06)
0.00  vechi info  opacity ->0, y -10 (0.18 power2.out)
0.08  SMASH   x dir·34 -> 0 (0.65 expo.out)  (parallax)
0.16  nou     x dir·0.6·W -> 0, rotation dir·8° -> 0, scale .92 -> 1 (0.49 back.out(1.5)) | opacity 0->1 (0.2)
0.30  SMASH   thump scaleY .92 -> 1
0.14+i·0.06  info nou: badge/desc/buton fade-up 14px (0.4); nume + preț roll-up (yPercent 108 -> 0, 0.45 expo.out)
```
Interrupt: la apelul următor, `settle()` duce tween-ul curent la final (`progress(1)` => `onComplete` curăță) și apoi pornește noul change. Verificat: 6 click-uri la 90 ms + explode + change => toate `style` goale, `is-leaving/entering` scoase, straturi `hidden`.
Dacă `from` are explode deschis, se închide instant (fără animație) înainte.

### Explode deschis (`explode(i, true)`)
```
0.00  așteaptă decodarea straturilor (max 1.2 s; de obicei preîncărcate în idle după intro)
0.00  .prod__layers autoAlpha 0->1 (0.12) | imaginea asamblată opacity 1->0 (0.16, de la 0.06)
0.14+k·0.06  strat k: x/y/scale din poziția asamblată în cea explodată, 0.75 s expo.out   (k=0 e chifla de sus)
0.38+k·0.06  eticheta k: opacity 0->1, x -8->0 (0.4 power3.out) + firul galben scaleX 0->1 (0.4)
```
Geometrie: straturile își păstrează y din `exploded.png`; stiva se mută în stânga (`Xc ≈ 0.30` din lățimea cutiei) și se scalează cel mult la 1 ca să încapă; coloana de etichete începe la `data-label-x` (0.62), fir de la marginea stratului până la text, `max-width` = până la marginea ecranului. În starea asamblată straturile sunt suprapuse (20-30% overlap) și mărite cu `A = clamp(heroW/maxW, 1, 1.9)` ca să se potrivească cu burgerul din `hero`.
Fără straturi (`.layer` lipsă): imaginea asamblată se estompează la 0.28, etichetele apar într-o coloană (fără fir).

### Explode închis (`explode(i, false)`)
```
0.00  etichete + fire opacity->0 / scaleX->0 (0.16, de jos în sus, 0.025)
0.06+(n-1-k)·0.06  straturile se reasamblează de jos în sus (0.5 power3.inOut)
TE-0.12  imaginea asamblată opacity 0->1 (0.14), TE: straturile autoAlpha->0
TE-0.04  slam: visual scaleY .94 / scaleX 1.03 (0.08) -> 1 back.out(3.2) (0.42)
```
Poate fi întrerupt în orice moment (se omoară tween-ul și se construiește cel opus din starea curentă).

### Idle
Produsul activ (`.prod__hero` + `.prod__loop`) respiră ±4 px. Se oprește: la explode, la change, când hero iese din viewport (IntersectionObserver, prag 0.15, `pause()/resume()`), în reduced-motion.

### Scroll (un singur efect, fără pin)
`ScrollTrigger` pe `#hero`, `start: top top`, `end: bottom top`, `scrub: 0.5`: `.hero__stage` scale 1 -> .86 și y -24 px; `.hero__word` y +14% din înălțimea hero și opacity -> .35. Reveal-uri: `y 24 -> 0` + opacity, 0.4 s `power3.out`, o singură dată (`once: true`), `start: top 88%`. Elementele deja vizibile la load nu sunt ascunse.

## 4. Reduced-motion (`prefers-reduced-motion: reduce`)
- fără intro (se scoate doar clasa `mx-pre`), fără idle, fără scroll-effect, fără reveal, fără video autoplay;
- `change` = crossfade 0.15 s liniar pe `.prod` (vechi `is-leaving`, nou `is-entering`);
- `explode` = straturile apar direct în poziția explodată, etichetele și firele direct vizibile; închiderea la fel, direct;
- ascultă schimbarea setării din OS la runtime.

## 5. Geometria straturilor (3 căi, în ordinea prioritații)
1. Atribute pe fiecare `.layer`: `data-cx`, `data-ey`, `data-w`, `data-h` = fracțiuni din cutia vizuală (valorile `exploded.cx / cy / w / h` din `layers.json`); opțional `data-ay` (y asamblat forțat).
2. `window.SNAQ_LAYERS = { "<slug>": <conținutul layers.json> }` (A4 îl poate inlina).
3. `data-json="layers/<slug>/layers.json"` pe `.prod__layers` (fetch la preîncărcare).
Fără niciuna: fallback egal distribuit după dimensiunile naturale (funcțional, dar nu fidel imaginii).

Imaginile `layers/<slug>/layer_NN.webp` se pun ca `<img class="layer" data-layer="NN" src=... alt="">`; ordinea `data-layer` = ordinea din `layers.json` (0 = chifla de sus). Sunt transparente și decupate la bbox. Cutia vizuală trebuie să fie 4:5 ca `exploded.png`.

## 6. Video loop (opțional)
`<video class="prod__loop" muted playsinline loop preload="none" data-src="...">`. JS: pune `src` doar pentru produsul activ, după intro; `play()` doar dacă hero e în viewport, produsul nu are explode deschis, nu e Save-Data, `effectiveType` nu e 2g/3g, nu e reduced-motion; fade-in 0.4 s la `play()` reușit; `pause()` la ieșire din viewport, la change, la tab ascuns. `.prod__loop` e `position:absolute; inset:0; object-fit:cover; opacity:0` din `motion.css`.

## 7. Integrare (ordinea scripturilor)
```html
<head>
  <script>document.documentElement.classList.add('mx-pre')</script>   <!-- inline, înainte de CSS -->
  <link rel="stylesheet" href="motion/type.css">
  <link rel="stylesheet" href="motion/motion.css">
  <link rel="stylesheet" href="ux/....css">                           <!-- CSS-ul lui A2 după -->
</head>
<body> ... #hero ... 
  <script src="motion/node_modules/gsap/dist/gsap.min.js"></script>        <!-- 73 KB, 28 KB gzip -->
  <script src="motion/node_modules/gsap/dist/ScrollTrigger.min.js"></script> <!-- 45 KB, 18 KB gzip; opțional -->
  <script src="motion/motion.js"></script>                                  <!-- ~8 KB gzip -->
  <script> /* codul de stare al lui A2 */ SNAQMotion.init(document.getElementById('hero')); </script>
</body>
```
- `init()` se apelează o dată, după ce DOM-ul hero există. Idempotent.
- A2 poate fie să emită `hero:change` / `hero:explode` pe `#hero` (motion.js le ascultă), fie să apeleze `SNAQMotion.change/explode` direct. Dacă face ambele, a doua apelare în 80 ms cu aceiași parametri e ignorată.
- `hero:change` cu `detail.dir` (+1/-1) opțional; dacă lipsește se deduce din `to > from` (la 3 produse nu există wrap-around).
- Dacă `gsap` lipsește, `motion.js` iese fără eroare, iar `mx-pre` nu apare fără snippetul inline; dacă snippetul e prezent dar `init` nu rulează, elementele ascunse devin vizibile singure după 2.8 s (animație CSS `mx-failsafe`).
- `SNAQMotion.refresh()` = `ScrollTrigger.refresh()` (după ce se încarcă fonturile/imaginile care mută layout-ul).
- Fonturile din `type.css` sunt relative la `motion/` (`../src/site/src/fonts/`). La build A4 le inlinează sau le copiază și rescrie căile.

## 8. Cerințe pentru A2 (ca animațiile să arate cum trebuie)
1. `.prod__hero` trebuie să fie imaginea **decupată** (`layers/<slug>/hero_cut.webp`, produsă de `cut_layers.py`), nu `hero.png` cu fundal plin. Cu fundal plin dreptunghiul acoperă SMASH-ul și rămân vizibile doar S și H. Fallback dacă nu există decupaj: `mix-blend-mode: lighten` pe `.prod__hero` (artefacte pe zonele întunecate ale cărnii).
2. `.hero__word` în spatele stage-ului (`z-index` mai mic), centrat vertical spre partea de sus a burgerului (în demo: `top: calc(44px + 6svh)` pe mobil), ca litere să iasă pe lângă calota chiflei.
3. `.prod__visual` cu `position: relative`, raport 4:5, `.prod__layers` și `.prod__labels` copii ai lui.
4. La `change`, A2 poate comuta `is-active` imediat: `motion.css` ține produsul vechi vizibil (`is-leaving`) cât durează ieșirea. A2 să nu pună `visibility:hidden !important` pe `.prod`.
5. Textele etichetelor scurte (<= ~22 caractere) ca să încapă pe un rând la 360 px.
