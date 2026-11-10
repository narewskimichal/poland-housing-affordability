"""
Funkcje czyszczące dane w projekcie Poland Housing Affordability.

Każda funkcja przyjmuje DataFrame i zwraca oczyszczoną kopię (a tam, gdzie to
przydatne, także małą tabelę z tym, co znalazła), dzięki czemu notebook może
pokazać efekt każdej operacji osobno. CleaningLog zbiera, ile wierszy i wartości
zmieniła każda operacja - to część raportu jakości danych.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Dane referencyjne
# ---------------------------------------------------------------------------

FILE_PATTERN = re.compile(r"^apartments_(rent_)?pl_(\d{4})_(\d{2})\.csv$")

# city_key (małe litery, bez polskich znaków) -> (nazwa wyświetlana, województwo)
CITIES = {
    "warszawa": ("Warszawa", "mazowieckie"),
    "krakow": ("Kraków", "małopolskie"),
    "wroclaw": ("Wrocław", "dolnośląskie"),
    "lodz": ("Łódź", "łódzkie"),
    "poznan": ("Poznań", "wielkopolskie"),
    "gdansk": ("Gdańsk", "pomorskie"),
    "gdynia": ("Gdynia", "pomorskie"),
    "szczecin": ("Szczecin", "zachodniopomorskie"),
    "bydgoszcz": ("Bydgoszcz", "kujawsko-pomorskie"),
    "lublin": ("Lublin", "lubelskie"),
    "katowice": ("Katowice", "śląskie"),
    "bialystok": ("Białystok", "podlaskie"),
    "czestochowa": ("Częstochowa", "śląskie"),
    "radom": ("Radom", "mazowieckie"),
    "rzeszow": ("Rzeszów", "podkarpackie"),
}

# Surowe kody kategorii (znormalizowane) -> czytelne etykiety
CATEGORY_LABELS = {
    "building_type": {
        "blockofflats": "Block of flats",
        "apartmentbuilding": "Apartment building",
        "tenement": "Tenement",
    },
    "ownership": {
        "condominium": "Full ownership",
        "cooperative": "Cooperative",
        "udzial": "Shared ownership",
    },
    "building_material": {
        "brick": "Brick",
        "concreteslab": "Concrete slab",
    },
    "condition": {
        "premium": "Premium",
        "low": "To renovate",
    },
}

COLUMN_NAMES = {
    "id": "listing_id",
    "city": "city_key",
    "type": "building_type",
    "squareMeters": "square_meters",
    "rooms": "rooms",
    "floor": "floor",
    "floorCount": "floor_count",
    "buildYear": "build_year",
    "latitude": "latitude",
    "longitude": "longitude",
    "centreDistance": "centre_distance_km",
    "poiCount": "poi_count",
    "schoolDistance": "school_distance_km",
    "clinicDistance": "clinic_distance_km",
    "postOfficeDistance": "post_office_distance_km",
    "kindergartenDistance": "kindergarten_distance_km",
    "restaurantDistance": "restaurant_distance_km",
    "collegeDistance": "college_distance_km",
    "pharmacyDistance": "pharmacy_distance_km",
    "ownership": "ownership",
    "buildingMaterial": "building_material",
    "condition": "condition",
    "hasParkingSpace": "has_parking_space",
    "hasBalcony": "has_balcony",
    "hasElevator": "has_elevator",
    "hasSecurity": "has_security",
    "hasStorageRoom": "has_storage_room",
    "price": "price",
}

FLAG_COLUMNS = [
    "has_parking_space", "has_balcony", "has_elevator",
    "has_security", "has_storage_room",
]
INTEGER_COLUMNS = ["rooms", "floor", "floor_count", "build_year", "poi_count"]
DISTANCE_COLUMNS = [c for c in COLUMN_NAMES.values() if c.endswith("_distance_km")]

# Atrybuty opisujące samo mieszkanie
STATIC_COLUMNS = [
    "city_key", "building_type", "square_meters", "rooms", "floor", "floor_count",
    "build_year", "latitude", "longitude", *DISTANCE_COLUMNS, "poi_count",
    "ownership", "building_material", "condition", *FLAG_COLUMNS,
]

# Kolumny, których braki śledzimy w raporcie jakości
TRACKED_MISSING = [
    "build_year", "building_type", "building_material",
    "has_elevator", "floor", "floor_count", "condition",
]

# Atrybuty BUDYNKU (wspólne dla wszystkich mieszkań w nim) - do uzupełniania braków z budynku
BUILDING_COLUMNS = ["build_year", "building_type", "building_material", "has_elevator"]
BUILDING_KEY = ["city_key", "latitude", "longitude"]

# Reguły biznesowe dla wiarygodnych cen (zł za m²)
PRICE_PER_M2_LIMITS = {"sale": (2_000, 60_000), "rent": (10, 250)}

# Prostokąt obejmujący Polskę (z małym marginesem)
LAT_RANGE = (48.9, 55.0)
LON_RANGE = (14.0, 24.2)

_PL_CHARS = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


# ---------------------------------------------------------------------------
# Log czyszczenia
# ---------------------------------------------------------------------------

class CleaningLog:
    """Zbiera jeden wiersz na operację: wiersze przed i po, liczba zmienionych lub uzupełnionych wartości."""

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def record(self, operation: str, rows_before: int, rows_after: int,
               values_changed: int = 0, note: str = "") -> None:
        self.rows.append({
            "operation": operation,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "rows_removed": rows_before - rows_after,
            "values_changed": values_changed,
            "note": note,
        })

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


# ---------------------------------------------------------------------------
# Funkcje pomocnicze
# ---------------------------------------------------------------------------

def normalize_key(s: pd.Series) -> pd.Series:
    """Małe litery, bez polskich znaków, bez spacji, podkreślników i myślników."""
    return (
        s.astype("string")
        .str.strip()
        .str.lower()
        .str.translate(_PL_CHARS)
        .str.replace(r"[\s_\-]+", "", regex=True)
    )


def profile(df: pd.DataFrame) -> pd.DataFrame:
    """Jeden wiersz na kolumnę: typ, liczba braków i liczba różnych wartości."""
    out = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "non_null": df.notna().sum(),
        "missing": df.isna().sum(),
        "missing_pct": (df.isna().mean() * 100).round(1),
        "distinct": df.nunique(dropna=True),
    })
    return out.sort_values("missing_pct", ascending=False)


def duplicate_offer_key() -> list[str]:
    return ["offer_type", "snapshot_month", "city_key", "latitude", "longitude",
            "square_meters", "floor", "rooms", "price"]


def count_duplicate_offers(df: pd.DataFrame) -> int:
    """Liczba nadmiarowych wierszy opisujących ofertę, która istnieje już pod innym ID."""
    known_floor = df["floor"].notna()
    return int(df.loc[known_floor].duplicated(subset=duplicate_offer_key()).sum())


def quality_summary(df: pd.DataFrame, stage: str) -> pd.Series:
    """Najważniejsze wskaźniki jakości danych do porównania przed i po czyszczeniu."""
    data = {
        "Wiersze": len(df),
        "Ogłoszenia": df[["offer_type", "listing_id"]].drop_duplicates().shape[0],
        "Duplikaty ofert pod różnymi ID": count_duplicate_offers(df),
    }
    for col in TRACKED_MISSING:
        data[f"Braki: {col} (%)"] = round(df[col].isna().mean() * 100, 1)
    return pd.Series(data, name=stage)


# ---------------------------------------------------------------------------
# Wczytanie
# ---------------------------------------------------------------------------

def load_raw(raw_dir: Path) -> pd.DataFrame:
    """Wczytuje wszystkie miesięczne pliki CSV i łączy je w jedną tabelę.

    Dodaje kolumny: offer_type (sale / rent), snapshot_month (pierwszy dzień
    miesiąca) i source_file (z którego pliku pochodzi wiersz).
    """
    frames = []
    for path in sorted(Path(raw_dir).glob("*.csv")):
        m = FILE_PATTERN.match(path.name)
        if not m:
            print(f"Pomijam nieoczekiwany plik: {path.name}")
            continue
        df = pd.read_csv(path, dtype={"id": "string"})
        df["offer_type"] = "rent" if m.group(1) else "sale"
        df["snapshot_month"] = pd.Timestamp(int(m.group(2)), int(m.group(3)), 1)
        df["source_file"] = path.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"Brak plików CSV z ogłoszeniami w {raw_dir}")
    return pd.concat(frames, ignore_index=True)


def file_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Liczba wierszy wg typu oferty i miesiąca - szybkie sprawdzenie, czy wczytały się wszystkie pliki."""
    return (
        df.pivot_table(index="snapshot_month", columns="offer_type",
                       values="id", aggfunc="count")
        .rename_axis(columns=None)
        .astype("Int64")
    )


