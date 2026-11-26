# SNAQ v5 — brief comun pentru agenți (director de creație: Opus)

Rădăcina: `/home/claude/snaq_v5/`. Fiecare agent scrie DOAR în folderul lui. Citești ce scriu alții, nu modifici.

| Agent | Scrie în | Atinge Higgsfield? |
|---|---|---|
| A1 Imagini | `assets/gen/` | DA — singurul |
| A2 UX | `ux/` | NU, niciodată |
| A3 Tipografie + motion | `motion/` | NU, niciodată |
| A4 Cod + mobil | `build/`, `qa/` | NU, niciodată |

## Ce facem
Homepage demo pentru SNAQ (smashed burgers, București; IG @snaq.ro; livrare Glovo/Wolt/Bolt). Prospect, nesemnat. Site-ul trebuie să arate ca ceva pentru care se plătesc bani: top-notch motion design, mobile first.
Plan mare: `src/plan-v5.md` (citește §3–§9). Versiunea veche (referință de conținut, NU de design): `src/site/src/v4.html`. Fonturi: `src/site/src/fonts/` (Anton = display, Archivo 400/700 = text).

## HERO = „Promoțiile perioadei" — 3 produse, omul alege unul
Ordinea: 1 Double Bacon · 2 Double El Chapo · 3 Italian Beef Roll.
Date (sursa: pagina SNAQ de pe Wolt, 25.11.2026; prețuri de confirmat cu SNAQ):

| slug | Nume | Preț Wolt | Ingrediente (Wolt) |
|---|---|---|---|
| double-bacon | Double Bacon | 52 lei | chiflă pufoasă unsă cu unt, 1 carne vită Black Angus smash, 2 felii bacon, cheddar, sos Dijon, sos Spicy, castraveți murați, ceapă prăjită, sare, piper |
| double-el-chapo | Double El Chapo | 60 lei | chiflă pufoasă unsă cu unt, 2 cărni vită Black Angus smash, ceapă, ceapă prăjită, ceapă caramelizată, cheddar, castraveți murați, sos andalouse, sare, piper |
| italian-beef-roll | Italian Beef Roll | 60 lei | lipie crocantă, 2 chiftele vită Black Angus zdrobite, salată iceberg, cartofi prăjiți, parmesan, rucola, roșii, oregano, roșii confiate, sos pesto, sos de trufe negre |

Atenție: „Double Bacon" are O SINGURĂ carne (dublu = bacon). Double El Chapo are DOUĂ cărni.

Oferta: Eduard a dat o captură „Promoții" cu -20% și -25% pe toate trei (`assets/ref/promotii_screenshot.png`). Pe Wolt nu apare nicio promoție → platforma și sensul lui -25% sunt NECONFIRMATE. Pe site: badge „-20%" pe fiecare produs, fără preț redus calculat. Toate datele produselor stau într-un singur loc (`ux/products.json`) ca să se schimbe ușor.

ACTUALIZARE 23:30 — oferta confirmată pe Glovo: „-20% la unele articole" + „-25% cu Prime". Prețuri Glovo redus/tăiat: Roll 52,20/65,00 · Double Bacon 41,80/52,00 · Double El Chapo 48,20/60,00. Fără dată de final. Link Glovo: https://kaspi.glovoapp.com/ro/ro/bucharest/stores/snaq-buc

