# Poland Housing Affordability – knowledge base for the Q&A agent

This document contains all facts the agent may use. It describes a data analytics project about the housing market in the 15 largest Polish cities. Every number below comes from the project's own analysis.

## About the project

- Author: Michał Narewski. Portfolio project combining Python (data cleaning), SQL (PostgreSQL database and analysis), Power BI (interactive dashboard) and Copilot Studio (this agent).
- Point of view: a private person who wants to buy a flat to live in (not an investor).
- Main data: apartment listings scraped from the Otodom portal, published on Kaggle as "Apartment Prices in Poland" (author: Krzysztof Jamroz). Monthly snapshots of sale offers from August 2023 to June 2024 (11 months) and rent offers from November 2023 to June 2024 (8 months).
- Additional data: NBP reference interest rate (National Bank of Poland) and average monthly gross wages in each city (Statistics Poland, GUS, Local Data Bank, variable 64428, cities with powiat status).
- Cities covered (15): Warszawa, Kraków, Gdańsk, Wrocław, Gdynia, Poznań, Rzeszów, Lublin, Białystok, Szczecin, Katowice, Łódź, Bydgoszcz, Częstochowa, Radom.
- After cleaning: 128,608 unique listings (91,169 for sale, 37,439 for rent), 192,356 monthly sale price records and 70,016 monthly rent records.

## Definitions and assumptions

- All prices are ASKING prices from listings, not transaction prices. Real transaction prices are usually a few percent lower.
- "Typical" price = median, not average, because a few luxury flats would distort the average.
- "Latest month" = June 2024. Unless stated otherwise, city figures refer to June 2024.
- Price per m² = asking price divided by flat area, in PLN (zł).
- Mortgage assumptions used in this document: 20% down payment, 25-year loan with equal instalments, interest rate = NBP reference rate (5.75% in June 2024) + 2.0 percentage points bank margin = 7.75% per year. In the Power BI dashboard these values can be changed with sliders.
- "Typical flat" for the buy-vs-rent comparison = flats of 40–60 m².
- Wages are average monthly GROSS wages from GUS, excluding companies with up to 9 employees. They are a reference point, not the income of every household.
- Price index vs city: median price per m² of a group of flats divided by the median price per m² of the whole city × 100. 100 = typical price in the city; 115 = 15% more expensive per m²; 90 = 10% cheaper. Comparisons show association, not cause.
- Distances (to the centre, school etc.) are straight-line distances in km, not travel times.

## Poland – all 15 cities together (June 2024)

- Median asking price: 14,265 zł per m² (up from 11,386 zł in August 2023, +25.3%).
- Median asking rent: 64.9 zł per m² per month.
- Active offers in June 2024: 21,120 for sale and 8,748 for rent.

## Prices and rents by city (June 2024)

| City | Voivodeship | Sale offers | Median price per m² (zł) | Median flat price (zł) | Rent offers | Median rent per m² (zł) | Median monthly rent (zł) | Price change Aug 2023 → Jun 2024 |
|---|---|---|---|---|---|---|---|---|
| Warszawa | mazowieckie | 6 872 | 17 923 | 899 000 | 3 359 | 79.0 | 4 000 | +21.8% |
| Kraków | małopolskie | 3 156 | 16 322 | 800 000 | 1 740 | 65.6 | 2 999 | +25.4% |
| Gdańsk | pomorskie | 1 916 | 14 100 | 769 000 | 253 | 65.2 | 3 000 | +16.5% |
| Wrocław | dolnośląskie | 2 239 | 13 089 | 695 000 | 864 | 61.1 | 2 900 | +16.8% |
| Gdynia | pomorskie | 806 | 12 646 | 720 000 | 117 | 56.7 | 2 900 | +19.3% |
| Poznań | wielkopolskie | 785 | 11 019 | 599 000 | 494 | 52.7 | 2 400 | +12.4% |
| Rzeszów | podkarpackie | 162 | 10 797 | 593 000 | 89 | 51.2 | 2 400 | +17.0% |
| Lublin | lubelskie | 568 | 9 891 | 558 000 | 199 | 52.7 | 2 500 | +16.4% |
| Białystok | podlaskie | 231 | 9 884 | 499 000 | 53 | 43.2 | 1 800 | +22.0% |
| Szczecin | zachodniopomorskie | 640 | 9 224 | 540 000 | 169 | 53.2 | 2 500 | +15.4% |
| Katowice | śląskie | 582 | 8 460 | 474 000 | 373 | 48.3 | 2 200 | +15.4% |
| Łódź | łódzkie | 1 681 | 8 315 | 400 000 | 693 | 45.8 | 2 000 | +11.6% |
| Bydgoszcz | kujawsko-pomorskie | 917 | 7 987 | 395 000 | 211 | 46.4 | 1 900 | +9.3% |
| Częstochowa | śląskie | 371 | 6 900 | 355 000 | 100 | 39.1 | 1 900 | +14.8% |
| Radom | mazowieckie | 194 | 6 695 | 350 000 | 34 | 39.0 | 1 875 | +9.0% |

