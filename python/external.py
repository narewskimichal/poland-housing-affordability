"""
Dane zewnętrzne w projekcie Poland Housing Affordability.

- stopa referencyjna NBP (Narodowy Bank Polski, archiwum XML)
- przeciętne miesięczne wynagrodzenie brutto w 15 miastach (GUS, API BDL)

Funkcje pobierające (fetch_*) są oddzielone od funkcji przetwarzających (parse_*),
dzięki czemu przetwarzanie można przetestować bez dostępu do internetu.
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

from clean import CITIES, normalize_key

HEADERS = {"User-Agent": "poland-housing-affordability (portfolio project)"}

NBP_RATES_URLS = [
    "https://static.nbp.pl/dane/stopy/stopy_procentowe_archiwum.xml",
    "https://www.nbp.pl/xml/stopy_procentowe_archiwum.xml",
]

BDL_API = "https://bdl.stat.gov.pl/api/v1"
BDL_WAGE_VARIABLE = 64428      # przeciętne miesięczne wynagrodzenie brutto - ogółem
BDL_POWIAT_LEVEL = 5           # wszystkie 15 miast to miasta na prawach powiatu


# ---------------------------------------------------------------------------
# Stopa referencyjna NBP
# ---------------------------------------------------------------------------

def fetch_nbp_rates_xml(save_to: Path | None = None) -> bytes:
    """Pobiera archiwum stóp procentowych NBP (próbuje kolejno znanych adresów)."""
    errors = []
    for url in NBP_RATES_URLS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            if save_to:
                Path(save_to).parent.mkdir(parents=True, exist_ok=True)
                Path(save_to).write_bytes(r.content)
            print(f"Downloaded {len(r.content):,} bytes from {url}")
            return r.content
        except requests.RequestException as e:
            errors.append(f"{url}: {e}")
    raise ConnectionError("Could not download NBP rates:\n" + "\n".join(errors))


def parse_nbp_rate_changes(xml_bytes: bytes, rate_id: str = "ref") -> pd.DataFrame:
    """Każda zmiana wybranej stopy NBP: data obowiązywania i wysokość w %.

    W pliku XML każdy blok <pozycje obowiazuje_od="RRRR-MM-DD"> zawiera stopy
    obowiązujące od tej daty; stopa referencyjna to <pozycja id="ref"
    oprocentowanie="5,75" .../> (przecinek dziesiętny).
    """
    root = ET.fromstring(xml_bytes)
    rows = []
    for block in root.iter():
        valid_from = block.get("obowiazuje_od")
        if not valid_from:
            continue
        for item in block:
            if item.get("id") == rate_id:
                rows.append({
                    "valid_from": pd.Timestamp(valid_from),
                    "rate_pct": float(item.get("oprocentowanie").replace(",", ".")),
                })
    if not rows:
        raise ValueError(f"No '{rate_id}' rate found in the NBP file")
    return (pd.DataFrame(rows).drop_duplicates("valid_from")
            .sort_values("valid_from").reset_index(drop=True))


def monthly_average_rate(changes: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Średnia stopa obowiązująca w każdym miesiącu (ważona liczbą dni), od start do end włącznie."""
    days = pd.date_range(start, pd.Timestamp(end) + pd.offsets.MonthEnd(0), freq="D")
    rate = changes.set_index("valid_from")["rate_pct"]
    daily = rate.reindex(rate.index.union(days)).ffill().reindex(days)
    monthly = daily.groupby(daily.index.to_period("M")).mean().round(3)
    return pd.DataFrame({
        "month": monthly.index.to_timestamp(),
        "reference_rate_pct": monthly.to_numpy(),
    })


# ---------------------------------------------------------------------------
# Wynagrodzenia GUS (API BDL)
# ---------------------------------------------------------------------------

def fetch_bdl_variable_info(var_id: int = BDL_WAGE_VARIABLE) -> dict:
    """Metadane zmiennej BDL - do sprawdzenia, czy pobieramy właściwy wskaźnik."""
    r = requests.get(f"{BDL_API}/variables/{var_id}",
                     params={"format": "json", "lang": "pl"}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_bdl_by_variable(var_id: int, years: list[int], unit_level: int,
                          save_to: Path | None = None, page_size: int = 100) -> list[dict]:
    """Wszystkie strony wyników /data/by-variable dla jednej zmiennej (bez klucza API: maks. 5 zapytań/s)."""
    results, page = [], 0
    while True:
        params = [("format", "json"), ("lang", "pl"), ("unit-level", unit_level),
                  ("page-size", page_size), ("page", page)] + [("year", y) for y in years]
        r = requests.get(f"{BDL_API}/data/by-variable/{var_id}",
                         params=params, headers=HEADERS, timeout=30)
        r.raise_for_status()
        payload = r.json()
        batch = payload.get("results", [])
        results.extend(batch)
        total = payload.get("totalRecords", len(results))
        if not batch or len(results) >= total:
            break
        page += 1
        time.sleep(0.4)
    if save_to:
        import json
        Path(save_to).parent.mkdir(parents=True, exist_ok=True)
        Path(save_to).write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
    print(f"Downloaded {len(results)} territorial units")
    return results


def _city_key_from_unit_name(name: str) -> str | None:
    """'Powiat m. Kraków' / 'Powiat m.st. Warszawa' -> 'krakow' / 'warszawa'.
    Powiaty ziemskie, np. 'Powiat krakowski', są pomijane."""
    key = normalize_key(pd.Series([name])).iloc[0]
    key = "".join(ch for ch in key if ch.isalpha())
    key = key.removeprefix("powiat")
    if not key.startswith("m"):          # 'm.' lub 'm.st.' = miasto na prawach powiatu
        return None
    for city in CITIES:
        if key.endswith(city):
            return city
    return None


def parse_bdl_wages(results: list[dict]) -> pd.DataFrame:
    """Zostawia 15 miast z projektu; jeden wiersz na miasto i rok."""
    rows = []
    for unit in results:
        city = _city_key_from_unit_name(unit.get("name", ""))
        if city is None:
            continue
        for v in unit.get("values", []):
            if v.get("val") is None:
                continue
            rows.append({
                "city_key": city,
                "year": int(v["year"]),
                "avg_gross_wage_pln": round(float(v["val"]), 2),
                "bdl_unit_id": unit.get("id"),
                "bdl_unit_name": unit.get("name"),
            })
    out = pd.DataFrame(rows).sort_values(["city_key", "year"]).reset_index(drop=True)
    missing = sorted(set(CITIES) - set(out["city_key"]))
    if missing:
        print("Warning - cities not found in the BDL response:", missing)
    return out
