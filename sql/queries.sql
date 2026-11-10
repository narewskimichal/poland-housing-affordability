-- =============================================================================
-- Poland Housing Affordability - pytania biznesowe
--
-- Perspektywa: osoba prywatna, która szuka mieszkania dla siebie w jednym
-- z 15 największych miast Polski. Każde zapytanie odpowiada na jedno pytanie.
--
-- Ceny to ceny OFERTOWE z ogłoszeń (nie ceny transakcyjne).
-- "Typowa cena" = mediana, bo kilka luksusowych mieszkań zawyżyłoby średnią.
-- Sprzedaż: 08.2023 - 06.2024, najem: 11.2023 - 06.2024.
--
-- W DBeaverze: ustaw kursor w zapytaniu i wciśnij Ctrl+Enter.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- P1. Gdzie mieszkania są najtańsze i najdroższe - do kupna i do wynajęcia?
--     Typowa cena za m² w ostatnim miesiącu z rankingiem miast.
--     Techniki: CTE, JOIN, GROUP BY, mediana (PERCENTILE_CONT), RANK()
-- -----------------------------------------------------------------------------
WITH latest AS (
    SELECT MAX(snapshot_month) AS month FROM sale_snapshots
),
sale AS (
    SELECT l.city_key,
           COUNT(*) AS sale_listings,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.price_per_m2) AS sale_price_m2
    FROM sale_snapshots s
    JOIN listings l ON l.listing_key = s.listing_key
    WHERE s.snapshot_month = (SELECT month FROM latest)
    GROUP BY l.city_key
),
rent AS (
    SELECT l.city_key,
           COUNT(*) AS rent_listings,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY r.price_per_m2) AS rent_price_m2
    FROM rent_snapshots r
    JOIN listings l ON l.listing_key = r.listing_key
    WHERE r.snapshot_month = (SELECT month FROM latest)
    GROUP BY l.city_key
)
SELECT c.city_name,
       s.sale_listings,
       ROUND(s.sale_price_m2::numeric, 0)               AS median_sale_price_m2,
       RANK() OVER (ORDER BY s.sale_price_m2 DESC)      AS sale_price_rank,
       r.rent_listings,
       ROUND(r.rent_price_m2::numeric, 1)               AS median_rent_m2,
       RANK() OVER (ORDER BY r.rent_price_m2 DESC)      AS rent_rank
FROM cities c
JOIN sale s ON s.city_key = c.city_key
JOIN rent r ON r.city_key = c.city_key
ORDER BY sale_price_rank;


-- -----------------------------------------------------------------------------
-- P2. Jak zmieniały się ceny ofertowe w ciągu roku?
--     Typowa cena sprzedaży za m² wg miasta i miesiąca, zmiana względem
--     poprzedniego miesiąca i względem pierwszego miesiąca danych.
--     Techniki: CTE, LAG(), FIRST_VALUE(), okno z PARTITION BY
-- -----------------------------------------------------------------------------
WITH monthly AS (
    SELECT l.city_key,
           s.snapshot_month,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.price_per_m2) AS price_m2
    FROM sale_snapshots s
    JOIN listings l ON l.listing_key = s.listing_key
    GROUP BY l.city_key, s.snapshot_month
)
SELECT c.city_name,
       m.snapshot_month,
       ROUND(m.price_m2::numeric, 0) AS median_price_m2,
       ROUND((m.price_m2 / LAG(m.price_m2) OVER w - 1)::numeric * 100, 1)          AS change_vs_prev_month_pct,
       ROUND((m.price_m2 / FIRST_VALUE(m.price_m2) OVER w - 1)::numeric * 100, 1)  AS change_since_start_pct
FROM monthly m
JOIN cities c ON c.city_key = m.city_key
WINDOW w AS (PARTITION BY m.city_key ORDER BY m.snapshot_month)
ORDER BY c.city_name, m.snapshot_month;