The most expensive city is Warszawa (17,923 zł/m²), the cheapest is Radom (6,695 zł/m²) – a 2.7× difference. Prices grew fastest in Kraków (+25.4%) and slowest in Radom (+9.0%).

## Affordability: what an average salary buys (June 2024 prices, 2024 wages)

| City | Average gross wage 2023 (zł) | Average gross wage 2024 (zł) | m² bought by one monthly gross wage | Years of gross pay for a 50 m² flat |
|---|---|---|---|---|
| Radom | 7 042 | 8 269 | 1.24 | 3.4 |
| Katowice | 9 106 | 10 052 | 1.19 | 3.5 |
| Częstochowa | 6 715 | 7 830 | 1.13 | 3.7 |
| Bydgoszcz | 7 478 | 8 448 | 1.06 | 3.9 |
| Łódź | 7 548 | 8 622 | 1.04 | 4.0 |
| Szczecin | 7 933 | 9 045 | 0.98 | 4.2 |
| Poznań | 8 303 | 9 495 | 0.86 | 4.8 |
| Lublin | 7 444 | 8 507 | 0.86 | 4.8 |
| Białystok | 7 089 | 8 282 | 0.84 | 5.0 |
| Rzeszów | 7 429 | 8 680 | 0.80 | 5.2 |
| Gdańsk | 8 916 | 10 107 | 0.72 | 5.8 |
| Wrocław | 8 335 | 9 425 | 0.72 | 5.8 |
| Gdynia | 7 890 | 8 999 | 0.71 | 5.9 |
| Kraków | 9 224 | 10 455 | 0.64 | 6.5 |
| Warszawa | 9 626 | 10 715 | 0.60 | 7.0 |

The most affordable cities relative to local wages are Radom, Katowice and Częstochowa; the least affordable are Warszawa and Kraków. In Katowice one monthly gross wage buys 1.19 m², in Warszawa only 0.60 m².

## Buy or rent? Typical 40–60 m² flat (June 2024)

Assumptions: 20% down payment, 25-year loan, 7.75% interest (NBP reference rate 5.75% + 2.0 pp margin).

| City | Typical price of a 40–60 m² flat (zł) | Monthly mortgage payment (zł) | Typical monthly rent of a 40–60 m² flat (zł) | Payment higher than rent by | Years of rent equal to the price |
|---|---|---|---|---|---|
| Radom | 347 000 | 2 097 | 2 000 | 5% | 14.5 |
| Częstochowa | 325 000 | 1 961 | 1 850 | 6% | 14.6 |
| Katowice | 415 000 | 2 508 | 2 300 | 9% | 15.0 |
| Szczecin | 490 000 | 2 961 | 2 500 | 18% | 16.3 |
| Bydgoszcz | 389 000 | 2 351 | 2 000 | 18% | 16.2 |
| Łódź | 399 000 | 2 411 | 2 025 | 19% | 16.4 |
| Lublin | 520 000 | 3 139 | 2 500 | 26% | 17.3 |
| Rzeszów | 540 000 | 3 263 | 2 500 | 31% | 18.0 |
| Poznań | 559 000 | 3 378 | 2 500 | 35% | 18.6 |
| Gdynia | 624 000 | 3 771 | 2 800 | 35% | 18.6 |
| Wrocław | 655 000 | 3 958 | 2 900 | 36% | 18.8 |
| Gdańsk | 690 000 | 4 169 | 3 000 | 39% | 19.2 |
| Warszawa | 850 000 | 5 136 | 3 500 | 47% | 20.2 |
| Kraków | 770 000 | 4 653 | 3 000 | 55% | 21.4 |
| Białystok | 486 000 | 2 937 | 1 800 | 63% | 22.5 |

In every city the mortgage payment is higher than the rent of a similar flat. The gap is smallest in Radom (+5%), Częstochowa and Katowice, and largest in Białystok (+63%) and Kraków (+55%). The payment covers the purchase of the flat, while rent does not – so this comparison shows the monthly cost, not which option is financially better in the long run.

## What drives the price per m² (all months, within each city)

