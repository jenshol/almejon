# Almejón — veneilykeliohjain

Mobiilioptimoitu, yhden tiedoston dashboard Almejónin veneilykelien tarkistamiseen kahdelle Suomenlahden alueelle: **avomeri** (lähellä Kalbådagrundia) ja **rannikko** (Suomenlinna).

Sivu näyttää:

- Nykyhetken aallonkorkeuden ja -jakson **oikeasta poijuhavainnosta** (Aaltopoiju.fi), + 3h historia
- Ennusteen (Open-Meteo Marine + Forecast API) aallonkorkeudelle, -jaksolle, tuulelle ja merivedenkorkeudelle
- Selkeän mukava/epämukava/vaarallista-luokituksen väreillä (vihreä/keltainen/punainen), joka ottaa huomioon Almejónin vesilinjan pituuden (7,3 m, kajuuttavene)
- Tuulen nopeuden ja suunnan samoissa laatikoissa aaltotietojen kanssa (nyt-tilanne + jokaisessa tuntiennustelaatikossa pieni tuuli-ikoni)
- Seuraavat tunnit tuntikohtaisina "chippeinä"
- Seuraavat vuorokaudet Aamu/Päivä/Ilta-lohkoina (ei yötä)

## Käyttöönotto GitHubissa

1. **Työnnä tämä hakemisto** `jenshol/almejon`-repositoryyn (juureen, ei alikansioon).
2. **Ota GitHub Pages käyttöön**: Settings → Pages → Source: "Deploy from a branch" → valitse `main` (tai oma oletushaarasi) ja `/ (root)`. Muutaman minuutin päästä sivu on osoitteessa `https://jenshol.github.io/almejon/`.
3. **Actions on jo valmiiksi konfiguroitu**: `.github/workflows/update-buoy.yml` hakee poijudataa 30 min välein ja committaa sen `data/buoy.json`-tiedostoon. Se tarvitsee kirjoitusoikeuden, joka on jo asetettu workflow-tiedostossa (`permissions: contents: write`) — mutta tarkista silti Settings → Actions → General → Workflow permissions, että "Read and write permissions" on valittuna organisaatio-/repotasolla, muuten ensimmäinen push epäonnistuu.
4. Voit myös käynnistää haun heti manuaalisesti: Actions-välilehti → "Päivitä aaltopoijudata" → "Run workflow".
5. `data/buoy.json` on jo esitäytetty oikealla, 31.8.2026 aamupäivällä haetulla datalla, joten sivu toimii heti ilman ensimmäistä Action-ajoakin — data vain päivittyy vanhaksi kunnes ensimmäinen ajo onnistuu.

## Mitä voi säätää

Kaikki säädöt ovat `index.html`:n `<script>`-osiossa:

- `BOAT_LWL_M` — Almejónin vesilinjan pituus (nyt 7,3 m). Vaikuttaa `classify()`-funktion kynnysarvoihin.
- `classify(heightM, periodS, windMs)` — mukava/epämukava/vaarallista-logiikka, oma heuristiikka kajuuttaveneelle. Selitys "pähkinänkuoressa" on myös suoraan sivulla avattavassa "Miten arvio lasketaan?" -osiossa.
- `LOCATIONS` — koordinaatit ja nimet kahdelle alueelle.
- Poijujen URL:t ja asematarkistukset ovat `scripts/fetch_buoy.py`:ssä (`STATIONS`-sanakirja).

## Tietolähteet

- **Aaltopoiju.fi** — oikea, poijuista mitattu aallonkorkeus/-jakso/-suunta ja merivesilämpötila (havainto, ei ennuste). Kolmannen osapuolen sivusto — jos sen HTML-rakenne muuttuu, `scripts/fetch_buoy.py` alkaa raportoida virhettä (ei koskaan hiljaa väärää dataa).
- **Open-Meteo Marine Weather API** — avoin, ilmainen ennuste aallonkorkeudelle, -jaksolle, -suunnalle, merenpinnan korkeudelle.
- **Open-Meteo Forecast API** — tuulen nopeus, suunta ja puuska-ennuste.

## Tunnetut rajoitukset / avoimet kohdat

- "Suomenlahti (avomeri)" -poijun tarkkaa WGS84-koordinaattia ei ole julkisesti dokumentoitu aaltopoiju.fi:llä — käytetty sijainti (59.973, 25.602, Kalbådagrundin lähellä) on paras arvio ja vaikuttaa vain siihen, miltä pisteeltä Open-Meteo-ennuste haetaan, ei poijuhavaintoon itseensä.
- Itämerellä ei ole merkittävää vuorovesivaihtelua — merivedenkorkeus-osio linkittää Ilmatieteen laitoksen sivulle, koska paikallinen sääolosuhteiden (ilmanpaine, tuuli) aiheuttama vaihtelu voi silti olla merkittävää.
