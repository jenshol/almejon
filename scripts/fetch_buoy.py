#!/usr/bin/env python3
"""
Hakee Aaltopoiju.fi:n HAVAINTO-datan (oikeasti mitattu, ei ennuste) kahdelle
poijulle: Suomenlahti (avomeri) ja Suomenlinna (rannikko). Kirjoittaa tuloksen
tiedostoon data/buoy.json, jota index.html lukee samasta originesta (ei CORS-
ongelmaa, koska GitHub Pages tarjoilee sekä sivun että JSON:in).

Ajetaan GitHub Actionilla (.github/workflows/update-buoy.yml) esim. 30 min
välein. Jos haku tai jäsennys epäonnistuu jommallekummalle poijulle, aiempi
tieto SÄILYTETÄÄN sille poijulle ja status merkitään "error" — sivu ei siis
koskaan näytä väärää lukemaa hiljaisesti, ja git-historia paljastaa milloin
haku alkoi/lakkasi toimimasta.

HUOM: aaltopoiju.fi on kolmannen osapuolen sivusto eikä virallinen rajapinta.
Jos sivun rakenne muuttuu, tämä jäsennin pitää päivittää — STATION_NAME_CHECK
laukaisee tällöin virheen sen sijaan, että kirjoittaisi hiljaa väärää dataa.
"""
import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

HELSINKI = timezone(timedelta(hours=3))  # EEST (kesäaika); ks. huomio alla
DATA_PATH = "data/buoy.json"

STATIONS = {
    "avomeri": {
        "label": "Suomenlahti (avomeri)",
        "url": "https://m.aaltopoiju.fi/data.php?v=hel&lng=fi",
        "name_check": "SUOMENLAHTI",
        # Kalbådagrundin majakan liepeillä, avoimen Suomenlahden poiju.
        # Tarkkaa poijun WGS84-sijaintia ei ole julkisesti dokumentoitu
        # aaltopoiju.fi:llä — tämä on paras arviomme, tarkista tarvittaessa.
        "lat": 59.973,
        "lon": 25.602,
    },
    "rannikko": {
        "label": "Suomenlinna (rannikko)",
        "url": "https://m.aaltopoiju.fi/data.php?v=suomenlinna&lng=fi",
        "name_check": "SUOMENLINNA",
        # Lähde: Ilmatieteen laitos / Merikarhut — 60°07.40'N, 024°58.35'E
        "lat": 60.1233,
        "lon": 24.9725,
    },
}

DAY_NAMES = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

TIMESTAMP_RE = re.compile(
    r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(\d{1,2})\s+(\d{2}):(\d{2})\b"
)
DIR_RE = re.compile(r"\b([NSEW]{1,3})\s+(\d{1,3})°")
HEIGHT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*m\b")
PERIOD_RE = re.compile(r"(\d+(?:\.\d+)?)\s*s\b")
TEMP_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*°C")


def fetch_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; AlmejonDashboardBot/1.0; "
                "+https://github.com/) almejon-weather-dashboard"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
    html = raw.decode("utf-8", errors="replace")
    # Kevyt tag-strippaus: korvaa tagit rivinvaihdolla, jotta peräkkäiset
    # arvot eivät sula yhteen, mutta emme ole riippuvaisia tarkasta DOM-
    # rakenteesta (joka voi vaihdella selaimen renderöinnin mukaan).
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"&deg;", "°", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def resolve_date(day_abbr: str, day_of_month: int, now_helsinki: datetime) -> datetime.date:
    """Etsii lähimmän päivämäärän +-4 päivän ikkunasta, jonka viikonpäivä
    JA kuukauden päivä täsmäävät. Näin kuukauden/vuoden vaihtuminen ei
    sekoita jäsennystä, kunhan Action ajetaan riittävän usein."""
    target_wd = DAY_NAMES[day_abbr]
    for delta in range(-4, 5):
        candidate = (now_helsinki + timedelta(days=delta)).date()
        if candidate.day == day_of_month and candidate.weekday() == target_wd:
            return candidate
    # Ei löytynyt järkevää täsmäystä - palautetaan paras arvaus (tämä päivä)
    return now_helsinki.date()


