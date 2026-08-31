# Almejón — veneilykeliohjain

Mobiilioptimoitu, yhden tiedoston dashboard Almejónin veneilykelien tarkistamiseen kahdelle Suomenlahden alueelle: **rannikko** (Suomenlinna, näytetään ensin) ja **avomeri** (lähellä Kalbådagrundia).

Sivu näyttää:

- Nykyhetken aallonkorkeuden ja -jaksonpituuden **oikeasta poijuhavainnosta** (Aaltopoiju.fi), suuntanuolella + 4h historia (5 havaintoikkunaa)
- Ennusteen (Open-Meteo Marine + Forecast API) aallonkorkeudelle, -jaksolle, tuulelle ja merivedenkorkeudelle
- Selkeän hyvä/välttävä/huono-luokituksen väreillä (vihreä/keltainen/punainen) ja jatkuvan mukavuusindeksin (näkyy värillisessä pallossa), jotka ottavat huomioon Almejónin mitat ja painon (LWL 7,3 m, LOA 8,37 m, leveys 2,83 m, n. 2500 kg, puoliliukuva runko)
- Vallitsevan hetken sään (ikoni + lämpötila, yhdestä pisteestä, Porkkala) suoraan kummankin alueen nyt-tilanteen laatikossa, poijuhavainnon vieressä
- Tuulen nopeuden ja suunnan samoissa laatikoissa aaltotietojen kanssa (nyt-tilanne + jokaisessa tuntiennustelaatikossa pieni tuuli-ikoni)
- Seuraavat tunnit tuntikohtaisina "chippeinä"
- Seuraavat 4 vuorokautta Yö/Aamu/Päivä/Ilta-lohkoina, joissa aallokon lisäksi näkyy myös kyseisen ajanjakson sää (ikoni + keskilämpötila, lohkon PAHIN säätila) — ei enää erillistä sääkorttia (huomisen Aamu näkyy tarkoituksella myös tuntiennusteessa, koska veneellä voi olla yöpymässä vesillä valoisana kesäyönä)

## Käyttöönotto GitHubissa

1. **Työnnä tämä hakemisto** `jenshol/almejon`-repositoryyn (juureen, ei alikansioon).
2. **Ota GitHub Pages käyttöön**: Settings → Pages → Source: "Deploy from a branch" → valitse `main` (tai oma oletushaarasi) ja `/ (root)`. Muutaman minuutin päästä sivu on osoitteessa `https://jenshol.github.io/almejon/`.
3. **Actions on jo valmiiksi konfiguroitu**: `.github/workflows/update-buoy.yml` hakee poijudataa 30 min välein ja committaa sen `data/buoy.json`-tiedostoon. Se tarvitsee kirjoitusoikeuden, joka on jo asetettu workflow-tiedostossa (`permissions: contents: write`) — mutta tarkista silti Settings → Actions → General → Workflow permissions, että "Read and write permissions" on valittuna organisaatio-/repotasolla, muuten ensimmäinen push epäonnistuu.
4. Voit myös käynnistää haun heti manuaalisesti: Actions-välilehti → "Päivitä aaltopoijudata" → "Run workflow".
5. `data/buoy.json` on jo esitäytetty oikealla, 31.8.2026 aamupäivällä haetulla datalla, joten sivu toimii heti ilman ensimmäistä Action-ajoakin — data vain päivittyy vanhaksi kunnes ensimmäinen ajo onnistuu.

## Mitä voi säätää

Kaikki säädöt ovat `index.html`:n `<script>`-osiossa:

