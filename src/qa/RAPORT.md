# RAPORT QA A4 (SNAQ demo v5)

Build testat: `build/dist/index.html`, servit local cu `qa/tools/serve.py` (gzip + Range, ca un hosting real). Chromium din /opt/pw-browsers (Playwright), Lighthouse 13.6 din `qa/lh`.

## Cifre
| Metrica | Valoare |
|---|---|
| Prima zona (pana la sfarsitul intro-ului, fara video) | **294 KB** pe 390x844 si pe 1440x900: index.html 113 KB (gzip) + hero AVIF 93 KB + press/assemble/local 94 KB (lazy, dar Chrome le ia devreme). Fara cele 3 poze de sub fold: 206 KB. Buget: < 600 KB |
| Total dupa o sesiune completa (3 produse, 3x explode, scroll pana jos, 3 video) | 2046 KB mobil, 1807 KB desktop |
| `dist/` pe disc | 4.4 MB (html 279 KB, img 2.9 MB cu toate variantele, media 1.0 MB) |
| Lighthouse mobil (preset perf, Moto G Power, 4G simulat, CPU 4x), 3 rulari, mediana | **LCP 2.1 s** (1.99 / 2.19 / 2.11), FCP 0.96 s, **CLS 0**, **TBT 153 ms** (90-188), Speed Index 1.7 s, scor 0.97 (0.97-0.99). Raport: `lighthouse-mobile.html`, cifre: `lighthouse-summary.json` |
| Elementul LCP | imaginea hero (208k px²), la 1.5 s in rularea mea cu 4G+CPU 4x |
| Erori | pageerror = 0, console error/warning = 0, requestfailed = 0 pe toate rularile (3 viewport-uri, comportament, reduced-motion, CPU 4x) |
| CPU 4x, 390x844, intro + 3 schimbari + explode/inchis, inregistrare video activa (`demo_390.webm`, 16 s) | 1546 cadre rAF: mediana 16.7 ms, p95 33.3 ms, max 133 ms; 34 cadre > 33 ms, 20 > 50 ms, 8 > 100 ms. Long tasks (`perf_cpu4x.json`): 9, intre 51 si 125 ms; cele mai lungi (113 + 125 ms) sunt la incarcarea scripturilor, cele din interactiune 53-116 ms (cel de 116 ms la prima deschidere de „Ce are?” pe produs: decodare straturi + calcul geometrie). Inregistrarea video a Playwright adauga ea insasi sarcina, deci cifrele sunt pesimiste |

Buget: prima zona, LCP si CLS in tinta, zero erori. TBT 153 ms e sub 200 ms; nu e un buget impus.

## Ce am verificat
**Capturi** (`shots/`, toate vazute): 360x640 si 390x844 (touch, DPR 3) si 1440x900: hero dupa intro, dupa swipe/sageata pe fiecare produs, explode deschis pe fiecare produs, sheet comanda, sectiunile Cum/Meniu/Local/Comanda, footer. Foi de contact: `_sheet_*.png`, `_diacritice.png`.
Etichete la 360: masurate cu getBoundingClientRect, 0 in afara ecranului (`shots_report.json`). Straturi: numar real 8/9/9 = numar etichete, fiecare eticheta verificata pe imagine.

**Comportament** (`tools/behavior.py`, `behavior_report.json`, 390x844 touch): toate OK.
- swipe stanga/dreapta (CDP touch real), swipe sub prag ramane pe loc, ←/→ cu wrap, click pe tab, ←/→/Home pe tab (roving tabindex, focusul urmeaza), explode+inchis de 2 ori la rand, explode+Esc, explode apoi swipe (se inchide singur), **swipe rapid de 6 ori** si explode imediat dupa schimbare: stare curata (un singur `is-active`, 0 `is-leaving/entering`, `style` fara transform/opacity pe `.prod`/`.prod__visual`, straturi ascunse, SMASH fara stil inline).
- sheet: deschis de 2 ori, focus capcana (5x Tab ramane in sheet), Esc inchide, focusul revine pe butonul „Comanda acum”, fundalul `inert`; Wolt/Bolt nu navigheaza si au `href` gol; Glovo are linkul din BRIEF.
- reduced-motion: tab, sageata, explode (straturile apar direct, 9 etichete vizibile, fara video), inchidere, sheet: OK.
- cele 3 hero-uri se hidrateaza dupa intro (AVIF 1000w pe DPR 3).

**Ș/ț**: Ș, ț, ă, â, î randate corect in Archivo (bara de sus „BUCUREȘTI”, „Castraveți murați”, „MĂNÂNCI”, „Strivită”) si in Anton (titluri, „ȚI-E FOAME?”), virgula, nu sedila.

## Probleme gasite si reparate (detalii in build/HANDOFF.md)
1. LCP 2.9 s: candidatul era SMASH (text) pe urma imaginii inregistrate cu arie partiala; drop-ul de intro mutat in viewport -> 2.1 s.
2. Dupa un swipe tactil, primul tap pe „Ce are?” nu facea nimic (flag `swiped` neresetat). Reparat.
3. Dupa inchiderea „Ce are?”, `transform`+`will-change` ramaneau pe vizual; in reduced-motion hero ramanea invizibil (opacity 0). Bug in motion.js (A3), reparat prin patch la build.
4. 360x640: stiva explodata acoperea tab-urile si badge-ul; etichete suprapuse. Stiva se comprima acum si etichetele se de-coliziona.
5. A2 punea `is-exploded -> hero opacity 0` instant, ceea ce anula animatia A3. Scos.
6. Desktop: `.prod__visual` devenea `relative` (motion.css) si burgerul cadea in stanga-jos; SMASH iesea din ecran. Reparat.
7. SMASH nu se vedea prin video (dreptunghi opac): blend `lighten` + SMASH mutat in stage.

## Ce NU s-a testat / ramane pe telefon real
- Fluiditatea pe Android mediu si iPhone (am doar Chromium cu CPU 4x; fara GPU real). In special `mix-blend-mode: lighten` peste `<video>` si contra-zoom-ul CSS sincron cu video.
- Safari/iOS: AVIF (iOS < 16.4 cade pe WebP), autoplay video `muted playsinline`, `:has()`.
- Firefox nu a fost rulat. Chrome real cu throttling de retea in DevTools (am folosit emulare CDP in `tools/lcp_debug.py`).
- LCP in teren (CrUX): video-ul poate deveni candidat; aria lui e limitata la a imaginii, neverificat in teren.
- Zero test cu cititor de ecran real; doar structura (aria, focus, inert).
- Linkurile Glovo/Wolt/Bolt: doar Glovo are href; nu am deschis linkul (fara retea externa).
- Rularile Lighthouse sunt pe localhost: latenta si banda sunt simulate, dar nu exista DNS/TLS reale.

## Fisiere
`tools/`: serve.py, common.py, shots.py, behavior.py, perf.py, weight.py, lcp_debug.py. Rapoarte: `shots_report.json`, `behavior_report.json`, `perf_cpu4x.json`, `weight.json`, `lighthouse-summary.json`, `lighthouse-mobile.html`. `qa/lh/` = Lighthouse instalat local (node_modules, se poate sterge).
