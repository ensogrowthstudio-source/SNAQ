# ALB — varianta pe alb a homepage-ului SNAQ v5

Livrabil: `build/dist/alb/index.html` (296 KB, imaginile din `../img/`, fără video). Se construiește din ACELAȘI `build/build_v5.py` (o singură rulare produce ambele pagini): pagina pe închis e construită întâi, apoi `build_light()` îi aplică tema (`build/snippets/light.css`), scoate video-ul, rescrie căile `img/` → `../img/`, schimbă `theme-color` și linkul din footer. Aceleași texte, același JS (motion.js, glue.js, scriptul de stare), același DOM.

Link de prezentare în footer: pe închis „Vezi varianta pe alb" → `alb/index.html`; pe alb „Vezi varianta pe închis" → `../index.html`. Am pus `index.html` explicit (nu `alb/` / `../` goale) ca să meargă și din `file://`, unde un director se deschide ca listă de fișiere.

## Decizii de design
| Zonă | Decizie | De ce |
|---|---|---|
| Fundal | `#FBF8F2` alb cald; suprafețe `#F2ECE1` (secțiunea „Cum facem", „Localul", card în meniu); panou/sheet `#FFFDF9` | nu clinic, hârtie de burger; alternanța dă ritm fără linii grele |
| Text | `#15110C` (17,7:1); secundar `#5E5548` (6,9:1 pe fundal, 6,2:1 pe suprafață) | peste 4,5:1 chiar și la 12px |
| Galben `#F8B018` | doar suprafață: banda de sus, badge, CTA, tag „-20%", marker sub preț, blocul Comandă, SMASH. Niciodată text. Pe galben: text `#15110C` (10:1) | galbenul ca text pe alb are 1,9:1 |
| Banda din hero | eticheta „Promoțiile de acum · -20% pe Glovo" devine bandă galbenă full-bleed sub bara de sus, cu linie neagră jos | e „blocul mare galben" din hero; păstrează textul, nu adaugă înălțime semnificativă (hero încape pe 360x640) |
| Preț | negru, cu marker galben (gradient 66-94% din înălțime) | prețul rămâne cel mai greu element din info, identitatea de brand fără text galben |
| Comandă | secțiune plină galbenă (border negru sus), butoane de platformă negre cu text crem | ancora vizuală a paginii; contrast 17,7:1 pe butoane |
| Lila | `#5B4BB5` (6,35:1 pe fundal, 5,7:1 pe suprafață), doar pe eyebrow-uri și numărul din etichete | varianta `#9D8CE0` pică ca text |
| Bara de sus / panou navigare | fundal alb solid, linie fină `rgba(21,17,12,.16)` mereu, ținte ≥44px neschimbate | cerința; fără transparență (la fel ca pe închis) |
| Sheet comandă | alb `#FFFDF9`, platforme clare (fundal alb cald + contur negru 2px, activ galben), scrim negru 50% | cerința; platformele din panoul de navigare rămân negre (rând de 3 butoane mici) |
| Chip-uri | activ = negru cu text crem (hero, meniu); inactiv = alb cu contur `#8A8072` (3,66:1, UI ≥3:1) | selecția se vede dintr-o privire |
| Focus | contur negru 3px + inel galben 3px lipit de element | vizibil pe alb, pe galben și pe negru |
| Umbră de contact | pseudo-element `.prod__visual::before` cu `radial-gradient` (elipsă, 34% negru → 0), sub burger; dispare la „Ce are?" | burgerul nu mai plutește; fără `filter`; se mișcă cu intro-ul, idle-ul rămâne pe imagine |
| Etichete „Ce are?" | fir negru 1px + punct galben cu inel negru (firul galben dispărea pe alb); text negru cu halou crem | citibile peste SMASH estompat |
| SMASH la „Ce are?" | opacitate .16 (pe închis .1) | pe alb galbenul plin are nevoie de puțin mai mult ca să nu pară gol |
| Numerele 01/02/03 din „Cum facem" | negru cu umbră galbenă dură 3px | conturul galben subțire dispărea; negrul trece contrastul |
| Video | scos complet (0 `<video>`, 0 buton pauză) | au fundal închis copt |
| Tipografie | Anton + Archivo, aceleași mărimi; doar `letter-spacing:.012em` pe numele produsului (Anton negru pe alb arată mai greu) | Ș, Ț, Ă verificate în capturi: „BUCUREȘTI", „Castraveți", „Strivită", „ȚI-E FOAME?" corecte |
| `theme-color` | `#FBF8F2`, plus `color-scheme: light` | bara browserului se topește în pagină |