| City | Centre premium: flats up to 2 km from the centre vs city median | Elevator: price per m² with vs without elevator | New buildings (2010 or later) vs city median | Offers with a school and a kindergarten within 500 m (June 2024) |
|---|---|---|---|---|
| Warszawa | +25.2% | +9.0% | +7.3% | 78% |
| Kraków | +22.2% | +12.3% | +8.5% | 64% |
| Gdańsk | +25.8% | +22.9% | +16.1% | 57% |
| Wrocław | +5.0% | +15.9% | +14.3% | 73% |
| Gdynia | +22.7% | +26.8% | +18.4% | 37% |
| Poznań | +3.3% | +14.3% | +15.3% | 61% |
| Rzeszów | +0.2% | +13.0% | +12.0% | 67% |
| Lublin | +1.1% | +15.1% | +20.2% | 79% |
| Białystok | +0.1% | +12.4% | +22.6% | 85% |
| Szczecin | -7.4% | +24.9% | +35.5% | 69% |
| Katowice | +5.9% | +24.7% | +46.4% | 66% |
| Łódź | -6.6% | +18.1% | +29.3% | 79% |
| Bydgoszcz | -1.9% | +25.2% | +31.4% | 76% |
| Częstochowa | -0.5% | +8.6% | +34.6% | 52% |
| Radom | -1.0% | +5.4% | +36.0% | 90% |

Across cities (median of city-level results): an elevator is linked with about +15% price per m², a parking space +4%, a balcony +2%, while a storage room is linked with about −10% (storage rooms are typical of older blocks of flats, which are cheaper for other reasons). Buildings from 2010 or later have a price index of 114 (city = 100), buildings from 1970–1989 have 92. In Łódź and Szczecin flats in the very centre are cheaper than the city median (−7%), because the centres have many old tenement houses.

## Market dynamics (sale offers)

Only listings whose real start is known (they appeared after August 2023) and whose description did not change between months.

| City | Share of listings with a price cut | Average price cut | Average months on the market (listings that disappeared before June 2024) |
|---|---|---|---|
| Radom | 19.4% | -5.1% | 2.6 |
| Lublin | 17.5% | -4.4% | 1.9 |
| Białystok | 16.2% | -3.5% | 2.1 |
| Bydgoszcz | 15.9% | -5.3% | 2.1 |
| Szczecin | 15.7% | -5.1% | 2.0 |
| Częstochowa | 15.6% | -5.2% | 1.7 |
| Gdynia | 13.6% | -4.7% | 1.9 |
| Łódź | 13.4% | -4.6% | 1.9 |
| Gdańsk | 13.1% | -4.8% | 1.9 |
| Wrocław | 11.9% | -4.6% | 1.8 |
| Poznań | 11.7% | -5.0% | 1.7 |
| Rzeszów | 11.6% | -4.0% | 1.9 |
| Katowice | 11.2% | -5.3% | 1.8 |
| Warszawa | 9.4% | -4.7% | 1.6 |
| Kraków | 9.0% | -4.7% | 1.7 |

Between 5,000 and 8,000 new sale listings appeared every month. A listing disappearing does not always mean the flat was sold.

## Monthly median asking price per m² by city (zł)

| City | Aug 2023 | Sep 2023 | Oct 2023 | Nov 2023 | Dec 2023 | Jan 2024 | Feb 2024 | Mar 2024 | Apr 2024 | May 2024 | Jun 2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Warszawa | 14 714 | 15 211 | 15 623 | 15 957 | 16 766 | 17 134 | 17 368 | 17 636 | 17 833 | 17 842 | 17 923 |
| Kraków | 13 018 | 13 451 | 14 227 | 14 694 | 15 595 | 15 789 | 15 995 | 16 199 | 16 329 | 16 379 | 16 322 |
| Gdańsk | 12 105 | 12 433 | 12 661 | 12 861 | 13 635 | 13 980 | 14 091 | 14 172 | 13 939 | 14 008 | 14 100 |
| Wrocław | 11 204 | 11 358 | 11 667 | 11 869 | 12 308 | 12 568 | 12 807 | 12 977 | 12 981 | 13 125 | 13 089 |
| Gdynia | 10 601 | 10 724 | 11 148 | 11 323 | 12 176 | 12 298 | 12 369 | 12 388 | 12 558 | 12 676 | 12 646 |
| Poznań | 9 800 | 9 984 | 9 989 | 10 132 | 10 780 | 10 760 | 10 896 | 10 868 | 10 934 | 10 969 | 11 019 |
| Rzeszów | 9 227 | 9 274 | 9 603 | 9 400 | 9 372 | 9 842 | 9 963 | 10 525 | 10 721 | 10 824 | 10 797 |
| Lublin | 8 496 | 8 650 | 8 729 | 8 784 | 8 980 | 8 987 | 9 352 | 9 653 | 9 774 | 9 760 | 9 891 |
| Białystok | 8 101 | 8 167 | 8 305 | 8 517 | 8 915 | 9 117 | 9 117 | 9 565 | 9 657 | 9 891 | 9 884 |
| Szczecin | 7 992 | 8 055 | 8 164 | 8 089 | 8 289 | 8 535 | 8 759 | 8 922 | 9 127 | 9 242 | 9 224 |
| Katowice | 7 332 | 7 500 | 7 661 | 7 699 | 7 875 | 7 862 | 7 916 | 7 999 | 8 400 | 8 498 | 8 460 |
| Łódź | 7 448 | 7 481 | 7 558 | 7 725 | 8 034 | 8 000 | 8 088 | 8 088 | 8 140 | 8 280 | 8 315 |
| Bydgoszcz | 7 310 | 7 335 | 7 291 | 7 401 | 7 356 | 7 585 | 7 733 | 7 751 | 7 772 | 7 902 | 7 987 |
| Częstochowa | 6 011 | 6 029 | 5 939 | 6 042 | 6 379 | 6 403 | 6 625 | 6 840 | 6 604 | 6 707 | 6 900 |
| Radom | 6 144 | 6 215 | 6 292 | 6 295 | 6 296 | 6 238 | 6 344 | 6 435 | 6 500 | 6 525 | 6 695 |