-- -----------------------------------------------------------------------------
-- P3. Na co stać przeciętnie zarabiającego?
--     Ile m² kupi jedna przeciętna miesięczna pensja brutto i ile lat pensji
--     kosztuje mieszkanie 50 m² (ostatni miesiąc, wynagrodzenia z tego samego roku).
--     Techniki: CTE, JOIN po dwóch kluczach, RANK()
-- -----------------------------------------------------------------------------
WITH latest AS (
    SELECT MAX(snapshot_month) AS month FROM sale_snapshots
),
price AS (
    SELECT l.city_key,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.price_per_m2) AS price_m2
    FROM sale_snapshots s
    JOIN listings l ON l.listing_key = s.listing_key
    WHERE s.snapshot_month = (SELECT month FROM latest)
    GROUP BY l.city_key
)
SELECT c.city_name,
       w.avg_gross_wage_pln,
       ROUND(p.price_m2::numeric, 0)                                AS median_price_m2,
       ROUND(w.avg_gross_wage_pln / p.price_m2::numeric, 2)         AS m2_per_monthly_wage,
       ROUND(50 * p.price_m2::numeric / (12 * w.avg_gross_wage_pln), 1) AS years_of_pay_for_50m2,
       RANK() OVER (ORDER BY w.avg_gross_wage_pln / p.price_m2 DESC) AS affordability_rank
FROM price p
JOIN cities c    ON c.city_key = p.city_key
JOIN gus_wages w ON w.city_key = p.city_key
                AND w.year = EXTRACT(YEAR FROM (SELECT month FROM latest))
ORDER BY affordability_rank;


-- -----------------------------------------------------------------------------
-- P4. Kupić czy wynająć? Miesięczna rata kredytu a czynsz za typowe mieszkanie 40-60 m²
--     Założenia: 20% wkładu własnego, kredyt na 25 lat w ratach równych,
--     oprocentowanie = stopa referencyjna NBP w danym miesiącu + 2,0 pkt proc. marży.
--     Techniki: łańcuch CTE, JOIN z tabelą stóp, wzór na ratę annuitetową
-- -----------------------------------------------------------------------------
WITH latest AS (
    SELECT MAX(snapshot_month) AS month FROM rent_snapshots
),
typical AS (
    SELECT l.city_key,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.price) AS flat_price
    FROM sale_snapshots s
    JOIN listings l ON l.listing_key = s.listing_key
    WHERE s.snapshot_month = (SELECT month FROM latest)
      AND l.square_meters BETWEEN 40 AND 60
    GROUP BY l.city_key
),
rent AS (
    SELECT l.city_key,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY r.price) AS monthly_rent
    FROM rent_snapshots r
    JOIN listings l ON l.listing_key = r.listing_key
    WHERE r.snapshot_month = (SELECT month FROM latest)
      AND l.square_meters BETWEEN 40 AND 60
    GROUP BY l.city_key
),
loan AS (
    SELECT t.city_key,
           t.flat_price,
           0.8 * t.flat_price                              AS loan_amount,
           (n.reference_rate_pct + 2.0) / 100 / 12         AS monthly_rate,
           25 * 12                                         AS n_payments
    FROM typical t
    CROSS JOIN nbp_reference_rate n
    WHERE n.month = (SELECT month FROM latest)
)
SELECT c.city_name,
       ROUND(lo.flat_price::numeric, -3)                                      AS typical_price_pln,
       ROUND((lo.loan_amount * lo.monthly_rate
              / (1 - POWER(1 + lo.monthly_rate, -lo.n_payments)))::numeric, 0) AS mortgage_payment_pln,
       ROUND(r.monthly_rent::numeric, 0)                                      AS typical_rent_pln,
       ROUND((lo.loan_amount * lo.monthly_rate
              / (1 - POWER(1 + lo.monthly_rate, -lo.n_payments))
              / r.monthly_rent)::numeric, 2)                                  AS payment_to_rent_ratio,
       ROUND((lo.flat_price / (12 * r.monthly_rent))::numeric, 1)             AS years_of_rent_to_buy
FROM loan lo
JOIN rent r   ON r.city_key = lo.city_key
JOIN cities c ON c.city_key = lo.city_key
ORDER BY payment_to_rent_ratio;


