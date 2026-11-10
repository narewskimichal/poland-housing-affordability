-- =============================================================================
-- Poland Housing Affordability - schemat bazy danych (PostgreSQL)
--
-- Uruchom ten skrypt raz w bazie "housing", przed załadowaniem danych.
-- Można go uruchomić ponownie w dowolnym momencie: usuwa i tworzy od nowa
-- wszystkie tabele (razem z danymi).
--
-- Model:
--   cities ──< listings ──< sale_snapshots >── months ──< nbp_reference_rate
--     │                 └──< rent_snapshots >──┘
--     └──< gus_wages
-- =============================================================================

DROP TABLE IF EXISTS sale_snapshots, rent_snapshots, listings,
                     nbp_reference_rate, gus_wages, cities, months CASCADE;


-- -----------------------------------------------------------------------------
-- months: jeden wiersz na miesiąc kalendarzowy (wspólny wymiar czasu)
-- -----------------------------------------------------------------------------
CREATE TABLE months (
    month        DATE        PRIMARY KEY,          -- pierwszy dzień miesiąca
    year         SMALLINT    NOT NULL,
    month_number SMALLINT    NOT NULL CHECK (month_number BETWEEN 1 AND 12),
    month_name   VARCHAR(9)  NOT NULL,
    quarter      SMALLINT    NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    year_month   CHAR(7)     NOT NULL UNIQUE,      -- np. 2024-03
    CHECK (EXTRACT(DAY FROM month) = 1)
);

INSERT INTO months (month, year, month_number, month_name, quarter, year_month)
SELECT d::date,
       EXTRACT(YEAR FROM d),
       EXTRACT(MONTH FROM d),
       TRIM(TO_CHAR(d, 'Month')),
       EXTRACT(QUARTER FROM d),
       TO_CHAR(d, 'YYYY-MM')
FROM generate_series(DATE '2023-01-01', DATE '2030-12-01', INTERVAL '1 month') AS d;


-- -----------------------------------------------------------------------------
-- cities: 15 miast objętych ogłoszeniami
-- -----------------------------------------------------------------------------
CREATE TABLE cities (
    city_key      VARCHAR(20)   PRIMARY KEY,       -- np. krakow
    city_name     VARCHAR(40)   NOT NULL UNIQUE,   -- np. Kraków
    voivodeship   VARCHAR(40)   NOT NULL,
    latitude      NUMERIC(9,6)  NOT NULL,          -- mediana położenia ogłoszeń
    longitude     NUMERIC(9,6)  NOT NULL,
    sale_listings INTEGER       NOT NULL CHECK (sale_listings >= 0),
    rent_listings INTEGER       NOT NULL CHECK (rent_listings >= 0)
);


-- -----------------------------------------------------------------------------
-- listings: jeden wiersz na mieszkanie (najnowszy opis + historia ogłoszenia)
-- -----------------------------------------------------------------------------
CREATE TABLE listings (
    listing_key              VARCHAR(40)   PRIMARY KEY,   -- S-<id> sprzedaż, R-<id> najem
    listing_id               VARCHAR(40)   NOT NULL,
    offer_type               VARCHAR(4)    NOT NULL CHECK (offer_type IN ('sale', 'rent')),
    city_key                 VARCHAR(20)   NOT NULL REFERENCES cities (city_key),

    -- mieszkanie i budynek
    building_type            VARCHAR(30)   NOT NULL,
    square_meters            NUMERIC(6,2)  NOT NULL CHECK (square_meters > 0),
    rooms                    SMALLINT      CHECK (rooms BETWEEN 1 AND 10),
    floor                    SMALLINT      CHECK (floor >= 0),
    floor_count              SMALLINT      CHECK (floor_count BETWEEN 1 AND 60),
    build_year               SMALLINT,
    latitude                 NUMERIC(9,6)  NOT NULL,
    longitude                NUMERIC(9,6)  NOT NULL,
    ownership                VARCHAR(30)   NOT NULL,
    building_material        VARCHAR(30)   NOT NULL,
    condition                VARCHAR(30)   NOT NULL,
    has_parking_space        BOOLEAN,
    has_balcony              BOOLEAN,
    has_elevator             BOOLEAN,
    has_security             BOOLEAN,
    has_storage_room         BOOLEAN,

    -- jakość lokalizacji (km do najbliższego punktu danego rodzaju)
    centre_distance_km       NUMERIC(6,3)  CHECK (centre_distance_km >= 0),
    school_distance_km       NUMERIC(6,3)  CHECK (school_distance_km >= 0),
    clinic_distance_km       NUMERIC(6,3)  CHECK (clinic_distance_km >= 0),
    post_office_distance_km  NUMERIC(6,3)  CHECK (post_office_distance_km >= 0),
    kindergarten_distance_km NUMERIC(6,3)  CHECK (kindergarten_distance_km >= 0),
    restaurant_distance_km   NUMERIC(6,3)  CHECK (restaurant_distance_km >= 0),
    college_distance_km      NUMERIC(6,3)  CHECK (college_distance_km >= 0),
    pharmacy_distance_km     NUMERIC(6,3)  CHECK (pharmacy_distance_km >= 0),
    poi_count                SMALLINT      CHECK (poi_count >= 0),   -- punkty usługowe w promieniu 500 m

    -- przedziały do grupowania w raporcie
    size_band                VARCHAR(20)   NOT NULL,
    build_era                VARCHAR(20)   NOT NULL,
    distance_zone            VARCHAR(20)   NOT NULL,

    -- historia ogłoszenia
    first_seen               DATE          NOT NULL REFERENCES months (month),
    last_seen                DATE          NOT NULL REFERENCES months (month),
    months_listed            SMALLINT      NOT NULL CHECK (months_listed >= 1),
    first_price              NUMERIC(12,2) NOT NULL CHECK (first_price > 0),
    last_price               NUMERIC(12,2) NOT NULL CHECK (last_price > 0),
    n_price_changes          SMALLINT      NOT NULL CHECK (n_price_changes >= 0),
    price_change_pct         NUMERIC(8,2)  NOT NULL,
    listed_at_start          BOOLEAN       NOT NULL,   -- było już w pierwszym miesiącu: prawdziwy początek nieznany
    still_listed_at_end      BOOLEAN       NOT NULL,
    inconsistent_history     BOOLEAN       NOT NULL,   -- powierzchnia/położenie/pokoje zmieniły się między miesiącami

    UNIQUE (offer_type, listing_id),
    CHECK (last_seen >= first_seen),
    CHECK ((offer_type = 'sale' AND listing_key LIKE 'S-%')
        OR (offer_type = 'rent' AND listing_key LIKE 'R-%'))
);

