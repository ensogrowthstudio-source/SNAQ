# HANDOFF A2 (UX)

## Livrat
`v5.html` (pagina, un fișier HTML+CSS+JS de stare, imagini/fonturi prin căi relative `../assets/...`, `../src/site/src/...`), `products.json`, `UX-SPEC.md`, `shots/`, scripturi în `tools/`.
`v5.html` e GENERAT: editezi `v5.template.html` (CSS/JS/structură) sau `products.json` (produse, meniu, ofertă, linkuri, benzi straturi) și rulezi `python3 ux/build_ux.py`. Generatorul pune direct căile `assets/gen/<slug>/...` dacă fișierul există, altfel placeholder (fără 404); `--force-gen` forțează căile gen/.

## Actualizare director aplicată (Glovo, 25.11.2026)
`offer` per produs în products.json; hero: badge „-20% pe Glovo", preț Glovo mare + preț întreg tăiat (`<s aria-label="preț întreg">`), rând „-25% cu Glovo Prime". Meniul păstrează prețurile Wolt. Linkul Glovo e pe butoane (sheet + secțiunea Comandă).

## Hook-uri pentru A3 (motion)
- `window.SNAQMotion = {init(root), change(from,to,dir), explode(i,open)}`. Chemate de mine: `init(hero)` la DOMContentLoaded (și la `load` dacă lipsea), `change` după ce starea DOM e deja schimbată, `explode` la fel. Folosiți DOAR apelurile directe SAU DOAR evenimentele `hero:change` {from,to} / `hero:explode` {i,open} (bubble pe `#hero`), nu ambele, altfel animația se dublează.
- `change` poate returna Promise/timeline: articolul vechi păstrează `.is-leaving` (rămâne vizibil) până se rezolvă (max 1,6 s); fără motion, instant.
- Stare: `#hero[data-active]`, `.prod.is-active/.is-leaving/.is-exploded`, tab `aria-selected`, `.prod__explode[aria-pressed]`. API: `window.SNAQHero {go,next,prev,explode,active,count}`; eveniment `snaq:ready`.
- Straturile: `.layer[data-layer]` = aceeași `exploded.png` tăiată cu `clip-path` (`--t`, `--b`, și `data-band="sus,jos"` în % din înălțime). Poziția „desfăcută" e cea naturală (cutia `.prod__layers`); animați de la o stare strânsă (translateY spre centru) spre 0. Cutia e calculată din CSS (`--ex-top`, `--ex-hgt`, `--ex-w`, `--ex-left`). Etichetele `.prod__labels li[data-layer]` sunt poziționate pe banda stratului.
- Hero asamblat `.prod__hero` și `.prod__loop` fac fade-out la explodare prin CSS (opacity) – suprascrieți dacă animați altfel.
- Cuvântul `.hero__word span` (contur, 66vw mobil / 46vw desktop), `[data-reveal]` pe titluri/pași/poză local/platforme (fără ascundere din CSS: A3 poate seta starea inițială). Tranzițiile CSS ale sheet-ului/dock-ului (transform/opacity) se pot suprascrie; la reduced-motion sunt dezactivate.
- Nu animați `visual` cu `left/right`; layout-ul nu folosește `transform` pe `.prod__visual`.

## Rămâne pentru A4 (cod/mobil)
- Rulează build_ux.py cu imaginile finale; inlinează `src` din hero/layer/loop (`data-src` la video) și fonturile; `href` Wolt/Bolt când vin.
- Imaginile A1: fundalul diferă de #0D0B09 (hero (17,12,6)…(22,13,8); exploded (23,16,10)/(15,12,7)) – se vede un dreptunghi ușor pe straturi; fie A1 uniformizează, fie corecție de nivel la build. Exploded.png e 2:3 (nu 4:5), tăiat pe lățime în CSS (`exploded_ar` în JSON). Dacă A1 regenerează exploded, rulează `python3 ux/tools/bands.py <img>` și actualizează `layers[].band`/etichete (acum 8 / 11 / 9 straturi).
- Parametri de încadrare per produs în JSON: `hero_fit` {trim,bottom} (fracții din înălțimea hero.png), la nevoie reglați.
- WebP + dimensiuni reale în `width/height` (acum 1600×2000 generic, doar pentru raport). Imaginile `press.jpg`/`assemble.jpg` sunt 274px, folosite mici.
- Nu e implementat: „Alege pentru mine" (T8), memorarea ultimei platforme, lista/„Copiază lista" (T12–T14), starea „Deschis acum" (fără program confirmat). Bara de sus și dock-ul sunt simple.
- Lighthouse, greutate: placeholder-ele au 5–7 MB, deci cifrele de acum nu sunt relevante.
