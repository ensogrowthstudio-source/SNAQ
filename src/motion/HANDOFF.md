# HANDOFF · A3 tipografie + motion

## Ce e gata
| Fișier | Rol |
|---|---|
| `cut_layers.py` | `python3 motion/cut_layers.py <slug>` : `assets/gen/<slug>/exploded.png` -> `motion/layers/<slug>/layer_NN.webp` (transparente, bbox, WebP q82, max 900 px) + `layers.json` + `_sheet_dark.png` / `_sheet_light.png`. Face și `hero_cut.webp` (produsul asamblat decupat, 1000 px, cadru 4:5 păstrat) din `hero.png`. `_placeholder` merge pe `g1_v1.png` + `h1_classic`/`h3_double`. Opțiuni: `--thr`, `--no-hero`, `--src/--out`. |
| `motion.js` | `window.SNAQMotion = { init, change, explode, refresh, destroy }`. GSAP, doar transform/opacity. |
| `motion.css` | stări anti-flash (`mx-pre`), straturi, etichete cu fir galben + număr lila, mască roll-up. |
| `type.css` | @font-face Anton + Archivo 400/700 (`font-display: swap`), scară fluidă clamp 360->1440, stil SMASH (hibrid contur + umplere slabă; variante `--solid`, `--outline`). |
| `demo.html` | banc autonom (3 produse, 3 căi de geometrie, swipe/tab/tastatură). |
| `tools/serve_and_shoot.py`, `tools/variants.py` | capturi deterministe Playwright (ceasul GSAP avansat manual). |
| `shots/` | intro 1/150/300/450/600/800/1300 ms, change, explode, close, variante, `demo.webm` (390x844, 13 s: intro, 3 change-uri, swipe rapid întrerupt, explode, închidere, scroll). |
| `layers/` | `_placeholder/` (7 straturi), `double-bacon/` (8), `double-el-chapo/` (9): rulate pe exploded-urile A1 existente la 25.11, 23:3x. `italian-beef-roll` nu exista încă. |
| `MOTION-SPEC.md` | tokeni, coregrafie pe timeline, DOM citit, integrare, reduced-motion, cerințe pentru A2. |
| `node_modules/gsap` | gsap 3 (`gsap.min.js` 73 KB / 28 KB gzip, `ScrollTrigger.min.js` 45 KB / 18 KB gzip). |

## Verificat
- Zero `pageerror` / console error / warning / requestfailed în toate rulările (mobil 390x844 și 360x640, desktop 1440x900, reduced-motion).
- Interrupt: 6 schimbări la 90 ms + explode + change => stare curată (toate `style` goale, clasele temporare scoase, straturi ascunse).
- Reduced-motion: fără intro, change = crossfade, explode direct (capturi în `shots/var_reduced_*`).
- Fără straturi (`?nolayers=1`): doar etichete, fără erori; închiderea restaurează opacitatea imaginii.
- ș, ț, Ș, Ț, Ă, Â, Î prezente în cmap-ul tuturor celor 3 fonturi (fontTools) și randate corect în capturi (`șmecher, țâfnos, strivită, două`).
- Decupajul straturilor: contact sheet pe fond închis și deschis, margini curățate (rembg u2net + choke 2 px + estimare culoare prim-plan). Modelul s-a descărcat; chroma-key rămâne fallback automat.

## De știut / neverificat
- **60 fps pe telefon: NEMĂSURAT.** Am testat doar în Chromium headless pe desktop. Designul respectă regulile (doar transform/opacity, will-change temporar, ~8 KB JS propriu), dar A4 trebuie să măsoare pe un Android mediu real sau cu throttling CPU 4x.
- Cu `hero.png` plin (fundal #0D0B09 opac), SMASH e acoperit: rămân vizibile doar S și H. `.prod__hero` trebuie să folosească `layers/<slug>/hero_cut.webp`. Decupajul pierde umbra de sol și aburul din imagine (abur ușor tăiat de rembg); dacă SNAQ vrea abur, A1 îl poate livra ca strat separat sau prin `loop.mp4`.
- Exploded-urile A1 actuale: Double Bacon are 8 straturi (două sosuri într-un singur strat), Double El Chapo 9 (două perechi brânză+carne lipite într-un singur strat, 343 px și 340 px înălțime). Etichetele (`li[data-layer]`) se potrivesc cu straturile după index: A2 trebuie să alinieze textele la straturile reale din `layers.json` (sau A1 să regenereze cu goluri între brânză și carne), altfel eticheta „Cheddar" arată spre o pereche brânză+carne.
- SMASH: am testat hibrid (contur 1.5 px galben .55 + umplere .075), umplere solidă .14 și contur pur. Implicit: hibrid (cea mai lizibilă la 360 px fără să concureze cu burgerul). Pe pozițiile unde burgerul acoperă 78% din lățime, SMASH se citește doar dacă literele ies deasupra calotei: vezi cerința 2 din MOTION-SPEC §8.
- Pe desktop `--fs-word` e plafonat la `52vh` ca să nu depășească hero-ul.
- Layout-ul din `demo.html` (tab-uri, spațieri, desktop) e doar pentru test; nu e propunere de UX.
- Videoul loop e implementat (lazy, Save-Data, viewport) dar netestat cu un `loop.mp4` real: A1 încă nu a livrat niciunul.
- ScrollTrigger e opțional: fără el scroll-efectul și reveal-urile se sar, restul merge.

## Ce urmează
- A2: citește MOTION-SPEC §5 și §8 (atribute pe `.layer` sau `window.SNAQ_LAYERS`, imaginea decupată, z-index SMASH, etichete scurte).
- A4: inlinare `gsap.min.js` + `ScrollTrigger.min.js` + `motion.js` + CSS, snippetul `mx-pre` în `<head>`, rescriere căi fonturi, test de fps pe dispozitiv; rulat `cut_layers.py italian-beef-roll` când apare exploded-ul.
- Re-rulare după fiecare regenerare A1: `python3 motion/cut_layers.py <slug>` (durează ~30-60 s per produs pe CPU).

## De confirmat
Nimic legat de conținutul SNAQ. Textele din demo sunt copiate din `ux/products.json` / BRIEF (prețuri și -20% neconfirmate, vezi BRIEF).
