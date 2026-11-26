# SNAQ v5 · UX-SPEC (A2)

Fișiere: `v5.html` (generat), `v5.template.html` (sursa), `products.json` (date), `build_ux.py` (generator), `tools/` (bands.py, shots.py, behavior.py), `shots/`.

## Flux
Intră (din IG, mobil, flămând) -> vede din prima 3 promoții (tab-uri cu numele) și un burger mare -> alege (tap pe tab, swipe, ←/→) -> vede preț Glovo redus + preț întreg tăiat + „-25% cu Glovo Prime" -> „Ce are?" desface straturile cu etichete -> „Comandă acum" (jos, în zona degetului) -> sheet cu Glovo / Wolt / Bolt.
Sub hero: Cum se face un smash -> Meniul (tab-uri pe categorii) -> Localul -> Comandă -> subsol. Pe mobil, după hero apare un dock „Ți-e foame? · Comandă" (dispare la secțiunea Comandă).

## Prima zonă la 360×640 (verificat în `shots/360x640_01_hero.png`)
Logo mic, H1 mic „Smashed burgers în București", burger (meniu) 52px, 3 tab-uri, burger foto, badge „-20% pe Glovo", „-25% cu Glovo Prime", nume, preț nou + preț tăiat, „Ce are?", CTA „Comandă acum". Pe ecrane sub 720px înălțime propoziția descriptivă se ascunde (rămâne în textul pentru cititor de ecran).
Cel mai lung nume („Italian Beef Roll", 17 caractere) intră pe un rând la 360px (Anton 10.2vw).

## Stări
| Componentă | Stări |
|---|---|
| Tab | implicit (gri) · activ (crem + linie galbenă) · focus (inel dublu negru/galben) · roving tabindex, ←/→/Home/End |
| Produs (`.prod`) | `is-active` (vizibil) · inactiv (`inert`, `aria-hidden`, `visibility:hidden`) · `is-leaving` (rămâne vizibil cât rulează animația A3) · `is-exploded` |
| „Ce are?" | `aria-pressed` false/true; true = fundal crem, plus devine ×; Esc îl închide; la schimbarea produsului se închide singur |
| Etichete straturi | ascunse; la explodare apar pe dreapta (mobil) / ambele părți (desktop); lista text pentru cititor de ecran e și în `.sr` de sub preț |
| Sheet comandă | `hidden` -> `is-open`; focus pe primul buton, trap Tab, Esc/backdrop/× închid, focusul revine pe butonul care l-a deschis, fundal `inert` + scroll blocat |
| Meniu burger | același mecanism (modal), `aria-expanded` pe buton |
| Platforme | Glovo are link (target _blank, rel noopener). Wolt, Bolt: `href=""`, click-ul nu face nimic, fără text „link de adăugat" |
| Reduced motion | fără tranziții, fără video; explodarea apare direct; totul funcționează |
| Imagine lipsă | `data-fallback` -> placeholder; dacă și ăla lipsește: cadru punctat cu numele produsului (`is-broken`, vezi `shots/360x640_07_broken.png`) |
| Video bucla | pornește doar dacă există `loop.mp4`, nu e reduced-motion, produsul e activ și nu e explodat; buton pauză 44px apare când rulează |

## Texte finale
H1 „Smashed burgers în București" · eyebrow S2 „Noi strivim. Tu mănânci." · S2 „Cum se face un smash" cu „Bila pe plită." / „Strivită, până face crustă." / „Brânza, cât e fierbinte." · „Ce are?" · CTA „Comandă acum" (T4 aprobat; nu doar „Comandă") · sheet „Unde comanzi?" / „Pe aplicația pe care o ai deja." · final „Comandă pe aplicația pe care o ai deja." · dock „Ți-e foame?" · local „Vino pe Jiului 5" / „Mănânci la noi sau comanzi acasă." · footer „Imagini concept generate, se înlocuiesc cu foto SNAQ."
Nu apar: oferta 3+1, program, timp de livrare, „gratuit", telefon, „deschis acum", „până pe {dată}".

## De confirmat cu SNAQ
- Oferta Glovo (-20% la unele articole, -25% cu Prime), data de final, dacă se aplică la cele 3 produse (sursa: pagina Glovo, 25.11.2026).
- Prețurile: Glovo (redus/întreg) vs Wolt din meniu (Double Bacon 52 Wolt = 52,00 întreg Glovo; Italian Beef Roll 60 Wolt vs 65,00 Glovo).
- Linkul Glovo (domeniul kaspi.glovoapp.com e cel primit de la director, de verificat că se deschide), linkurile Wolt și Bolt.
- Adresa Strada Jiului 5 (Wolt zice „virtual venue"), „Mănânci la noi", programul, telefonul (+40 784 584 119, doar în fișă, nu pe pagină).
- Ingredientele pe produs (copiate de pe Wolt); straturile din imaginile concept arată 2 felii de cheddar la Double El Chapo, Wolt zice „cheddar".
- Acordul pentru cadrele din filmări (press, assemble, local).

## Contrast WCAG (calculat)
Crem #F8F3E8 pe #0D0B09 17,75:1 · galben pe fond 10,49:1 · negru pe galben 10,49:1 (CTA, badge, tag) · gri #B9B0A2 pe fond 9,16:1, pe card 8,62:1 · lila #9D8CE0 pe fond 6,79:1 (doar numere/indici, sub 5% din ecran) · negru pe crem 17,75:1 (butoane platforme, „Ce are?" apăsat). Alb pe galben nu se folosește. Cuvântul SMASH e decorativ (contur galben ~60%, `aria-hidden`), exceptat. Ținte tactile ≥44px verificate automat (0 excepții). Focus: contur galben 3px + inel negru 3px.

## Teste rulate (Playwright, Chromium)
`tools/shots.py` (360×640, 390×844, 1440×900: 0 pageerror, 0 console error, fără overflow orizontal, sheet, explodare) și `tools/behavior.py` (swipe cu prag 40px, ←/→, wrap, trap focus, backdrop, burger, tab-uri meniu, dock, ținte 44px, reduced-motion, fallback imagine): toate OK.