CREATE INDEX ix_listings_city       ON listings (city_key);
CREATE INDEX ix_listings_offer_type ON listings (offer_type);


-- -----------------------------------------------------------------------------
-- sale_snapshots / rent_snapshots: cena każdego mieszkania w każdym miesiącu
-- -----------------------------------------------------------------------------
CREATE TABLE sale_snapshots (
    listing_key    VARCHAR(40)   NOT NULL REFERENCES listings (listing_key),
    snapshot_month DATE          NOT NULL REFERENCES months (month),
    price          NUMERIC(12,2) NOT NULL CHECK (price > 0),          -- zł
    price_per_m2   NUMERIC(10,2) NOT NULL CHECK (price_per_m2 > 0),   -- zł za m²
    PRIMARY KEY (listing_key, snapshot_month),
    CHECK (listing_key LIKE 'S-%')
);

CREATE TABLE rent_snapshots (
    listing_key    VARCHAR(40)   NOT NULL REFERENCES listings (listing_key),
    snapshot_month DATE          NOT NULL REFERENCES months (month),
    price          NUMERIC(12,2) NOT NULL CHECK (price > 0),          -- zł miesięcznie
    price_per_m2   NUMERIC(10,2) NOT NULL CHECK (price_per_m2 > 0),
    PRIMARY KEY (listing_key, snapshot_month),
    CHECK (listing_key LIKE 'R-%')
);

CREATE INDEX ix_sale_snapshots_month ON sale_snapshots (snapshot_month);
CREATE INDEX ix_rent_snapshots_month ON rent_snapshots (snapshot_month);


-- -----------------------------------------------------------------------------
-- nbp_reference_rate: stopa referencyjna NBP, średnia miesięczna
-- -----------------------------------------------------------------------------
CREATE TABLE nbp_reference_rate (
    month              DATE         PRIMARY KEY REFERENCES months (month),
    reference_rate_pct NUMERIC(6,3) NOT NULL CHECK (reference_rate_pct >= 0)
);


-- -----------------------------------------------------------------------------
-- gus_wages: przeciętne miesięczne wynagrodzenie brutto wg miasta i roku (GUS, BDL)
-- -----------------------------------------------------------------------------
CREATE TABLE gus_wages (
    city_key           VARCHAR(20)   NOT NULL REFERENCES cities (city_key),
    year               SMALLINT      NOT NULL CHECK (year BETWEEN 2000 AND 2100),
    avg_gross_wage_pln NUMERIC(10,2) NOT NULL CHECK (avg_gross_wage_pln > 0),
    bdl_unit_id        VARCHAR(12),
    bdl_unit_name      VARCHAR(60),
    PRIMARY KEY (city_key, year)
);


-- -----------------------------------------------------------------------------
-- Opisy tabel (widoczne w DBeaverze i w słowniku danych)
-- -----------------------------------------------------------------------------
COMMENT ON TABLE months             IS 'Miesiące kalendarzowe - wspólny wymiar czasu';
COMMENT ON TABLE cities             IS '15 największych miast Polski objętych ogłoszeniami';
COMMENT ON TABLE listings           IS 'Jeden wiersz na mieszkanie na sprzedaż lub wynajem: najnowszy opis i historia ogłoszenia';
COMMENT ON TABLE sale_snapshots     IS 'Cena ofertowa każdego mieszkania na sprzedaż w każdym miesiącu (08.2023 - 06.2024)';
COMMENT ON TABLE rent_snapshots     IS 'Ofertowy czynsz najmu każdego mieszkania w każdym miesiącu (11.2023 - 06.2024)';
COMMENT ON TABLE nbp_reference_rate IS 'Stopa referencyjna NBP, średnia miesięczna ważona liczbą dni obowiązywania';
COMMENT ON TABLE gus_wages          IS 'Przeciętne miesięczne wynagrodzenie brutto w mieście (GUS BDL, zm. 64428, bez podmiotów do 9 osób)';