## SMASH: variante testate (390x844, `qa/shots-alb/_smash_variante_a_b_c.png`)
- **A, galben plin, fără contur.** Puternică, curată, dar litera galbenă pe `#FBF8F2` are doar 1,9:1: forma se pierde la margini (S și H se topesc în fundal pe ecrane luminoase).
- **B, contur negru subțire, fără umplere.** Clară, dar goală: concurează cu burgerul (liniile trec prin chiflă) și dă zgomot deasupra titlului. Cea mai slabă.
- **C, galben plin + contur negru** (aleasă; conturul final e 3px cu `paint-order: stroke fill`, adică ~1,5px vizibil în afara literei). Are masa lui A și marginea definită din B, burgerul se suprapune curat peste ea, se leagă cu banda galbenă și cu butoanele conturate în negru. Pe 360x640 forma se citește fără efort.
Rămâne comutabil: `html[data-smash="a|b|c"]` în `light.css` (default = C).

## Imagini
- Decupajele (`hero_cut`, straturile) sunt curate pe alb: am verificat la 200% marginile pe `#FBF8F2` (crop din `hero_cut` și din captura „Ce are?" la DPR 2): fără halou închis. Doar ~0,9% din pixelii cu alfa > 5 sunt semitransparenți și au culoarea burgerului. **Nu am creat variante defringed**, deci `dist/alb/` nu are imagini proprii; totul vine din `../img/`.
- Miniaturile din chip-uri: fundal radial alb→bej în loc de cel maro închis.

## Contrast (`qa/contrast_alb.json`, `qa/tools/contrast_alb.py`)
Crawl automat în browser pe 390x844 și 1440x900, în stările: hero, „Ce are?", Cum/Meniu/Local/Comandă, footer, sheet, panou navigare. 677 noduri text (deduplicate pe clasă+culori), calculat din culoarea efectivă a textului și fundalul efectiv (alfa compus). **0 sub prag** (4,5:1 text normal, 3:1 text mare ≥24px sau ≥18,66px bold). Excepție conștientă: cuvântul SMASH din fundal (`aria-hidden`, decor, fără informație).

Perechi distincte, de la cea mai mică la cea mai mare:

| Text | Fundal | Raport | Prag | Exemplu |
|---|---|---|---|---|
| #5B4BB5 | #F2ECE1 | 5.73 | 4.5 | `.eyebrow` „Noi strivim. Tu mănânci.” |
| #5E5548 | #F2ECE1 | 6.23 | 4.5 | `.fine` „Cadre din filmările SNAQ.” |
| #5B4BB5 | #FBF8F2 | 6.35 | 4.5 | `.eyebrow` „Prețuri de pe Wolt” |
| #5E5548 | #FBF8F2 | 6.91 | 4.5 | `.pg__n` „/ 3” |
| #5E5548 | #FFFDF9 | 7.2 | 4.5 | `p` „Pe aplicația pe care o ai de” |
| #15110C | #F8B018 | 10.04 | 4.5 | `.skip` „Sari la conținut” |
| #15110C | #F8B018 | 10.04 | 3 | `.h2` „Comandă” |
| #15110C | #F2ECE1 | 15.98 | 3 | `.h2` „Cum se face un smash” |
| #15110C | #F2ECE1 | 15.98 | 4.5 | `.local__big` „Mănânci la noi sau comanzi a” |
| #15110C | #FBF8F2 | 17.73 | 3 | `.top__word` „SNAQ” |
| #FBF8F2 | #15110C | 17.73 | 4.5 | `.w` „Double” |
| #15110C | #FBF8F2 | 17.73 | 4.5 | `b` „1” |
| #FBF8F2 | #15110C | 17.73 | 3 | `span` „Glovo” |
| #15110C | #FFFDF9 | 18.5 | 4.5 | `.w` „Double” |
| #15110C | #FFFDF9 | 18.5 | 3 | `h2` „Unde comanzi?” |

UI (calculat manual): contur chip-uri/butoane secundare `#8A8072` pe `#FBF8F2` = 3,66:1 (≥3:1); inel de focus negru pe alb 17,7:1; inel galben lipit de element nu e singurul indicator (conturul negru exterior duce contrastul).

## Cifre
- Lighthouse mobil (Moto G Power, 4G simulat, CPU 4x, performanță, 6 rulări pe `/alb/index.html`): **LCP mediană 2,25 s** (2,25 / 2,64 / 2,25 / 2,18 / 2,26 / 2,19), **CLS 0** în toate, TBT mediană 235 ms (113-530), scor mediană 0,93 (0,85-0,97). FCP 1,27 s. Elementul LCP: imaginea hero (`fetchpriority=high`, întârziere de randare ~1,6 s, adică JS-ul de intro sub CPU 4x). **O rulare din șase (2,64 s) a depășit 2,5 s**; restul 2,18-2,26 s. Pagina pe închis, măsurată acum în aceleași condiții (3 rulări): LCP 2,26 / 2,26 / 2,40 s; deci mediul e azi ceva mai lent decât la măsurătorile din RAPORT.md (2,1 s), nu pagina albă.
- Greutate transferată în Lighthouse: 656 KB (închis, aceeași măsurătoare: 926 KB; diferența vine probabil din video-uri, neverificat separat). Prima zonă: HTML 116 KB gzip + hero AVIF 93 KB.
- Erori: pageerror / console error / requestfailed / HTTP >= 400 = **0** pe ambele pagini, pe toate cele 4 viewport-uri (`qa/shots-alb/_errors.json` are rularea albă; închis: `[]` pe toate). `file://`: ambele pagini, 0 erori, 0 imagini rupte, 8/8 etichete „Ce are?" vizibile, linkurile între variante duc la `file:///.../index.html` și `.../alb/index.html`.
- Reduced-motion (alb, 390x844): 8/8 etichete apar direct, hero rămâne opacity 1 după închiderea „Ce are?", sageata următor merge (produs 2), 0 erori.
- Pagina pe închis: diferența față de build-ul aprobat (verificat cu diff pe linii) = exact 2 adăugiri: linkul „Vezi varianta pe alb" în footer și o regulă CSS pentru el. Capturile și comportamentul rămân cele aprobate; 0 erori.

## Capturi
`qa/shots-alb/`: `alb_*` și `inchis_*` pe 360x640, 390x844, 440x956, 1440x900: hero, swipe p1/p2, „Ce are?" pe fiecare din cele 3 produse, panou navigare (mobil), sheet comandă, Cum/Meniu/Local/Comandă, footer; reduced-motion și `file://` pe 390. Foi de contact: `_contact_alb_all.png`, `_contact_alb_390.png`, `_contact_inchis_390.png`. Scripturi: `qa/tools/shots_alb.py`, `contrast_alb.py`, `misc_alb.py`.

## Probleme găsite pe drum
1. **Etichete „Ce are?" peste tab-uri la 360x640 (Double El Chapo, Italian Beef Roll).** Există și pe pagina pe închis (stiva de 9 etichete, unele pe 2 rânduri, se de-coliziona în sus peste tab-uri; pe închis tab-urile inactive sunt semitransparente deci nu se vede crud, dar „Chiflă cu unt" se suprapune cu chip-ul „Italian Beef Roll" în `inchis_360x640_03_cearare_p1.png`). Pe alb tab-urile sunt opace și ar fi tăiat etichetele. Rezolvat **doar pe alb**, în CSS: sub 720px înălțime etichetele au 11px și fără numărul lila, deci o singură linie. **Pe închis nu am umblat** (cerința: nu o strica); fixul e de făcut separat, în motion.js `placeLabels` sau cu aceeași regulă CSS.
2. Numerele „01/02/03": galben cu contur negru pica 1,59:1 la crawl, schimbat în negru cu umbră galbenă.

## Ce rămâne
- Fără verificare pe telefon real (Safari iOS): `:has()` (SMASH estompat la „Ce are?") și AVIF sub iOS 16.4, ca la pagina pe închis.
- Marginile imaginilor sunt curate la 200% pe `#FBF8F2`; dacă SNAQ schimbă fundalul în alb pur sau altă nuanță, se reverifică.
- Linkul din footer către cealaltă variantă e pentru prezentare: se scoate la livrarea finală (o linie în `build_v5.py`: `FOOT_END` și `foot__alt`).
- Imaginile rămân concept AI (nota din footer păstrată).
- Prețuri, ofertă, linkuri Wolt/Bolt: neschimbate (neconfirmate cu SNAQ).