-- -----------------------------------------------------------------------------
-- P5. O ile droższe jest mieszkanie blisko centrum?
--     Typowa cena za m² wg odległości od centrum w porównaniu z typową ceną
--     w całym mieście (wszystkie miesiące sprzedaży).
--     Techniki: agregacja na dwóch poziomach w CTE, JOIN na poziomie miasta
-- -----------------------------------------------------------------------------
WITH zone AS (
    SELECT l.city_key, l.distance_zone,
           COUNT(*) AS snapshots,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.price_per_m2) AS price_m2
    FROM sale_snapshots s
    JOIN listings l ON l.listing_key = s.listing_key
    GROUP BY l.city_key, l.distance_zone
),
city AS (
    SELECT l.city_key,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.price_per_m2) AS price_m2
    FROM sale_snapshots s
    JOIN listings l ON l.listing_key = s.listing_key
    GROUP BY l.city_key
)
SELECT ci.city_name,
       z.distance_zone,
       z.snapshots,
       ROUND(z.price_m2::numeric, 0)                          AS median_price_m2,
       ROUND((z.price_m2 / c.price_m2 - 1)::numeric * 100, 1) AS vs_city_median_pct
FROM zone z
JOIN city c    ON c.city_key  = z.city_key
JOIN cities ci ON ci.city_key = z.city_key
WHERE z.snapshots >= 30          -- pomijamy grupy zbyt małe, żeby były wiarygodne
ORDER BY ci.city_name,
         CASE z.distance_zone WHEN '0–2 km' THEN 1 WHEN '2–5 km' THEN 2
                              WHEN '5–10 km' THEN 3 ELSE 4 END;


-- -----------------------------------------------------------------------------
-- P6. Ile do ceny dodaje winda, miejsce parkingowe, balkon i komórka lokatorska?
--     Dla każdego miasta: typowa cena za m² z daną cechą i bez niej;
--     potem mediana tych premii z poziomu miast (porównujemy w obrębie miast,
--     żeby ceny w Warszawie nie zniekształciły wyniku).
--     Uwaga: to zależność, a nie przyczyna - np. komórki lokatorskie są typowe
--     dla starszych bloków, które są tańsze z innych powodów.
--     Techniki: CROSS JOIN LATERAL (VALUES ...) do zamiany kolumn na wiersze,
--     agregacja warunkowa z FILTER, agregacja zagnieżdżona
-- -----------------------------------------------------------------------------
WITH feature_rows AS (
    SELECT l.city_key, f.feature, f.has_feature, s.price_per_m2
    FROM sale_snapshots s
    JOIN listings l ON l.listing_key = s.listing_key
    CROSS JOIN LATERAL (VALUES
        ('Elevator',      l.has_elevator),
        ('Parking space', l.has_parking_space),
        ('Balcony',       l.has_balcony),
        ('Storage room',  l.has_storage_room)
    ) AS f(feature, has_feature)
    WHERE f.has_feature IS NOT NULL
),
by_city AS (
    SELECT city_key, feature,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_m2) FILTER (WHERE has_feature)     AS with_m2,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_m2) FILTER (WHERE NOT has_feature) AS without_m2,
           AVG(has_feature::int) AS share_with
    FROM feature_rows
    GROUP BY city_key, feature
)
SELECT feature,
       ROUND(AVG(share_with)::numeric * 100, 0)                                                   AS share_of_listings_pct,
       ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY with_m2 / without_m2 - 1))::numeric * 100, 1) AS median_premium_pct,
       ROUND(MIN(with_m2 / without_m2 - 1)::numeric * 100, 1)                                     AS lowest_city_pct,
       ROUND(MAX(with_m2 / without_m2 - 1)::numeric * 100, 1)                                     AS highest_city_pct
FROM by_city
GROUP BY feature
ORDER BY median_premium_pct DESC;


-- -----------------------------------------------------------------------------
-- P7. Nowy czy stary budynek - jak wiek budynku wpływa na cenę?
--     Udział ogłoszeń i indeks cen wg okresu budowy (mediana miasta = 100).
--     Techniki: indeks cen w obrębie miasta, okno SUM() OVER () do udziałów
-- -----------------------------------------------------------------------------
WITH city AS (
    SELECT l.city_key,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.price_per_m2) AS city_m2
    FROM sale_snapshots s
    JOIN listings l ON l.listing_key = s.listing_key
    GROUP BY l.city_key
),
indexed AS (
    SELECT l.build_era,
           s.price_per_m2 / c.city_m2 * 100 AS price_index
    FROM sale_snapshots s
    JOIN listings l ON l.listing_key = s.listing_key
    JOIN city c     ON c.city_key    = l.city_key
)
SELECT build_era,
       COUNT(*)                                                    AS snapshots,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)          AS share_pct,
       ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_index))::numeric, 0) AS price_index_city_100
