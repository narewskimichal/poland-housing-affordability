-- =============================================================================
-- Poland Housing Affordability - warstwa raportowa dla Power BI
--
-- Power BI czyta wyłącznie te widoki (schemat "reporting"), nigdy tabel bazowych.
-- Widoki układają dane w schemat gwiazdy: trzy widoki faktów (ceny sprzedaży,
-- czynsze, wynagrodzenia) wokół wspólnych wymiarów (ogłoszenie, miasto, miesiąc),
-- z etykietami gotowymi do raportu i kolumnami do sortowania.
--
-- Wartości widoczne na wykresach są tu tłumaczone na polski; tabele bazowe
-- i cały proces w Pythonie zostają po angielsku.
--
-- Uruchom po schema.sql i po załadowaniu danych. Można uruchamiać wielokrotnie.
--
--                     dim_month
--                   /     |     \
--   fact_sale_price  fact_rent_price  fact_city_wage
--          |    \        /    |         /
--   dim_listing  dim_city ----+--------+
-- =============================================================================

DROP SCHEMA IF EXISTS reporting CASCADE;
CREATE SCHEMA reporting;


-- -----------------------------------------------------------------------------
-- dim_month: 11 miesięcy objętych ogłoszeniami, ze stopą NBP
-- -----------------------------------------------------------------------------
CREATE VIEW reporting.dim_month AS
SELECT m.month,
       m.year,
       m.month_number,
       (ARRAY['styczeń', 'luty', 'marzec', 'kwiecień', 'maj', 'czerwiec', 'lipiec',
              'sierpień', 'wrzesień', 'październik', 'listopad', 'grudzień'])[m.month_number]
                                                       AS month_name,
       (ARRAY['sty', 'lut', 'mar', 'kwi', 'maj', 'cze', 'lip', 'sie', 'wrz', 'paź', 'lis', 'gru'])[m.month_number]
           || ' ' || m.year                            AS month_label,      -- np. mar 2024
       m.year * 100 + m.month_number                   AS month_sort,       -- klucz sortowania dla month_label
       m.quarter,
       (ARRAY['I', 'II', 'III', 'IV'])[m.quarter] || ' kw. ' || m.year
                                                       AS quarter_label,    -- np. II kw. 2024
       n.reference_rate_pct,
       EXISTS (SELECT 1 FROM sale_snapshots s WHERE s.snapshot_month = m.month) AS has_sale_data,
       EXISTS (SELECT 1 FROM rent_snapshots r WHERE r.snapshot_month = m.month) AS has_rent_data
FROM months m
LEFT JOIN nbp_reference_rate n ON n.month = m.month
WHERE m.month BETWEEN (SELECT MIN(snapshot_month) FROM sale_snapshots)
                  AND (SELECT MAX(snapshot_month) FROM sale_snapshots);


-- -----------------------------------------------------------------------------
-- dim_city: 15 miast
-- -----------------------------------------------------------------------------
CREATE VIEW reporting.dim_city AS
SELECT city_key,
       city_name,
       voivodeship,
       latitude,
       longitude
FROM cities;


