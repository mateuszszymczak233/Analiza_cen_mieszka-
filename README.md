# 🏠 Analiza Rynku Nieruchomości w Polsce (2023-2024)

Projekt analityczny oparty na danych o cenach mieszkań w 15 największych miastach Polski. System przetwarza ponad **110 000 ofert**, buduje relacyjną bazę danych i generuje automatyczne raporty biznesowe w formacie Excel.

## 🚀 Główne Cele Projektu
- Stworzenie procesu **ETL** (Extract, Transform, Load) dla rozproszonych plików CSV.
- Analiza trendów cenowych (m/m) dla rynku nieruchomości w Katowicach i innych miastach.
- Wykrywanie anomalii rynkowych i "okazji" inwestycyjnych przy użyciu zaawansowanego SQL.
- Automatyzacja raportowania wyników do formatu przyjaznego dla biznesu (Excel).

## 🛠️ Stack Technologiczny
- **Język:** Python 3.x
- **Baza danych:** SQLite (SQL)
- **Biblioteki:** 
  - `Pandas` (przetwarzanie danych)
  - `NumPy` (obliczenia numeryczne)
  - `OpenPyXL` (generowanie plików Excel)
  - `Sqlite3` (silnik bazy danych)

## 📊 Kluczowe Funkcjonalności i Zapytania SQL
W projekcie zaimplementowano 15 zaawansowanych zapytań analitycznych. Najciekawsze z nich to:

### 1. Wykrywanie okazji rynkowych (Window Functions & CTE)
Zapytanie identyfikuje oferty, których cena za m² jest o co najmniej **20% niższa od średniej dla danego miasta** w czerwcu 2024 r.

```sql
WITH x AS (
    SELECT
        id, city, price_per_m2,
        AVG(price_per_m2) OVER (PARTITION BY city) AS city_avg
    FROM offers
    WHERE report_month = '2024-06' AND price_per_m2 IS NOT NULL
)
SELECT
    id, city, ROUND(price_per_m2, 2) AS price_per_m2,
    ROUND(city_avg, 2) AS city_avg,
    ROUND(100.0 * (city_avg - price_per_m2) / city_avg, 2) AS taniej_o_pct
FROM x
WHERE price_per_m2 < 0.8 * city_avg
ORDER BY taniej_o_pct DESC
LIMIT 50;