- `BOAT_LWL_M`, `BOAT_LOA_M`, `BOAT_BEAM_M`, `BOAT_DISPLACEMENT_KG` — Almejónin (Scand 7800 Nautic) mitat ja paino veneen omasta teknisestä tiedosta. Vaikuttavat sekä Comfort Ratioon että `classify()`-funktion kynnysarvoihin.
- `classify(heightM, periodS, windMs)` — palauttaa jatkuvan mukavuusindeksin `{level, score, ...}` (ei portaittaisia pykälänostoja). Kolme osatekijää, kukin oma kaava suoraan ilman turvamarginaaleja, lopputulos on osatekijöiden huonoin (max):
  1. **Aallon jyrkkyys vs. Michen murtumisraja** (0,14 = ~1/7) — aallonpituus L=1,56×jakso² (deep-water-dispersio), jyrkkyys=korkeus/L. Korvaa vanhat kiinteät jakson kynnysarvot jatkuvalla, fysikaalisella suureella.
  2. **Korkeus/LWL-suhde, skaalattu Ted Brewerin Comfort Ratiolla** (CR ≈ 17,4 Almejónille — CR yhdistää painon, LWL:n ja LOA:n sekä leveyden^1,333:n). Koska CR on kehitetty purjeveneille eikä sellaisenaan sovi leveään puoliliukuvaan runkoon, sitä käytetään vain kertoimena (CR÷25) yleisohjeen 6 %:n korkeus/LWL-rajalle.
  3. **Tuuli** (12 m/s → indeksi 1,0, 17 m/s → indeksi 2,0, lineaarinen).

  Indeksi < 1,0 = Hyvä, 1,0–2,0 = Välttävä, > 2,0 = Huono. Täysi kaava, laskuesimerkit ja Comfort Ratio -perustelut ovat sivulla avattavassa "Miten hyvä/välttävä/huono-indeksi lasketaan?" -osiossa.
  Pallon väri liukuu portaattomasti vihreästä keltaiseen koko Hyvä+Välttävä-alueella (indeksi 0–2,0, `greenYellowBlend()`), jotta esim. 1,1 erottuu selvästi 1,8:sta vaikka molemmat ovat teksti-luokaltaan "Välttävä" — Välttävä→Huono-raja (2,0) sen sijaan on tarkoituksella terävä, ei liukua.
- `LOCATIONS` — koordinaatit ja nimet kahdelle alueelle. Näyttöjärjestys (rannikko ennen avomerta) määräytyy `loadAll()`-funktion `renderLocationCard(...)`-kutsujen järjestyksestä, ei `LOCATIONS`-objektista.
- Poijujen URL:t ja asematarkistukset ovat `scripts/fetch_buoy.py`:ssä (`STATIONS`-sanakirja).
- `WEATHER_LOCATION` — sään hakupiste (oletus: Porkkala). Yksi piste riittää, koska ilman lämpötila/pilvisyys ei juuri eroa Avomeren ja Rannikon välillä.
- `WEATHER_CODES` / `weatherSeverityRank()` — WMO-säätilakoodien (Open-Meteon `weather_code`) käännökset suomeksi + ikoni, ja niiden karkea vakavuusjärjestys. Kun useampi tunti yhdistetään yhdeksi Yö/Aamu/Päivä/Ilta-lohkoksi, näytetään lohkon PAHIN sää (sama periaate kuin aallokko-luokittelussa) ja lämpötilan keskiarvo. `currentWeather()` poimii vallitsevan hetken säätilan (lähin tuleva/nykyinen tunti) nyt-tilanteen laatikkoon.
- "↻ Päivitä nyt" -nappi ei vain piirrä samaa dataa uudelleen: se hakee poijudatan uudelleen (`data/buoy.json`, cache-buster-parametrilla) ja tekee Open-Meteo-ennusteista uudet HTTP-pyynnöt (`&_=Date.now()`-parametri estää selaimen välimuistin) — eli tarkistaa aidosti onko ennuste päivittynyt. Sama tapahtuu automaattisesti 10 min välein.

## Tietolähteet

- **Aaltopoiju.fi** — oikea, poijuista mitattu aallonkorkeus/-jakso/-suunta ja merivesilämpötila (havainto, ei ennuste). Kolmannen osapuolen sivusto — jos sen HTML-rakenne muuttuu, `scripts/fetch_buoy.py` alkaa raportoida virhettä (ei koskaan hiljaa väärää dataa).
- **Open-Meteo Marine Weather API** — avoin, ilmainen ennuste aallonkorkeudelle, -jaksolle, -suunnalle, merenpinnan korkeudelle.
- **Open-Meteo Forecast API** — tuulen nopeus, suunta ja puuska-ennuste.
- **Ted Brewer Comfort Ratio** — veneenrakennuksen tunnusluku (ks. esim. keelindex.com/formulas/comfort-ratio), käytetty `classify()`-funktion korkeusrajan kertoimena.
- **Michen kriteeri (Miche, 1944)** — syvän veden aallon murtumisen jyrkkyysraja (~1/7), käytetty jakson vaikutuksen laskennassa jyrkkyytenä kiinteiden kynnysarvojen sijaan.