# ---------------------------------------------------------------------------
# Ujednolicenie nazw, tekstu i typów danych
# ---------------------------------------------------------------------------

def standardize(df: pd.DataFrame, log: CleaningLog) -> tuple[pd.DataFrame, dict]:
    """Nazwy kolumn w snake_case, przycięty tekst, klucze miast i czytelne kategorie.

    Zwraca oczyszczoną tabelę i słownik wartości kategorii bez etykiety
    (zostają bez zmian, więc nic nie ginie po cichu).
    """
    out = df.rename(columns=COLUMN_NAMES).copy()
    changed = 0
    unmapped: dict[str, list] = {}

    new_city = normalize_key(out["city_key"])
    changed += int((new_city != out["city_key"].astype("string")).fillna(False).sum())
    out["city_key"] = new_city
    unknown_cities = sorted(set(out["city_key"].dropna()) - set(CITIES))
    if unknown_cities:
        unmapped["city_key"] = unknown_cities

    for col, labels in CATEGORY_LABELS.items():
        raw = out[col].astype("string")
        key = normalize_key(raw)
        mapped = key.map(labels)
        missing_label = key.notna() & mapped.isna()
        if missing_label.any():
            unmapped[col] = sorted(raw[missing_label].str.strip().unique().tolist())
        new_values = mapped.fillna(raw.str.strip()).astype("string")
        changed += int((new_values != raw).fillna(False).sum())
        out[col] = new_values

    log.record("Ujednolicenie nazw i tekstu", len(df), len(out), changed,
               "nazwy kolumn w snake_case, klucze miast, czytelne etykiety kategorii")
    return out, unmapped