Comandă: butoane Glovo (cu linkul de mai sus), Wolt, Bolt (aceste două fără link deocamdată) (`href` gol / `data-href=""`, fără text „link de adăugat" vizibil).

## Sistem vizual (din plan-v5 §5)
- fundal #0D0B09 · accent galben #F8B018 (DOAR text negru pe galben; niciodată alb pe galben) · cremă #F8F3E8 pentru text · lila #9D8CE0 accent mic (≤5% din ecran)
- Anton pentru titluri și cuvântul uriaș SMASH din spatele burgerului · Archivo pentru text
- Animăm doar `transform` și `opacity`. Blur-ul e copt în imagini, nu `filter` CSS. `prefers-reduced-motion` = fără mișcare, totul încă funcționează.
- Fără auto-advance pe slider. Fără scroll-jacking. Ținte tactile ≥ 44px.
- Mobil întâi: 360×640 și 390×844 sunt ecranele de referință; desktop 1440×900 secundar.
- Animație: GSAP (+ScrollTrigger dacă trebuie), inlinat din npm, fără CDN la final.

## Contract DOM pentru hero (A2 îl construiește, A3 îl animă, A4 îl verifică)
```html
<section id="hero" class="hero" data-active="0">
  <div class="hero__word" aria-hidden="true"><span>SMASH</span></div>
  <div class="hero__tabs" role="tablist" aria-label="Promoțiile perioadei">
    <button role="tab" class="hero__tab" data-i="0" aria-selected="true">Double Bacon</button> ...
  </div>
  <div class="hero__stage">
    <article class="prod is-active" data-i="0" data-slug="double-bacon" role="tabpanel">
      <div class="prod__visual">
        <img class="prod__hero" ...>                      <!-- produsul asamblat -->
        <video class="prod__loop" muted playsinline loop preload="none" data-src="..."></video> <!-- opțional -->
        <div class="prod__layers" aria-hidden="true">      <!-- straturile pentru „Ce are?" -->
          <img class="layer" data-layer="0" ...> ...         <!-- 0 = sus (chifla), crescător în jos -->
        </div>
        <ul class="prod__labels"> <li data-layer="0">Chiflă cu unt</li> ...</ul>
      </div>
      <div class="prod__info">
        <span class="badge">-20%</span>
        <h2 class="prod__name">Double Bacon</h2>
        <p class="prod__desc">…o propoziție…</p>
        <p class="prod__price">52 lei</p>
        <button class="prod__explode" aria-pressed="false">Ce are?</button>
      </div>
    </article> ...
  </div>
  <button class="hero__cta" data-open="order">Comandă</button>
</section>
<div class="order-sheet" id="order" role="dialog" aria-modal="true" hidden> Glovo / Wolt / Bolt </div>
```
Evenimente (A3 le ascultă, A2 le emite din JS-ul de stare): `hero:change` (detail {from,to}), `hero:explode` (detail {i, open}). A2 face starea (index activ, swipe, tastatură ←/→, tab-uri, sheet), A3 face DOAR animațiile, prin `window.SNAQMotion = { init(root), change(from,to,dir), explode(i,open) }`. Dacă `SNAQMotion` lipsește, site-ul merge fără animații.

## Imagini (A1 le produce, în ordinea asta; până apar, A2/A3 folosesc `assets/placeholder/`)
Per produs, în `assets/gen/<slug>/`:
- `hero.png` — produsul asamblat, 4:5, fundal închis uniform #0D0B09, lumină caldă din stânga sus, rim light, unghi 3/4 jos.
- `exploded.png` — vedere din lateral, la nivelul ochilor, straturile plutind separat cu goluri MARI și egale, fundal plat uniform, nimic suprapus → se taie în straturi pe benzi orizontale.
- `loop.mp4` — opțional, 5 s, 720p, fără sunet, cameră fixă, push-in foarte lent, abur.
Manifest: `assets/gen/MANIFEST.json` (A1 îl ține la zi: fișier, job_id, status, observații QC).
Placeholder azi: `assets/placeholder/g1_v1.png` (exploded generic), `h1_classic.png`, `h3_double.png` (asamblat).

## Reguli fixe
- Nimic plătit. Nimic publicat. v2–v4 nu se ating.
- Tot ce e generat e „imagine concept generată, se înlocuiește cu foto SNAQ" — rândul ăsta apare în footer și în README.
- Texte în română, cu ș/ț cu virgulă. Fără emoji. Fără promisiuni neconfirmate (program, livrare gratuită, timp de livrare etc.).
- La final fiecare agent scrie `<folderul lui>/HANDOFF.md`: ce a făcut, fișierele, ce rămâne, ce e de confirmat.