-- -----------------------------------------------------------------------------
-- dim_listing: jeden wiersz na mieszkanie - wszystko, czym filtrujemy i grupujemy.
-- Celowo bez city_key: fakty łączą się z dim_city bezpośrednio, więc w Power BI
-- jest tylko jedna ścieżka od ceny do miasta.
-- -----------------------------------------------------------------------------
CREATE VIEW reporting.dim_listing AS
SELECT l.listing_key,
       CASE l.offer_type WHEN 'sale' THEN 'Sprzedaż' ELSE 'Najem' END AS offer_type,
       l.square_meters,
       l.rooms,
       l.floor,
       l.floor_count,
       l.build_year,
       CASE l.building_type
            WHEN 'Block of flats'     THEN 'Blok'
            WHEN 'Apartment building' THEN 'Apartamentowiec'
            WHEN 'Tenement'           THEN 'Kamienica'
            ELSE 'Brak danych' END                        AS building_type,
       CASE l.ownership
            WHEN 'Full ownership'   THEN 'Pełna własność'
            WHEN 'Cooperative'      THEN 'Spółdzielcze'
            WHEN 'Shared ownership' THEN 'Udział'
            ELSE 'Brak danych' END                        AS ownership,
       CASE l.building_material
            WHEN 'Brick'         THEN 'Cegła'
            WHEN 'Concrete slab' THEN 'Wielka płyta'
            ELSE 'Brak danych' END                        AS building_material,
       CASE l.condition
            WHEN 'Premium'     THEN 'Wysoki standard'
            WHEN 'To renovate' THEN 'Do remontu'
            ELSE 'Brak danych' END                        AS condition,

       -- etykiety tak / nie / brak danych do fragmentatorów
       CASE WHEN l.has_elevator      THEN 'Tak' WHEN NOT l.has_elevator      THEN 'Nie' ELSE 'Brak danych' END AS elevator,
       CASE WHEN l.has_parking_space THEN 'Tak' WHEN NOT l.has_parking_space THEN 'Nie' ELSE 'Brak danych' END AS parking_space,
       CASE WHEN l.has_balcony       THEN 'Tak' WHEN NOT l.has_balcony       THEN 'Nie' ELSE 'Brak danych' END AS balcony,
       CASE WHEN l.has_storage_room  THEN 'Tak' WHEN NOT l.has_storage_room  THEN 'Nie' ELSE 'Brak danych' END AS storage_room,
       CASE WHEN l.has_security      THEN 'Tak' WHEN NOT l.has_security      THEN 'Nie' ELSE 'Brak danych' END AS security,

       -- lokalizacja
       l.latitude,
       l.longitude,
       l.centre_distance_km,
       l.school_distance_km,
       l.kindergarten_distance_km,
       l.clinic_distance_km,
       l.pharmacy_distance_km,
       l.poi_count,
       CASE WHEN l.school_distance_km <= 0.5 AND l.kindergarten_distance_km <= 0.5
            THEN 'Tak' ELSE 'Nie' END                     AS school_and_kindergarten_500m,

       -- przedziały z kluczami sortowania (Power BI: Sortuj według kolumny)
       l.size_band,
       CASE l.size_band WHEN '<35 m²' THEN 1 WHEN '35–50 m²' THEN 2 WHEN '50–70 m²' THEN 3
                        WHEN '70–90 m²' THEN 4 WHEN '90+ m²' THEN 5 ELSE 9 END            AS size_band_sort,
       CASE l.build_era WHEN 'Before 1945'   THEN 'Przed 1945'
                        WHEN '2010 or newer' THEN '2010 i nowsze'
                        WHEN 'Unknown'       THEN 'Brak danych'
                        ELSE l.build_era END                                              AS build_era,
       CASE l.build_era WHEN 'Before 1945' THEN 1 WHEN '1945–1969' THEN 2 WHEN '1970–1989' THEN 3
                        WHEN '1990–2009' THEN 4 WHEN '2010 or newer' THEN 5 ELSE 9 END    AS build_era_sort,
       l.distance_zone,
       CASE l.distance_zone WHEN '0–2 km' THEN 1 WHEN '2–5 km' THEN 2
                            WHEN '5–10 km' THEN 3 WHEN '10+ km' THEN 4 ELSE 9 END         AS distance_zone_sort,

       -- historia ogłoszenia i flagi jakości
       l.first_seen,
       l.last_seen,
       l.months_listed,
       l.first_price,
       l.last_price,
       l.n_price_changes,
       l.price_change_pct,
       CASE WHEN l.last_price < l.first_price THEN 'Obniżka'
            WHEN l.last_price > l.first_price THEN 'Podwyżka'
            ELSE 'Bez zmian' END                          AS price_change_direction,
       l.listed_at_start,
       l.still_listed_at_end,
       l.inconsistent_history
FROM listings l;


-- -----------------------------------------------------------------------------
-- fact_sale_price: cena ofertowa każdego mieszkania na sprzedaż w każdym miesiącu
-- -----------------------------------------------------------------------------
CREATE VIEW reporting.fact_sale_price AS
SELECT s.listing_key,
       l.city_key,
       s.snapshot_month AS month,
       s.price,
       s.price_per_m2,
       l.square_meters
FROM sale_snapshots s
JOIN listings l ON l.listing_key = s.listing_key;


-- -----------------------------------------------------------------------------
-- fact_rent_price: ofertowy czynsz każdego mieszkania w każdym miesiącu
-- -----------------------------------------------------------------------------
CREATE VIEW reporting.fact_rent_price AS
SELECT r.listing_key,
       l.city_key,
       r.snapshot_month AS month,
       r.price          AS rent,
       r.price_per_m2   AS rent_per_m2,
       l.square_meters
FROM rent_snapshots r
JOIN listings l ON l.listing_key = r.listing_key;


-- -----------------------------------------------------------------------------
-- fact_city_wage: przeciętne wynagrodzenie brutto wg miasta i miesiąca
-- (GUS publikuje wartości roczne - każdy miesiąc dostaje wartość ze swojego roku)
-- -----------------------------------------------------------------------------
CREATE VIEW reporting.fact_city_wage AS
SELECT w.city_key,
       m.month,
       w.year,
       w.avg_gross_wage_pln
FROM gus_wages w
JOIN reporting.dim_month m ON m.year = w.year;


COMMENT ON SCHEMA reporting IS 'Widoki czytane przez Power BI - schemat gwiazdy danych mieszkaniowych';
