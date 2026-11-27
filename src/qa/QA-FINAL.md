# QA FINAL, SNAQ demo v5 (închis + alb)

Rulat pe `build/dist/index.html` și `build/dist/alb/index.html`, build curent din `python3 build/build_v5.py`. Chromium (Playwright), touch + DPR 3/2/3/3 pe mobile, DPR 1 pe 1440×900. Viewport-uri: 360×640, 375×667, 390×844, 440×956, 1440×900. Cifre brute: `qa_final_inchis.json`, `qa_final_alb.json`, `qa_final_rm_*.json` (reduced-motion), `qa_file.json` (file://). Scripturi: `qa/tools/qa_final.py`, `qa_labels.py`, `qa_file.py`. Capturi: `qa/shots-qa/` (+ `_contact_inchis_390.png`, `_contact_alb_390.png`).

## Reparat

| # | Defect | Cauză | Reparație | Verificat |
|---|---|---|---|---|
| 1 | Etichetele „Ce are?" urcau peste chip-uri la 360×640 și 375×667 (Double El Chapo, Italian Beef Roll), pe ambele teme | stiva de 9 etichete (unele pe 2 rânduri) nu încape între chip-uri și info; de-coliziunea împingea în sus fără limită | `placeLabels` (patch în `build_v5.py`): măsoară stiva, iar dacă nu încape între chip-uri și info pune `.mx-tight` pe listă (o linie, 11px, fără numărul lila); în plus, prima etichetă nu mai urcă niciodată deasupra chip-urilor. CSS-ul `.mx-tight` e în `snippets/overrides.css`. Regula doar-pe-alb din `light.css` scoasă: un singur mecanism, ambele teme | 3 produse × 2 teme × 5 viewport-uri: 0 etichete peste chip-uri, 0 sub info, 0 suprapuse între ele, 0 în afara ecranului. Compact apare doar la 360×640 și 375×667 (p2, p3); la 390+ rămân 13px cu număr |
| 2 | Desktop: blocul de text (nume, preț, „Ce are?") sărea ~130px în jos la finalul fiecărei schimbări de produs | `motion.css` forțează `display:block !important` pe `.prod` cât ține tranziția, iar pe desktop `.prod` e `grid` cu info centrat vertical | `snippets/overrides.css`: la ≥900px `.is-leaving/.is-entering` rămân `display:grid` | CLS la schimbare: 0,1045 (închis) / 0,1044 (alb) pe fiecare din 8 schimbări → **0** pe toate. Pe mobil era deja 0 |

## Rezultate

| Verificare | Închis | Alb |
|---|---|---|
| Erori consolă / pageerror / requestfailed / HTTP ≥400, 5 viewport-uri | PASS, 0 | PASS, 0 |
| Overflow orizontal (scrollWidth > clientWidth) în hero și la sfârșitul paginii; elemente în afara ecranului | PASS, 0 | PASS, 0 |
| Imagini lipsă (`naturalWidth` 0) | PASS, 0 din 41 | PASS, 0 din 41 |
| Ținte atingere < 44px (hero, „Ce are?" ×3, sheet, panou, fiecare secțiune, footer; linkurile inline din text excluse) | PASS, 0 | PASS, 0 |
| Etichete „Ce are?" vs chip-uri / info / între ele / margine | REPARAT (#1) | REPARAT (#1) |
| Text peste burger / sub bara de sus / info peste CTA | PASS | PASS |
| Hero încape în viewport (CTA + „Livrare prin…" sub marginea de jos), 360×640 inclusiv | PASS (`Livrare…` se termină exact la marginea de jos la 360×640 și 375×667, fără aer) | PASS (la fel) |
| Text tăiat, diacritice tăiate (overflow/line-height în containere cu overflow) | PASS (singurele semnalări sunt `.sr`, textul doar pentru cititoare de ecran) | PASS |
| Schimbare produs prin chip ×3, săgeți ×4 (inclusiv wrap 3→1), tastă →, swipe ×3 (mobil): un singur panou activ, tab/pager/`data-active` consecvente | PASS | PASS |
| CLS la schimbarea produsului, mobil (4 viewport-uri × 8–11 schimbări) | **0** | **0** |
| CLS la schimbare, desktop | REPARAT: 0,1045 → **0** | REPARAT: 0,1044 → **0** |
| CLS la deschiderea/închiderea „Ce are?" (3 produse × 5 viewport-uri) | 0 | 0 |
| CLS la încărcare | 0 mobil; 0,0056 desktop (font swap pe bara de sus, sub prag) | la fel |
| „Ce are?" deschis/închis pe fiecare produs: 8/9/9 etichete vizibile, burger revine la opacity 1, fără `transform` rămas | PASS | PASS |
| Swipe rapid ×6 (120ms între) → scrollY rămâne 0, stare coerentă; apoi explode + închidere în <1s → închis curat; 3 tap-uri rapide pe „Ce are?" → deschis (paritate corectă); schimbare produs cu „Ce are?" deschis → se închide și arată noul produs | PASS | PASS |
| „Comandă acum" → sheet: focus pe prima platformă, Esc închide și focusul revine pe buton, X închide, click pe scrim închide | PASS | PASS |
| Panou navigare (mobil): se deschide, Esc închide (focus pe burger), fiecare din 5 linkuri (promo-card→#hero, Cum facem, Meniul, Localul, Comandă) duce la secțiune, închide panoul, `aria-expanded=false`. Secțiunea ajunge sub bară (top 40–64px față de bara de 56px; padding-ul secțiunii ține titlul vizibil) | PASS | PASS |
| Nav desktop (Promoții, Meniu, Cum facem, Localul) | PASS | PASS |
| Scroll prin toată pagina din 85% în 85% al viewport-ului: dock-ul nu acoperă butoane/linkuri, nicio apariție de overflow, dock ascuns la Comandă și în footer | PASS | PASS |
| Tab-uri meniu (7 categorii): selecție + listă + fără overflow | PASS | PASS |
| Footer: link Instagram, linkul spre cealaltă variantă (44px înălțime) nu e sub dock | PASS | PASS |
| Link între variante prin `http://` | PASS → `/alb/index.html` | PASS → `/index.html` |
| Link între variante din `file://` (ambele sensuri, 390 și 1440): URL corect, tema corectă (fundal `#0D0B09` / `#FBF8F2`), 0 erori, 0 imagini rupte, 9/9 etichete pe alb | PASS | PASS |
| Focus vizibil doar la tastatură: după click/tap pe chip `:focus-visible` false; după Tab true, inel 3px (negru pe alb, galben pe închis, cu inel contrastant) | PASS | PASS |
| Reduced-motion (360×640, 390×844, 1440×900): 8/9/9 etichete apar direct, schimbare produs coerentă, burger revine la opacity 1 după „Ce are?", sheet/panou/linkuri ok, CLS 0, 0 erori, fără overflow | PASS | PASS |

Captură de verificare pentru defectul #1: `qa/shots-qa/inchis_360x640_03_cearare_p1.png` și `..._p2.png`, plus `alb_*` echivalent.

## Observații, nerezolvate (nu sunt defecte de cod)

1. **Butoanele Wolt și Bolt nu fac nimic** (`href=""`, click nu deschide nimic, sheet-ul rămâne deschis), în sheet, în panou și în secțiunea Comandă. Un client care apasă pe ele vede un buton mort. Se rezolvă doar cu linkurile reale de la SNAQ; până atunci, de spus la prezentare.
2. Un tap în primele ~350ms după un swipe pe stage e înghițit intenționat (garda `swiped` din A2, ca un swipe cu mouse să nu declanșeze click). Cu degetul real nu se simte.
3. După click pe un link din panoul de navigare focusul ajunge pe `body`, nu pe secțiunea țintă. Impact doar pentru cititoare de ecran/tastatură.
4. Texte din meniu fără diacritice, preluate din Wolt: „Salata Greceasca", „Salata Chicken Parmesan". De confirmat cu SNAQ dacă se scriu „Salată Grecească".
5. Lighthouse (LCP/TBT) nu a fost rerulat după cele două reparații. Modificările ating doar poziționarea etichetelor după „Ce are?" și CSS-ul tranziției pe desktop, deci nu ar trebui să atingă LCP, dar nemăsurat.
6. Linkul „Vezi varianta pe …" din footer e pentru prezentare; se scoate la livrarea finală (`FOOT_END` și `foot__alt` în `build_v5.py`).

## Rămâne de testat doar pe telefon real

- Safari iOS: `:has()` (SMASH estompat la „Ce are?"), `mix-blend-mode: lighten` pe video (închis), AVIF sub iOS 16.4, `100dvh`/bara de adresă care se retrage (hero 360×640 are zero aer sub „Livrare…").
- Fluiditatea animațiilor pe procesor real (aici doar Chromium desktop, 4× throttle măsurat anterior).
- Swipe cu degetul real vs. evenimente CDP: conflictul cu gestul „înapoi" de la marginea ecranului în iOS/Android.
- Tastatura virtuală și zoom-ul de sistem (text mărit): etichetele compacte la 11px nu sunt testate cu font scalat.
- Imagini concept AI: culoarea reală pe ecrane OLED, marginile decupajelor pe alb pe ecrane luminoase.