## Tunnetut rajoitukset / avoimet kohdat

- "Suomenlahti (avomeri)" -poijun tarkkaa WGS84-koordinaattia ei ole julkisesti dokumentoitu aaltopoiju.fi:llä — käytetty sijainti (59.973, 25.602, Kalbådagrundin lähellä) on paras arvio ja vaikuttaa vain siihen, miltä pisteeltä Open-Meteo-ennuste haetaan, ei poijuhavaintoon itseensä.
- Itämerellä ei ole merkittävää vuorovesivaihtelua — merivedenkorkeus-osio linkittää Ilmatieteen laitoksen sivulle, koska paikallinen sääolosuhteiden (ilmanpaine, tuuli) aiheuttama vaihtelu voi silti olla merkittävää.
- **GitHub Actionsin `schedule`-ajastus on epäluotettava**: `update-buoy.yml` on ajastettu 30 min välein, mutta havaittu käytännössä, että ajastettu ajo ei ole käynnistynyt kertaakaan itsestään usean tunnin aikana (vain manuaaliset "Run workflow" -ajot ovat toimineet). Tämä on GitHubin dokumentoitu, tunnettu rajoitus matalan aktiviteetin repoissa - ajastus on "best effort" eikä sillä ole SLA:ta. Katso alta "Ajastuksen luotettava korjaus".
- Selaimessa suoraan (ilman GitHub Actionsia) tehty poijuhaku ei toimi: aaltopoiju.fi ei salli CORS-pyyntöjä selaimesta, ja testatuista ilmaisista julkisista CORS-proxyista (allorigins.win, thingproxy, codetabs) yksikään ei vastannut luotettavasti, ja corsproxy.io vaatii nykyään oman API-avaimen. Siksi datan haku on pakko tehdä palvelinpuolella (GitHub Actions) eikä suoraan sivulta.

## Ajastuksen luotettava korjaus (suositeltu, ~5 min, vaatii oman GitHub-tokenin)

GitHub Actionsin oma `schedule`-ajastin ei siis käynnisty luotettavasti itsekseen matalan aktiviteetin repoissa. Luotettavin korjaus on ulkopuolinen, ilmainen ajastuspalvelu, joka kutsuu GitHubin API:a ja pakottaa `update-buoy.yml`-workflown käyntiin sovitulla välillä. Tätä ei voi tehdä automaattisesti puolestasi, koska se vaatii henkilökohtaisen GitHub-tokenin liittämisen kolmannen osapuolen palveluun — token pitää aina syöttää itse suoraan kyseisen palvelun omaan käyttöliittymään.

1. **Luo GitHub-token**: [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new) ("Fine-grained personal access token").
   - Resource owner: `jenshol`
   - Repository access: "Only select repositories" → `almejon`
   - Permissions → Repository permissions → **Actions: Read and write**
   - Expiration: esim. 1 vuosi
   - "Generate token" → kopioi arvo talteen (näytetään vain kerran).
2. **Luo ilmainen tili** osoitteessa [cron-job.org](https://cron-job.org) (ei vaadi luottokorttia).
3. **Luo uusi cronjob** seuraavilla asetuksilla:
   - Title: `Almejon buoy refresh`
   - URL: `https://api.github.com/repos/jenshol/almejon/actions/workflows/update-buoy.yml/dispatches`
   - Execution schedule: esim. joka 15. minuutti
   - Request method: `POST`
   - Headers (Advanced-välilehdeltä):
     - `Accept: application/vnd.github+json`
     - `Authorization: Bearer <LIITÄ_TOKEN_TÄHÄN>`
     - `X-GitHub-Api-Version: 2022-11-28`
     - `Content-Type: application/json`
   - Request body: `{"ref":"main"}`
4. Tallenna ja testaa heti "Run now" -painikkeella, tarkista sitten [Actions-välilehdeltä](https://github.com/jenshol/almejon/actions/workflows/update-buoy.yml), että uusi ajo käynnistyi ja onnistui.

Jos "Fine-grained token" tuntuu monimutkaiselta, kelpaa myös perinteinen "classic" token (Settings → Developer settings → Personal access tokens → Tokens (classic)) `public_repo`-oikeudella, koska repositorio on julkinen.