def parse_observations(text: str, now_helsinki: datetime):
    """Palauttaa listan havaintoja (HAVAINTO-osuus, ennen ENNUSTE-merkkiä),
    aikajärjestyksessä vanhimmasta uusimpaan, mukaan lukien erikoismerkitty
    'nykyhetki'-rivi."""
    ennuste_idx = text.find("ENNUSTE")
    scope = text if ennuste_idx == -1 else text[:ennuste_idx]

    matches = list(TIMESTAMP_RE.finditer(scope))
    observations = []
    for i, m in enumerate(matches):
        day_abbr, dom, hh, mm = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(scope)
        chunk = scope[start:end]

        dir_m = DIR_RE.search(chunk)
        height_m = HEIGHT_RE.search(chunk)
        period_m = PERIOD_RE.search(chunk)
        temp_m = TEMP_RE.search(chunk)
        if not (height_m and period_m):
            continue  # rivi ei sisällä odotettuja arvoja - ohitetaan

        date = resolve_date(day_abbr, dom, now_helsinki)
        iso_time = f"{date.isoformat()}T{hh}:{mm}:00+03:00"

        obs = {
            "time": iso_time,
            "height_m": float(height_m.group(1)),
            "period_s": float(period_m.group(1)),
        }
        if dir_m:
            obs["dir_compass"] = dir_m.group(1)
            obs["dir_deg"] = int(dir_m.group(2))
        if temp_m:
            sea_temp = float(temp_m.group(1))
            if sea_temp != 0.0:  # sivu palauttaa joskus 0.0°C virheellisenä placeholderina
                obs["sea_temp_c"] = sea_temp
        observations.append(obs)
    return observations


def load_existing():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"generated_at": None, "stations": {}}


def main():
    now_helsinki = datetime.now(HELSINKI)
    result = load_existing()
    result.setdefault("stations", {})
    any_ok = False

    for key, cfg in STATIONS.items():
        station_entry = result["stations"].get(key, {})
        try:
            text = fetch_text(cfg["url"])
            if cfg["name_check"] not in text.upper():
                raise ValueError(
                    f"Odotettu asemanimi '{cfg['name_check']}' ei löytynyt "
                    f"vastauksesta - sivu on voinut muuttua tai v-parametri "
                    f"osoittaa väärään poijuun."
                )
            observations = parse_observations(text, now_helsinki)
            if len(observations) < 2:
                raise ValueError(
                    f"Jäsennettiin vain {len(observations)} havaintoriviä - "
                    f"liian vähän, oletettavasti sivun rakenne on muuttunut."
                )
            # Säilytetään viimeiset 8 havaintoa (riittää "nyt + 3h taakse" -näyttöön
            # ja vähän marginaalia jos jokin Action-ajo välistä jää)
            station_entry = {
                "label": cfg["label"],
                "lat": cfg["lat"],
                "lon": cfg["lon"],
                "status": "ok",
                "fetched_at": now_helsinki.isoformat(),
                "observations": observations[-8:],
            }
            any_ok = True
            print(f"[OK] {key}: {len(observations)} havaintoa, viimeisin "
                  f"{observations[-1]['time']} {observations[-1]['height_m']}m")
        except (urllib.error.URLError, ValueError, TimeoutError) as exc:
            print(f"[VIRHE] {key}: {exc}", file=sys.stderr)
            station_entry = {
                **station_entry,
                "status": "error",
                "error": str(exc),
                "error_at": now_helsinki.isoformat(),
            }
        result["stations"][key] = station_entry

    if any_ok:
        result["generated_at"] = now_helsinki.isoformat()

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")

    if not any_ok:
        print("Molempien poijujen haku epäonnistui - lopetetaan virhekoodilla "
              "(vanha data.json säilyy sellaisenaan).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
