# Test questions

15 questions used to test the agent: 12 inside the scope of the project and 3 outside it. "Expected answer" comes from the knowledge base; "Result" is filled in after testing.

| # | Question | Expected answer | Result |
|---|---|---|---|
| 1 | Gdzie mieszkania są najdroższe, a gdzie najtańsze? | Warszawa 17 923 zł/m², Radom 6 695 zł/m² (czerwiec 2024) | OK – both, plus top 5 / bottom 5 lists and the 2.7× ratio |
| 2 | Jaka była mediana ceny za m² w Katowicach w czerwcu 2024? | 8 460 zł/m² | OK |
| 3 | O ile wzrosły ceny w Krakowie od sierpnia 2023? | +25,4% | OK – 13 018 → 16 322 zł/m², +25.4% |
| 4 | Ile m² kupi przeciętna miesięczna pensja w Katowicach, a ile w Warszawie? | 1,19 m² vs 0,60 m² | OK – also gives wages (10 052 / 10 715 zł) |
| 5 | Ile lat pensji kosztuje mieszkanie 50 m² w Warszawie? | 7,0 lat (pensji brutto) | OK – about 7 years |
| 6 | Jaka jest rata kredytu i czynsz za typowe mieszkanie 40–60 m² we Wrocławiu? | rata 3 958 zł, czynsz 2 900 zł | OK – also +36% and the loan assumptions |
| 7 | W którym mieście rata najmniej różni się od czynszu? | Radom, rata wyższa o 5% | OK – Radom, 2 097 vs 2 000 zł |
| 8 | Ile do ceny za m² dodaje winda? | ok. +15% (mediana dla miast) | OK – about +15%, with city examples |
| 9 | Czy mieszkania w centrum Łodzi są droższe niż w reszcie miasta? | Nie, ok. 6,6% tańsze niż mediana miasta | OK – 6.6% cheaper, old tenement houses |
| 10 | Jak często sprzedający w Radomiu obniżają cenę? | 19,4% ogłoszeń, średnio o 5,1% | OK |
| 11 | What was the median rent per m² in Gdańsk in June 2024? | 65.2 zł/m² | Correct number (65.2 zł/m²), but answered in Polish – see note below |
| 12 | Jakie założenia przyjęto przy liczeniu raty kredytu? | 20% wkładu, 25 lat, 7,75% (stopa NBP 5,75% + 2 pkt proc. marży) | OK |
| 13 | Ile kosztuje mieszkanie w Gliwicach? | poza zakresem (brak danych dla Gliwic) | OK – exact out-of-scope sentence |
| 14 | Jaka jest dziś stopa procentowa NBP? | poza zakresem | OK – exact out-of-scope sentence |
| 15 | Czy opłaca się teraz kupić mieszkanie w Krakowie jako inwestycję? | brak porady inwestycyjnej / poza zakresem | OK – out-of-scope sentence, no advice |

Result: all 15 answers had the correct figure or the correct out-of-scope reply. Tested in the Copilot Studio test panel on 10 November 2026.

Note on question 11: the instruction only says "answer in the language of the question (Polish or English)". The knowledge base mixes English text with Polish city names and units, and the agent answered this English question in Polish. A stricter rule ("an English question gets an English answer") would most likely fix it.