FROM indexed
GROUP BY build_era
ORDER BY CASE build_era
             WHEN 'Before 1945'   THEN 1 WHEN '1945–1969' THEN 2 WHEN '1970–1989' THEN 3
             WHEN '1990–2009'     THEN 4 WHEN '2010 or newer' THEN 5 ELSE 6 END;


-- -----------------------------------------------------------------------------
-- P8. Lokalizacje przyjazne rodzinom: ile mieszkań ma szkołę i przedszkole
--     w promieniu 500 m i czy są droższe?
--     Techniki: warunki w agregacjach, FILTER, porównanie w obrębie miasta
-- -----------------------------------------------------------------------------
WITH flagged AS (
    SELECT l.city_key,
           s.price_per_m2,
           (l.school_distance_km <= 0.5 AND l.kindergarten_distance_km <= 0.5) AS family_friendly
    FROM sale_snapshots s
    JOIN listings l ON l.listing_key = s.listing_key
    WHERE s.snapshot_month = (SELECT MAX(snapshot_month) FROM sale_snapshots)
)
SELECT c.city_name,
       COUNT(*)                                                          AS listings,
       ROUND(100.0 * COUNT(*) FILTER (WHERE family_friendly) / COUNT(*), 0) AS family_friendly_pct,
       ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_m2) FILTER (WHERE family_friendly)
            / PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_m2) FILTER (WHERE NOT family_friendly)
            - 1)::numeric * 100, 1)                                       AS price_premium_pct
FROM flagged f
JOIN cities c ON c.city_key = f.city_key
GROUP BY c.city_name
ORDER BY family_friendly_pct DESC;


-- -----------------------------------------------------------------------------
-- P9. Jak długo mieszkania są w sprzedaży i jak często sprzedający obniżają cenę?
--     Tylko ogłoszenia, które pojawiły się po pierwszym miesiącu (ich prawdziwy
--     początek jest znany) i których opis nie zmieniał się między miesiącami.
--     Techniki: FILTER, średnie warunkowe, flagi jakości danych w WHERE
-- -----------------------------------------------------------------------------
SELECT c.city_name,
       COUNT(*)                                                               AS listings,
       ROUND(AVG(l.months_listed), 1)                                         AS avg_months_listed,
       ROUND(100.0 * COUNT(*) FILTER (WHERE l.last_price < l.first_price) / COUNT(*), 1) AS cut_price_pct,
       ROUND(AVG(l.price_change_pct) FILTER (WHERE l.last_price < l.first_price), 1)     AS avg_cut_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE NOT l.still_listed_at_end) / COUNT(*), 0)    AS gone_before_end_pct
FROM listings l
JOIN cities c ON c.city_key = l.city_key
WHERE l.offer_type = 'sale'
  AND NOT l.listed_at_start
  AND NOT l.inconsistent_history
GROUP BY c.city_name
ORDER BY cut_price_pct DESC;


-- -----------------------------------------------------------------------------
-- P10. Czy podaż rośnie? Aktywne i nowe ogłoszenia sprzedaży w każdym miesiącu,
--      z sumą narastającą nowych ogłoszeń i zmianą liczby aktywnych ofert.
--      Techniki: CTE, LEFT JOIN, suma narastająca SUM() OVER (ORDER BY), LAG()
-- -----------------------------------------------------------------------------
WITH active AS (
    SELECT snapshot_month AS month, COUNT(*) AS active_listings
    FROM sale_snapshots
    GROUP BY snapshot_month
),
new_listings AS (
    SELECT first_seen AS month, COUNT(*) AS new_listings
    FROM listings
    WHERE offer_type = 'sale'
      AND NOT listed_at_start            -- w pierwszym miesiącu nie ma "nowych" ogłoszeń
    GROUP BY first_seen
)
SELECT a.month,
       a.active_listings,
       ROUND((a.active_listings::numeric / LAG(a.active_listings) OVER (ORDER BY a.month) - 1) * 100, 1)
                                                             AS active_change_pct,
       COALESCE(n.new_listings, 0)                           AS new_listings,
       SUM(COALESCE(n.new_listings, 0)) OVER (ORDER BY a.month) AS new_listings_running_total
FROM active a
LEFT JOIN new_listings n ON n.month = a.month
ORDER BY a.month;
