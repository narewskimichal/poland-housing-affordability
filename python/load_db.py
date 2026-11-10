"""
Ładowanie czystych tabel CSV do bazy PostgreSQL "housing".

Tabele muszą już istnieć (najpierw uruchom sql/schema.sql). Dane są ładowane
poleceniem COPY - najszybszym sposobem masowego ładowania w PostgreSQL - w jednej
transakcji: albo ładują się wszystkie tabele, albo nic się nie zmienia.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# Kolejność ładowania wynika z kluczy obcych: najpierw tabele nadrzędne, potem podrzędne.
# tabela -> (plik csv, kolumny z liczbami całkowitymi, kolumny z datami)
TABLES = {
    "cities": ("cities.csv", ["sale_listings", "rent_listings"], []),
    "listings": ("listings.csv",
                 ["rooms", "floor", "floor_count", "build_year", "poi_count",
                  "months_listed", "n_price_changes"],
                 ["first_seen", "last_seen"]),
    "sale_snapshots": ("sale_snapshots.csv", [], ["snapshot_month"]),
    "rent_snapshots": ("rent_snapshots.csv", [], ["snapshot_month"]),
    "nbp_reference_rate": ("nbp_reference_rate.csv", [], ["month"]),
    "gus_wages": ("gus_wages.csv", ["year"], []),
}


def get_engine(password: str, host: str = "localhost", port: int = 5432,
               database: str = "housing", user: str = "postgres"):
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")


def table_columns(conn, table: str) -> list[str]:
    """Nazwy kolumn tabeli w bazie, w kolejności z tabeli."""
    rows = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t ORDER BY ordinal_position"
    ), {"t": table}).fetchall()
    if not rows:
        raise RuntimeError(f"Table '{table}' not found - run sql/schema.sql first")
    return [r[0] for r in rows]


def prepare_table(csv_path: Path, columns: list[str], int_cols: list[str],
                  date_cols: list[str]) -> pd.DataFrame:
    """Wczytuje czysty CSV i dopasowuje go dokładnie do tabeli w bazie."""
    df = pd.read_csv(csv_path, parse_dates=date_cols)
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{csv_path.name}: columns missing in the CSV: {missing}")
    df = df[columns].copy()
    for col in int_cols:
        df[col] = df[col].astype("Int64")   # 3, a nie 3.0 - wymagane dla kolumn całkowitych
    return df


def to_copy_buffer(df: pd.DataFrame) -> io.StringIO:
    """Tekst CSV w formacie oczekiwanym przez COPY: bez nagłówka, puste pole = NULL."""
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="", date_format="%Y-%m-%d")
    buf.seek(0)
    return buf


def load_all(engine, clean_dir: Path) -> pd.DataFrame:
    """Czyści tabele z danymi i ładuje wszystkie pliki CSV w jednej transakcji."""
    clean_dir = Path(clean_dir)
    summary = []
    raw = engine.raw_connection()
    try:
        with engine.connect() as conn:
            prepared = {}
            for table, (file, int_cols, date_cols) in TABLES.items():
                prepared[table] = prepare_table(clean_dir / file, table_columns(conn, table),
                                                int_cols, date_cols)
        cur = raw.cursor()
        # najpierw tabele podrzędne, żeby klucze obce pozwoliły na usunięcie danych
        cur.execute("TRUNCATE " + ", ".join(reversed(list(TABLES))) + ";")
        for table, df in prepared.items():
            cols = ", ".join(df.columns)
            cur.copy_expert(f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT csv, NULL '')",
                            to_copy_buffer(df))
            summary.append({"table": table, "rows_in_csv": len(df)})
        raw.commit()
        cur.close()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()
    return pd.DataFrame(summary)


def row_counts(engine) -> pd.DataFrame:
    """Liczba wierszy w każdej tabeli bazy - do porównania z plikami CSV."""
    parts = " UNION ALL ".join(
        f"SELECT '{t}' AS table_name, COUNT(*) AS rows_in_database FROM {t}"
        for t in ["months", *TABLES]
    )
    with engine.connect() as conn:
        return pd.read_sql(text(parts), conn)
