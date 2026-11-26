# SNAQ — site demo (Enso Studio)

Propunere de homepage pentru SNAQ (smashed burgers, București). Nesemnat; publică doar Eduard.

- `dist/` — site-ul gata de servit (Netlify publică acest folder, fără build; vezi `netlify.toml`).
- `src/` — sursa: brief, UX (`ux/`), motion GSAP (`motion/`), scriptul de build (`build/`), raportul QA (`qa/`).

Imagini concept generate, se înlocuiesc cu foto SNAQ.
De confirmat cu SNAQ: durata ofertelor Glovo, linkurile Wolt și Bolt, prețurile pe platforme, ingredientele pe produs, adresa și programul.

Refacere: `cd src/motion && npm i gsap@3` apoi `python3 src/build/build_v5.py` (căile din script pornesc de la `/home/claude/snaq_v5/`; schimbă `ROOT` dacă rulezi altundeva).