## Monthly median asking rent per m² by city (zł)

| City | Nov 2023 | Dec 2023 | Jan 2024 | Feb 2024 | Mar 2024 | Apr 2024 | May 2024 | Jun 2024 |
|---|---|---|---|---|---|---|---|---|
| Warszawa | 81.1 | 80.9 | 80.9 | 80.8 | 81.0 | 80.3 | 78.6 | 79.0 |
| Kraków | 62.9 | 64.6 | 65.5 | 65.3 | 65.2 | 64.4 | 65.7 | 65.6 |
| Gdańsk | 66.0 | 65.9 | 67.0 | 67.1 | 66.6 | 66.7 | 66.0 | 65.2 |
| Wrocław | 63.6 | 62.9 | 62.8 | 62.5 | 61.8 | 62.5 | 61.5 | 61.1 |
| Gdynia | 55.6 | 56.7 | 56.3 | 55.5 | 54.1 | 55.6 | 55.6 | 56.7 |
| Poznań | 51.7 | 52.6 | 53.1 | 53.1 | 51.8 | 52.6 | 52.7 | 52.7 |
| Rzeszów | 52.1 | 53.2 | 52.9 | 51.1 | 52.9 | 50.0 | 50.3 | 51.2 |
| Lublin | 50.0 | 49.5 | 50.0 | 52.0 | 53.7 | 50.0 | 50.9 | 52.7 |
| Białystok | 43.9 | 43.9 | 43.9 | 43.8 | 43.3 | 41.6 | 41.5 | 43.2 |
| Szczecin | 50.2 | 50.0 | 51.6 | 50.4 | 51.5 | 52.4 | 51.4 | 53.2 |
| Katowice | 47.2 | 47.4 | 47.7 | 48.6 | 49.6 | 48.0 | 48.0 | 48.3 |
| Łódź | 44.9 | 45.0 | 45.0 | 45.2 | 44.4 | 44.9 | 46.3 | 45.8 |
| Bydgoszcz | 44.0 | 44.2 | 45.0 | 45.5 | 45.2 | 46.4 | 45.7 | 46.4 |
| Częstochowa | 37.5 | 37.5 | 37.8 | 39.1 | 40.0 | 40.2 | 39.3 | 39.1 |
| Radom | 40.5 | 41.5 | 42.6 | 39.0 | 39.0 | 39.9 | 38.9 | 39.0 |

## Data cleaning summary

- Raw data: 266,415 rows from 19 monthly files. Standard checks (duplicates, impossible values, extreme prices) found nothing – the dataset author had already filtered the data.
- 4,043 rows removed: the same flat posted under two different IDs in the same month.
- 1,527 listings flagged because their area, location or number of rooms changed between months.
- About 21,000 missing building attributes (build year, building type, material, elevator) filled from other months of the same listing and from other flats in the same building. The building rule was tested first: correct in 97% of cases for building material, 93% elevator, 92% building type, 83% build year (91% within 2 years).

## Limitations

- Asking prices, not transaction prices.
- 11 months of data – short-term trends only, not a full market cycle.
- The mortgage calculation is simplified; real offers depend on the bank and the borrower.
- GUS wages exclude small companies and are gross values.
- Only the 15 cities listed above. No data about other cities, villages, commercial property, houses or years outside August 2023 – June 2024.