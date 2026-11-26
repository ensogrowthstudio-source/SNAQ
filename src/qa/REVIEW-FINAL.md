# REVIEW FINAL, SNAQ demo v5

Capturi: `qa/shots-final/` (46 fisiere + `_contact_*.png`), verificate pe 360x640, 390x844, 440x956 (touch, DPR 2) si 1440x900. Masuratori: `qa/final_checks.json`.

## Cerintele clientului
| Cerinta | Ce am facut |
|---|---|
| Hero-ul nu se explica | Bara: logo + „SNAQ" + hamburger. Sub ea: „Promoțiile de acum · -20% pe Glovo" (Archivo 600/700), H1 „Smash burgers din București" (Anton, mic-mediu), selector de produse cu miniaturi, burger, badge + nume + pret, „Comandă acum", „Livrare prin Glovo, Wolt sau Bolt". Incape complet pe 360x640 (burgerul se micsoreaza, nu se scoate nimic). |
| Meniu burger „rau tare" | Panou refacut: logo + SNAQ + X, card „Promoțiile de acum" (3 miniaturi, duce la hero si inchide), 4 linkuri Anton ~30px cu sageata (rand 78-112px, diacritice libere), Glovo/Wolt/Bolt ca butoane, Instagram + adresa. Fara numere 01-05. Verticala distribuita (la 440x956 ramane un gol de ~125px intre linkuri si butoane, ancorat jos intentionat). |
| Selectoare lipite de margine | `.mtabs`: `padding-inline` si `scroll-padding-inline` = marginea continutului. Cauza: `scroll-snap-align:start` fara scroll-padding lipea primul chip de ecran. Masurat: primul chip si titlul la acelasi x (18/20/22/130 px). Fade pe dreapta cat timp mai sunt chip-uri. |
| Review UI | Lista de mai jos. |

## Constatari si rezolvari
1. Bara de sus semitransparenta (.94): „Cadre din filmarile SNAQ." se vedea prin ea. Cauza: `rgba(...,.94)` + aparea doar dupa 24px scroll. Acum fundal solid #0D0B09 mereu (masurat: rgb(13,11,9)); borderul apare la scroll.
2. Hero fara context (vezi mai sus). Etichetele din chips: sentence case, 2 randuri, tinta 91-118px inaltime.
3. „LEI" majuscul langa „52,00 lei": `small` mostenea uppercase din type.css. Acum „41,80 lei" / „52,00 lei" consecvent, pret vechi 14px mute, taiat subtire.
4. Badge „-20% pe Glovo" in Anton mic: acum Archivo 700 13px. Tag-ul din meniu la fel.
5. Butonul de pauza plutea peste textul de jos: mutat in coltul de sus-dreapta al imaginii, aliniat la marginea continutului, vizual 30px + zona de atingere 44px.
6. Indicator 1 / 3 + sageti ‹ › in randul badge-ului (ținte 44px); sagetile vechi doar de desktop scoase. Swipe si ←/→ pastrate. Nudge o singura data dupa intro (burgerul 12px stanga si revine), oprit la orice atingere/tasta/scroll, nu in reduced-motion.
7. Titluri cu diacritice taiate: `.step__t` line-height 1 -> 1.15, `.h2` .95 -> 1.08, dock „Ți-e foame?" 1 -> 1.3, panou/H1 1.25-1.3.
8. Ritm vertical: sectiunile Meniu si Comanda aveau `padding-top:24px` inline (goluri de 96 vs 144px intre sectiuni). Scos, toate la 72px mobil / 120px desktop.
9. Redundanta „TOT MENIUL" + „MENIUL": eticheta e acum „Prețuri de pe Wolt"; nota scurtata la 2 randuri, 12px.
10. Desktop, meniu: lista pe 2 coloane cu grid intindea rand „Chicken Smash" langa randul inalt Double Bacon. Trecut pe `columns:2` + `break-inside:avoid`.
11. Desktop hero: blocul de text era lipit de jos cu 250px gol deasupra; centrat vertical in stage.
12. Buton secundar „Deschide în Maps" si „Ce are?" arata dezactivate (border .55): border .85 + fundal usor.
13. Subsol: link Instagram subliniat inconsecvent, acum bold cu underline-offset; padding-bottom pentru dock pastrat (112px mobil), dock ascuns pe sectiunea Comanda.
14. Focus: `:focus-visible` doar (inelul nu apare la click; la deschiderea panoului focusul merge pe X, revine pe burger la inchidere).
15. CLS 0.028 aparut cu H1 nou (fallback font impacheta pe 2 randuri): `white-space:nowrap` pe H1/eticheta -> CLS 0.
16. LCP 2.56 s dupa miniaturi (3 cereri 26 KB concurau cu hero): miniaturi 112px q68 (4.6-5.6 KB) + `fetchpriority=low` -> 2.25 s.
17. `--info-h` calibrat dupa masuratori (info 118/126, 188/194, 192/194 px, 360/390/440).
18. Tinte tactile: nicio tinta vizibila < 44px pe niciun viewport (verificat cu boundingBox).

## De confirmat / compromisuri
- Eticheta: am scris „Promoțiile de acum" in loc de „săptămânii": „săptămânii" promite rotatie saptamanala, neconfirmata (Glovo nu arata data de final). Se schimba usor daca SNAQ confirma.
- „-25% cu Glovo Prime" apare in hero doar pe ecrane >= 760px inaltime si desktop (pe 360x640 nu incape fara sa micsoreze burgerul).
- Archivo 600: fontul are doar 400/700, deci 600 se randeaza cu 700.
- Miniaturile sunt crop din hero_cut (concept AI).
