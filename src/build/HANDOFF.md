# HANDOFF A4 (integrare, cod, mobil)

## Livrabil
`build/dist/` = `index.html` (279 KB, 107 KB gzip: CSS, JS, GSAP, ScrollTrigger, motion.js, fonturi woff2 base64, logo si favicon inline) + `img/` (AVIF + WebP, 600/1000 px) + `media/<slug>.mp4`.
`build/snaq-demo-v5.html` = acelasi fisier ca `dist/index.html`, dar NU e autonom: imaginile si video-urile sunt fisiere alaturate (cai relative `img/…`, `media/…`). Am ales asa (nu base64) pentru ca srcset, lazy si bugetul primei zone nu se pot face cu imagini inline (3 MB de imagini ar intra in HTML). Dist-ul se serveste de pe orice hosting static; pentru test: `python3 qa/tools/serve.py 8765` (gzip + Range pentru mp4).

## Reconstruire
```
python3 build/tools/encode_loops.py 24   # video (ffmpeg) -> build/media + media/loops.json (parametri aliniere CSS)
python3 build/tools/make_images.py       # AVIF/WebP din motion/layers/<slug>/ -> build/img + meta.json
python3 build/build_v5.py [--images]     # HTML + dist/ (asserturi pe fiecare inlocuire)
```
Dupa o regenerare A1: `python3 motion/cut_layers.py <slug>`, apoi `encode_loops.py`, apoi `build_v5.py --images`. Produsele, preturile, oferta, meniul: `build/products.v5.json` (copie a `ux/products.json`).

## Ce am schimbat fata de A2/A3 (documentat, aplicat la build cu `sub1()` + assert, sursele lor nu sunt atinse)
**products.v5.json**: `layers` = o eticheta per strat REAL din `layers.json` (8 / 9 / 9; A2 avea 8 / 11 / 9). Maparea (index 0 = sus):
- Double Bacon: Chifla cu unt, Sos Dijon si Spicy, Castraveti murati, Ceapa prajita, Bacon 2 felii, Cheddar, Carne Black Angus, Chifla jos.
- Double El Chapo: Chifla cu unt, Sos andalouse, Castraveti murati, Ceapa prajita, Ceapa caramelizata, Ceapa cruda, "Carne smash + cheddar", "A doua carne + cheddar", Chifla jos (cheddar lipit de carne in ambele straturi, deci apare in eticheta).
- Italian Beef Roll: Lipie crocanta, Pesto si sos de trufe, Parmesan, Rucola, Rosii + rosii confiate, 2 chiftele de vita, Cartofi prajiti, Salata iceberg, Lipie.
Clip-path-ul A2 pe exploded.png nu mai exista: straturi WebP/AVIF decupate (A3) + `hero_cut` transparent.

**Template A2**: scos CSS-ul de straturi/etichete (clip-path, mask, `.is-exploded` care punea hero la opacity 0 instant si strica animatia A3), scoase fonturile cu cai relative, `.hero__word` mutat ca prim copil al `.hero__stage` (altfel `mix-blend-mode` al video-ului nu vede SMASH; stage e stacking context din `container-type:size`), `.hero .prod__visual{position:absolute}` (motion.css il pusese relative si strica desktopul), logica de video A2 inlocuita cu un buton de pauza (redarea o face motion.js), `go()` nu mai scoate `is-leaving` imediat (A3.change nu returneaza promise), reset pe `swiped` (dupa un swipe tactil nu vine niciun click, deci primul tap pe „Ce are?” era inghitit).

**motion.js (A3), patch-uri in memorie la build** (cautati `// A4` / vezi `build_v5.py`):
1. poarta de video: nu se cere nimic pana la `snaq:intro-done`; `preload=auto` abia atunci; poster setat atunci.
2. `ready()` cheama `SNAQHydrate` (straturile se hidrateaza din `data-srcset`); `warm()` incarca doar straturile produsului activ, celelalte la schimbare (idle).
3. intro: caderea burgerului porneste din -13% viewport (era -55%). Motiv: LCP-ul se inregistra cu aria partiala a imaginii (restul iesea din ecran), iar SMASH (2.7 s) si video-ul (4.6 s) deveneau candidate mai mari. Dupa schimbare: LCP = imaginea, 208k px², 1.5 s sub 4G+CPU 4x. Caderea e mai scurta decat in MOTION-SPEC; daca A3 vrea una dramatica, trebuie o alta solutie de LCP (ex. SMASH in SVG).
4. `closeIt()`: dupa inchiderea explode ramaneau `transform`/`will-change` pe `.prod__visual` (stacking context permanent, deci blend-ul video stricat) si, in reduced-motion, hero ramanea cu opacity 0 (burgerul disparea dupa „Ce are?” inchis). Bug real in A3, reparat.
5. stiva explodata se comprima vertical pe ecrane unde nu incapea intre tab-uri si info (360x640 iesea peste tab-uri si peste badge).
6. etichetele se de-coliziona vertical (cele pe 2 randuri se suprapuneau cu vecinele).