def convert_types(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """yes/no -> prawda/fałsz, liczby i lata -> liczby całkowite, miary -> liczby zmiennoprzecinkowe."""
    out = df.copy()
    changed = 0
    for col in FLAG_COLUMNS:
        key = normalize_key(out[col])
        out[col] = key.map({"yes": True, "no": False}).astype("boolean")
        changed += int(out[col].notna().sum())
    for col in INTEGER_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce").round().astype("Int64")
    for col in ["square_meters", "latitude", "longitude", *DISTANCE_COLUMNS, "price"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
    out["price_per_m2"] = (out["price"] / out["square_meters"]).round(2)
    log.record("Konwersja typów danych", len(df), len(out), changed,
               "yes/no na prawda/fałsz; pokoje, piętra, lata na liczby całkowite; dodana cena za m²")
    return out


# ---------------------------------------------------------------------------
# Testy poprawności
# ---------------------------------------------------------------------------

def run_validation_checks(df: pd.DataFrame, log: CleaningLog,
                          iqr_k: float = 3.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Standardowe testy: duplikaty, niemożliwe wartości, niewiarygodne ceny.

    Niemożliwe wartości atrybutów są zamieniane na braki (samo ogłoszenie zostaje);
    wiersze, które nie przejdą testu na poziomie wiersza, są usuwane. Zwraca tabelę
    i zestawienie, ile wierszy oznaczył każdy test.
    """
    out = df.copy()
    rows_before = len(out)
    checks = []

    def add(check, action, mask):
        mask = pd.Series(mask, index=out.index).fillna(False).astype(bool)
        checks.append({"check": check, "action": action, "rows_flagged": int(mask.sum())})
        return mask

    # Duplikaty
    data_cols = [c for c in out.columns if c != "source_file"]
    exact = add("Identyczne wiersze", "usuń", out.duplicated(subset=data_cols))
    same_month = add("To samo ogłoszenie dwa razy w miesiącu", "usuń (zostaw ostatnie)",
                     out.duplicated(subset=["offer_type", "listing_id", "snapshot_month"],
                                    keep="last") & ~exact)

    # Niemożliwe wartości atrybutów -> brak danych
    year = out["snapshot_month"].dt.year
    attr_rules = [
        ("floor", "Piętro poniżej 0", out["floor"] < 0),
        ("floor", "Piętro wyższe niż budynek", out["floor"] > out["floor_count"]),
        ("floor_count", "Budynek z <1 lub >60 piętrami",
         (out["floor_count"] < 1) | (out["floor_count"] > 60)),
        ("build_year", "Rok budowy przed 1800 lub >5 lat w przyszłość",
         (out["build_year"] < 1800) | (out["build_year"] > year + 5)),
        ("rooms", "Liczba pokoi poza 1-10", (out["rooms"] < 1) | (out["rooms"] > 10)),
    ]
    attr_rules += [(c, f"Ujemna wartość {c}", out[c] < 0) for c in DISTANCE_COLUMNS]
    nulled = 0
    for col, check, mask in attr_rules:
        mask = add(check, f"{col} -> brak danych", mask)
        out.loc[mask, col] = pd.NA
        nulled += int(mask.sum())

    # Wiersze bezużyteczne
    bad_location = add("Współrzędne poza Polską", "usuń",
                       ~out["latitude"].between(*LAT_RANGE) | ~out["longitude"].between(*LON_RANGE))
    bad_area = add("Powierzchnia poza 10-400 m²", "usuń", ~out["square_meters"].between(10, 400))
    bad_price = add("Brak ceny lub cena niedodatnia", "usuń", ~(out["price"] > 0))

    # Niewiarygodne ceny
    low = out["offer_type"].map({k: v[0] for k, v in PRICE_PER_M2_LIMITS.items()})
    high = out["offer_type"].map({k: v[1] for k, v in PRICE_PER_M2_LIMITS.items()})
    business = add("Cena za m² poza limitami biznesowymi (sprzedaż 2-60 tys., najem 10-250 zł)",
                   "usuń", ~out["price_per_m2"].between(low, high))
    log_ppm = np.log(out["price_per_m2"].where(out["price_per_m2"] > 0))
    grp = log_ppm.groupby([out["offer_type"], out["city_key"]])
    q1 = grp.transform(lambda x: x.quantile(0.25))
    q3 = grp.transform(lambda x: x.quantile(0.75))
    iqr = q3 - q1
    extreme = add(f"Cena za m² skrajna dla swojego miasta (reguła {iqr_k}×IQR)", "usuń",
                  (log_ppm < q1 - iqr_k * iqr) | (log_ppm > q3 + iqr_k * iqr))

    drop = exact | same_month | bad_location | bad_area | bad_price | business | extreme
    out = out.loc[~drop].reset_index(drop=True)
    log.record("Testy poprawności", rows_before, len(out), nulled,
               "duplikaty, niemożliwe wartości, niewiarygodne ceny")
    return out, pd.DataFrame(checks)


# ---------------------------------------------------------------------------
# Duplikaty ofert pod różnymi ID
# ---------------------------------------------------------------------------

def remove_duplicate_offers(df: pd.DataFrame, log: CleaningLog) -> tuple[pd.DataFrame, pd.DataFrame]:
    """To samo mieszkanie wystawione pod dwoma ID (np. przez dwie agencje).

    Wiersze uznajemy za tę samą ofertę, gdy w tym samym miesiącu i typie oferty
    mają identyczne współrzędne, powierzchnię, piętro, liczbę pokoi i cenę.
    Porównujemy tylko wiersze ze znanym piętrem, żeby nie usunąć za dużo.
    Zostaje ogłoszenie widoczne w największej liczbie miesięcy, więc jego historia
    jest kompletna. Zwraca tabelę i kilka przykładowych par duplikatów.
    """
    key = duplicate_offer_key()
    known_floor = df["floor"].notna()
    in_group = known_floor & df.duplicated(subset=key, keep=False)

    months_seen = df.groupby(["offer_type", "listing_id"])["snapshot_month"].transform("size")
    cand = df.loc[in_group, key + ["listing_id"]].assign(months_seen=months_seen[in_group])
    cand = cand.sort_values(["months_seen", "listing_id"], ascending=[False, True])
    keep_idx = cand.drop_duplicates(subset=key, keep="first").index
    drop_idx = cand.index.difference(keep_idx)

    show = ["listing_id", "offer_type", "snapshot_month", "city_key", "square_meters",
            "rooms", "floor", "price"]
    examples = df.loc[in_group].sort_values(key)[show].head(6)

    out = df.drop(index=drop_idx).reset_index(drop=True)
    log.record("Usunięcie duplikatów ofert pod różnymi ID", len(df), len(out), 0,
               "ten sam miesiąc, położenie, powierzchnia, piętro, pokoje i cena")
    return out, examples


# ---------------------------------------------------------------------------
# Niespójne historie ogłoszeń
# ---------------------------------------------------------------------------

def find_inconsistent_listings(df: pd.DataFrame, area_tol: float = 0.10,
                               move_km: float = 1.0) -> pd.DataFrame:
    """Opis ogłoszenia nie powinien zmieniać się między miesiącami.

    Flagi dla każdego ogłoszenia:
    - area_changed: powierzchnia różni się między miesiącami o więcej niż area_tol (10%)
    - moved: współrzędne przesuwają się o więcej niż move_km (1 km)
    - rooms_changed: zmienia się liczba pokoi
    Drobne poprawki (np. 45,0 -> 45,5 m²) nie są oznaczane.
    """
    g = df.groupby(["offer_type", "listing_id"])
    area = g["square_meters"].agg(["min", "max"])
    lat = g["latitude"].agg(["min", "max"])
    lon = g["longitude"].agg(["min", "max"])
    dy = (lat["max"] - lat["min"]) * 111.0
    dx = (lon["max"] - lon["min"]) * 111.0 * np.cos(np.radians(lat["min"]))
    flags = pd.DataFrame({
        "area_changed": (area["max"] / area["min"] - 1) > area_tol,
        "moved": np.sqrt(dx ** 2 + dy ** 2) > move_km,
        "rooms_changed": g["rooms"].nunique() > 1,
    })
    flags["inconsistent_history"] = flags.any(axis=1)
    return flags


def inconsistency_summary(flags: pd.DataFrame) -> pd.DataFrame:
    total = len(flags)
    out = flags.sum().rename("listings").to_frame()
    out["share_pct"] = (out["listings"] / total * 100).round(2)
    out.index = ["Powierzchnia zmieniona o >10%", "Przesunięcie o >1 km", "Zmiana liczby pokoi",
                 "Którakolwiek z powyższych"]
    return out


# ---------------------------------------------------------------------------
# Uzupełnianie braków
# ---------------------------------------------------------------------------

def fill_from_same_listing(df: pd.DataFrame, cols: list[str],
                           log: CleaningLog) -> tuple[pd.DataFrame, pd.Series]:
    """Jeśli ogłoszenie ma wartość w części miesięcy, a w innych nie, i wszystkie
    znane wartości są zgodne, kopiujemy ją do miesięcy z brakiem."""
    out = df.copy()
    keys = ["offer_type", "listing_id"]
    filled = {}
    for col in cols:
        g = out.groupby(keys)[col]
        n_values = g.transform("nunique")
        value = g.transform("first")
        mask = out[col].isna() & (n_values == 1)
        out.loc[mask, col] = value[mask]
        filled[col] = int(mask.sum())
    filled = pd.Series(filled, name="values_filled")
    log.record("Uzupełnienie braków z innych miesięcy tego samego ogłoszenia",
               len(df), len(out), int(filled.sum()), ", ".join(cols))
    return out, filled


def _latest_per_listing(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values("snapshot_month").groupby(["offer_type", "listing_id"]).tail(1)


def _building_values(listings: pd.DataFrame, col: str, max_listings: int,
                     min_known: int) -> pd.Series:
    """Wartość `col` dla każdego budynku, w którym regułę można zastosować:
    najwyżej `max_listings` ogłoszeń w dokładnie tym punkcie (większe grupy to zwykle
    współrzędne ulicy lub dzielnicy, a nie jednego budynku), co najmniej `min_known`
    ogłoszeń ze znaną wartością i wszystkie znane wartości zgodne."""
    stats = listings.groupby(BUILDING_KEY).agg(
        n_listings=("listing_id", "size"),
        n_known=(col, "count"),
        n_values=(col, "nunique"),
        value=(col, "first"),
    )
    ok = ((stats["n_listings"] <= max_listings) & (stats["n_known"] >= min_known)
          & (stats["n_values"] == 1))
    return stats.loc[ok, "value"]


def validate_building_fill(df: pd.DataFrame, cols: list[str] = BUILDING_COLUMNS,
                           max_listings: int = 30, min_known: int = 2,
                           holdout: float = 0.10, seed: int = 42) -> pd.DataFrame:
    """Test reguły budynkowej przed jej użyciem: ukrywamy 10% ZNANYCH wartości,
    uzupełniamy je regułą i sprawdzamy, jak często uzupełniona wartość jest poprawna."""
    listings = _latest_per_listing(df)
    rows = []
    for col in cols:
        known_idx = listings.index[listings[col].notna()]
        hidden = listings.loc[known_idx].sample(frac=holdout, random_state=seed).index
        test = listings.copy()
        truth = test.loc[hidden, col]
        test.loc[hidden, col] = pd.NA
        values = _building_values(test, col, max_listings, min_known)
        predicted = pd.Series(
            values.reindex(pd.MultiIndex.from_frame(test.loc[hidden, BUILDING_KEY])).to_numpy(),
            index=hidden,
        )
        got = predicted.notna()
        if pd.api.types.is_numeric_dtype(truth) and not pd.api.types.is_bool_dtype(truth):
            correct = predicted[got].astype(float) == truth[got].astype(float)
        else:
            correct = predicted[got].astype(str) == truth[got].astype(str)
        row = {"column": col, "hidden_values": len(hidden),
               "could_fill_pct": round(got.mean() * 100, 1),
               "correct_pct": round(correct.mean() * 100, 1)}
        if col == "build_year":
            diff = (predicted[got].astype(float) - truth[got].astype(float)).abs()
            row["within_2_years_pct"] = round((diff <= 2).mean() * 100, 1)
        rows.append(row)
    return pd.DataFrame(rows).set_index("column")


def fill_from_same_building(df: pd.DataFrame, log: CleaningLog,
                            cols: list[str] = BUILDING_COLUMNS, max_listings: int = 30,
                            min_known: int = 2) -> tuple[pd.DataFrame, pd.Series]:
    """Uzupełnia atrybuty budynku (rok budowy, typ, materiał, winda) na podstawie
    innych ogłoszeń o identycznych współrzędnych, regułą przetestowaną w
    validate_building_fill."""
    out = df.copy()
    listings = _latest_per_listing(out)
    row_keys = pd.MultiIndex.from_frame(out[BUILDING_KEY])
    filled = {}
    for col in cols:
        values = _building_values(listings, col, max_listings, min_known)
        candidate = pd.Series(values.reindex(row_keys).to_numpy(), index=out.index)
        mask = out[col].isna() & candidate.notna()
        out.loc[mask, col] = candidate[mask].astype(out[col].dtype)
        filled[col] = int(mask.sum())
    filled = pd.Series(filled, name="values_filled")
    log.record("Uzupełnienie atrybutów budynku z tego samego budynku",
               len(df), len(out), int(filled.sum()), ", ".join(cols))
    return out, filled


# ---------------------------------------------------------------------------
# Tabele wynikowe
# ---------------------------------------------------------------------------

SIZE_BINS = [0, 35, 50, 70, 90, np.inf]
SIZE_LABELS = ["<35 m²", "35–50 m²", "50–70 m²", "70–90 m²", "90+ m²"]
ERA_BINS = [-np.inf, 1945, 1970, 1990, 2010, np.inf]
ERA_LABELS = ["Before 1945", "1945–1969", "1970–1989", "1990–2009", "2010 or newer"]
ZONE_BINS = [0, 2, 5, 10, np.inf]
ZONE_LABELS = ["0–2 km", "2–5 km", "5–10 km", "10+ km"]


def _band(values: pd.Series, bins, labels) -> pd.Series:
    return (pd.cut(values.astype("float64"), bins=bins, labels=labels, right=False)
            .astype("string").fillna("Unknown"))


def build_tables(df: pd.DataFrame, flags: pd.DataFrame,
                 log: CleaningLog) -> dict[str, pd.DataFrame]:
    """Dzieli miesięczne wiersze na:
    - listings: jeden wiersz na mieszkanie (najnowszy opis + historia ogłoszenia + flaga jakości),
    - sale_snapshots / rent_snapshots: jeden wiersz na mieszkanie na miesiąc (tylko cena),
    - cities: 15 miast z nazwami wyświetlanymi i województwami.
    """
    df = df.sort_values(["offer_type", "listing_id", "snapshot_month"]).copy()
    df["listing_key"] = (df["offer_type"].map({"sale": "S", "rent": "R"})
                         + "-" + df["listing_id"].astype("string"))

    g = df.groupby("listing_key")
    price_diff = g["price"].diff()
    changed = (price_diff.notna() & (price_diff != 0)).astype(int)
    history = pd.DataFrame({
        "first_seen": g["snapshot_month"].min(),
        "last_seen": g["snapshot_month"].max(),
        "months_listed": g["snapshot_month"].nunique(),
        "first_price": g["price"].first(),
        "last_price": g["price"].last(),
        "n_price_changes": changed.groupby(df["listing_key"]).sum(),
    })
    history["price_change_pct"] = (
        (history["last_price"] / history["first_price"] - 1) * 100
    ).round(2)

    latest = g.tail(1).set_index("listing_key")
    first_month = df.groupby("offer_type")["snapshot_month"].min()
    last_month = df.groupby("offer_type")["snapshot_month"].max()
    listings = latest[["listing_id", "offer_type", *STATIC_COLUMNS]].join(history)
    # Ogłoszenie było już w pierwszym miesiącu -> prawdziwy początek nieznany
    listings["listed_at_start"] = listings["first_seen"] == listings["offer_type"].map(first_month)
    listings["still_listed_at_end"] = listings["last_seen"] == listings["offer_type"].map(last_month)
    listings = listings.join(
        flags["inconsistent_history"], on=["offer_type", "listing_id"]
    )
    listings["inconsistent_history"] = listings["inconsistent_history"].fillna(False).astype(bool)
    listings["size_band"] = _band(listings["square_meters"], SIZE_BINS, SIZE_LABELS)
    listings["build_era"] = _band(listings["build_year"], ERA_BINS, ERA_LABELS)
    listings["distance_zone"] = _band(listings["centre_distance_km"], ZONE_BINS, ZONE_LABELS)
    for col in ["building_type", "ownership", "building_material", "condition"]:
        listings[col] = listings[col].fillna("Unknown")
    listings = listings.reset_index()

    snap_cols = ["listing_key", "snapshot_month", "price", "price_per_m2"]
    sale = df.loc[df["offer_type"] == "sale", snap_cols].reset_index(drop=True)
    rent = df.loc[df["offer_type"] == "rent", snap_cols].reset_index(drop=True)

    cities = (
        listings.groupby("city_key")
        .agg(latitude=("latitude", "median"), longitude=("longitude", "median"),
             sale_listings=("offer_type", lambda s: int((s == "sale").sum())),
             rent_listings=("offer_type", lambda s: int((s == "rent").sum())))
        .reset_index()
    )
    cities.insert(1, "city_name", cities["city_key"].map(lambda k: CITIES.get(k, (k, None))[0]))
    cities.insert(2, "voivodeship", cities["city_key"].map(lambda k: CITIES.get(k, (None, None))[1]))

    log.record("Podział na tabele modelu", len(df), len(df), 0,
               f"{len(listings):,} ogłoszeń, {len(sale):,} cen sprzedaży + {len(rent):,} czynszów")
    return {"listings": listings, "sale_snapshots": sale,
            "rent_snapshots": rent, "cities": cities}


def save_tables(tables: dict[str, pd.DataFrame], out_dir: Path) -> pd.DataFrame:
    """Zapisuje każdą tabelę do CSV (UTF-8) i zwraca krótkie podsumowanie."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, table in tables.items():
        path = out_dir / f"{name}.csv"
        table.to_csv(path, index=False, encoding="utf-8", date_format="%Y-%m-%d")
        rows.append({"file": path.name, "rows": len(table), "columns": table.shape[1],
                     "size_mb": round(path.stat().st_size / 1_048_576, 1)})
    return pd.DataFrame(rows)