## Imagini
Hero: `<picture>` AVIF q60 + WebP q80, 600w si 1000w, `sizes="(min-width:900px) 52vw, 100vw"`, produsul activ cu `fetchpriority=high` + `<link rel=preload>`. Celelalte doua hero-uri si toate straturile au `data-srcset`, hidratate de `snippets/glue.js`: heroes dupa intro (idle, nu pe 2g/3g/Save-Data) sau la prima atingere pe tab/stage/sageti; straturile la atingerea pe „Ce are?” sau in idle (produsul activ). AVIF la q60 = ~75% din WebP, la 100% zoom nu am vazut diferenta (comparatie facuta pe hero Double Bacon).
`build/img/` e rezultatul intermediar, `dist/img/` ce se publica. Pozele din sectiunile de jos (press, assemble, local) convertite in WebP.

## Video
H.264 high, preset veryfast, CRF 24, fara audio, faststart, 720x960, ping-pong (inainte + inapoi, fara salt). 286 / 503 / 245 KB. Fiecare e corectat de culoare la #0D0B09 (masurat pe colturi) si micsorat (zoom-out 0.93-0.95 + pad) ca burgerul sa nu iasa din cadru la varful push-in-ului.
- Italian Beef Roll: sursa iese din cadru dupa ~1.2 s (burgerul atinge marginile cadrului la frame 30), deci folosesc doar primele 28 de cadre incetinite 1.8x (baza de interpolare `blend`), ping-pong = 4.1 s. Double Bacon: 60 de cadre (2.5 s), El Chapo 84 (3.5 s), tot cu ping-pong.
- Aliniere cu hero_cut: wrapper `prod__loopin` cu translate/scale la start (masurat pe bbox-ul burgerului) + animatie CSS de contra-zoom sincrona cu video (`is-playing`/`is-paused`) ca burgerul sa stea pe loc si sa se miste doar aburul. Parametrii sunt in `media/loops.json` si ajung ca variabile CSS (`--vtx --vty --vs --vk --vdur`).
- `mix-blend-mode: lighten` pe wrapper: fundalul video dispare peste SMASH si peste pagina. Wrapper-ul are `overflow:hidden` ca aria video-ului sa nu depaseasca aria imaginii (altfel devine candidat LCP).
- Fara video: hero-ul arata complet (reduced-motion, Save-Data, 2g/3g, `preload=none` pana dupa intro).

## Buget / rezultate (detalii in qa/RAPORT.md)
Prima zona 294 KB (index 113 KB gzip-ul serverului de test + hero 93 KB + 3 poze lazy de sub fold 94 KB), Lighthouse mobil mediana LCP 2.1 s, CLS 0, TBT 153 ms, scor 0.97.

## De confirmat / ramas
- Pe telefon real: fluiditatea (am doar Chromium desktop cu CPU 4x), `mix-blend-mode` pe video in Safari iOS, AVIF pe iOS < 16.4 (fara fallback separat: `<picture>` cade pe WebP automat, straturile la fel), `:has()` (dim SMASH la „Ce are?”, Chrome 105+, Safari 15.4+, Firefox 121+; fara el SMASH ramane vizibil sub etichete).
- Chrome poate raporta in teren (nu in Lighthouse) prima imagine a video-ului ca LCP daca e mai mare; aria e limitata la cea a imaginii, deci nu ar trebui sa schimbe candidatul, dar nu am putut verifica in CrUX.
- Oferta/preturile/linkurile Wolt si Bolt: neschimbate fata de A2 (Wolt si Bolt `href=""`, click-ul nu face nimic).
- Nu am minificat JS-ul (nu am avut un minificator instalat; a fost refuzata instalarea unui pachet). Castig estimat: ~25 KB brut, ~6 KB gzip.
- Imaginile si video-urile raman concept AI ("se inlocuiesc cu foto SNAQ", in footer).
