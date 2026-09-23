import sqlite3
import pandas as pd

def run_analysis():
    conn = sqlite3.connect('apartments_pl.sqlite')

    queries = {
        "1_Ranking_Miast_2024_06": """
            SELECT city, COUNT(*) AS n_offers, ROUND(AVG(price_per_m2), 2) AS avg_m2
            FROM offers
            WHERE report_month = '2024-06' AND price_per_m2 IS NOT NULL
            GROUP BY city
            ORDER BY avg_m2 DESC
        """,
        "2_Trend_Katowice": """
            SELECT report_month,
                   ROUND(AVG(price_per_m2), 2) AS avg_m2,
                   COUNT(*) AS n_offers
            FROM offers
            WHERE city = 'katowice' AND price_per_m2 IS NOT NULL
            GROUP BY report_month
            ORDER BY report_month
        """,
        "3_Zmiana_MoM_Katowice": """
            WITH m AS (
                SELECT report_month, AVG(price_per_m2) AS avg_m2
                FROM offers
                WHERE city = 'katowice' AND price_per_m2 IS NOT NULL
                GROUP BY report_month
            )
            SELECT
                report_month,
                ROUND(avg_m2, 2) AS avg_m2,
                ROUND(
                    100.0 * (avg_m2 - LAG(avg_m2) OVER (ORDER BY report_month)) /
                    NULLIF(LAG(avg_m2) OVER (ORDER BY report_month), 0), 2
                ) AS mom_change_pct
            FROM m
            ORDER BY report_month
        """,
        "4_Top20_Najdrozsze_Katowice": """
            SELECT id, squareMeters, rooms, price, ROUND(price_per_m2, 2) AS price_per_m2
            FROM offers
            WHERE report_month = '2024-06'
              AND city = 'katowice'
              AND price_per_m2 IS NOT NULL
            ORDER BY price_per_m2 DESC
            LIMIT 20
        """,
        "5_Cena_Wg_Pokoi_Katowice": """
            SELECT rooms,
                   COUNT(*) AS n,
                   ROUND(AVG(price_per_m2), 2) AS avg_m2
            FROM offers
            WHERE report_month = '2024-06'
              AND city = 'katowice'
              AND rooms IS NOT NULL
              AND price_per_m2 IS NOT NULL
            GROUP BY rooms
            ORDER BY rooms
        """,
        "6_Wplyw_Windy_Katowice": """
            SELECT hasElevator,
                   COUNT(*) AS n,
                   ROUND(AVG(price_per_m2), 2) AS avg_m2
            FROM offers
            WHERE city = 'katowice'
              AND hasElevator IS NOT NULL
              AND price_per_m2 IS NOT NULL
            GROUP BY hasElevator
        """,
        "7_Balkon_Parking_Katowice": """
            SELECT hasBalcony,
                   hasParkingSpace,
                   COUNT(*) AS n,
                   ROUND(AVG(price_per_m2), 2) AS avg_m2
            FROM offers
            WHERE report_month = '2024-06'
              AND city = 'katowice'
              AND price_per_m2 IS NOT NULL
              AND hasBalcony IS NOT NULL
              AND hasParkingSpace IS NOT NULL
            GROUP BY hasBalcony, hasParkingSpace
            ORDER BY avg_m2 DESC
        """,
        "8_Odleglosc_Od_Centrum": """
            SELECT
                CASE
                    WHEN centreDistance < 2  THEN '1_ponizej_2km'
                    WHEN centreDistance < 5  THEN '2_od_2_do_5km'
                    WHEN centreDistance < 10 THEN '3_od_5_do_10km'
                    ELSE                          '4_powyzej_10km'
                END AS strefa,
                COUNT(*) AS n,
                ROUND(AVG(price_per_m2), 2) AS avg_m2
            FROM offers
            WHERE report_month = '2024-06'
              AND city = 'katowice'
              AND price_per_m2 IS NOT NULL
              AND centreDistance IS NOT NULL
            GROUP BY strefa
            ORDER BY strefa
        """,
        "9_Rok_Budowy_Katowice": """
            SELECT
                CASE
                    WHEN buildYear IS NULL   THEN '0_nieznany'
                    WHEN buildYear < 1945    THEN '1_przed_1945'
                    WHEN buildYear < 1970    THEN '2_1945_1969'
                    WHEN buildYear < 1990    THEN '3_1970_1989'
                    WHEN buildYear < 2010    THEN '4_1990_2009'
                    ELSE                          '5_2010_plus'
                END AS rocznik,
                COUNT(*) AS n,
                ROUND(AVG(price_per_m2), 2) AS avg_m2
            FROM offers
            WHERE city = 'katowice' AND price_per_m2 IS NOT NULL
            GROUP BY rocznik
            ORDER BY rocznik
        """,
        "10_Outliery_Usuniete": """
            SELECT city, COUNT(*) AS n, ROUND(AVG(price_per_m2), 2) AS avg_m2
            FROM offers
            WHERE report_month = '2024-06'
              AND price_per_m2 BETWEEN 2000 AND 40000
            GROUP BY city
            ORDER BY avg_m2 DESC
        """,
        "11_Okazje_20pct_Ponizej_Sredniej": """
            WITH x AS (
                SELECT
                    id, city, squareMeters, rooms, price, price_per_m2,
                    AVG(price_per_m2) OVER (PARTITION BY city) AS city_avg
                FROM offers
                WHERE report_month = '2024-06' AND price_per_m2 IS NOT NULL
            )
            SELECT
                id, city, squareMeters, rooms, price,
                ROUND(price_per_m2, 2) AS price_per_m2,
                ROUND(city_avg, 2) AS city_avg,
                ROUND(100.0 * (city_avg - price_per_m2) / city_avg, 2) AS taniej_o_pct
            FROM x
            WHERE price_per_m2 < 0.8 * city_avg
            ORDER BY taniej_o_pct DESC
            LIMIT 50
        """,
        "12_Typ_Budynku_Katowice": """
            SELECT type,
                   COUNT(*) AS n,
                   ROUND(AVG(price_per_m2), 2) AS avg_m2
            FROM offers
            WHERE report_month = '2024-06'
              AND city = 'katowice'
              AND type IS NOT NULL
              AND price_per_m2 IS NOT NULL
            GROUP BY type
            ORDER BY n DESC
        """,
        "13_Liczba_Ofert_Per_Miesiac": """
            SELECT report_month, city, COUNT(*) AS n_offers
            FROM offers
            GROUP BY report_month, city
            ORDER BY report_month, n_offers DESC
        """,
        "14_Najdrozsze_Miasta_Wszystkie_Miesiace": """
            SELECT city,
                   ROUND(AVG(price_per_m2), 2) AS avg_m2_all,
                   COUNT(*) AS n
            FROM offers
            WHERE price_per_m2 IS NOT NULL
            GROUP BY city
            HAVING n >= 1000
            ORDER BY avg_m2_all DESC
        """,
        "15_Mediana_Katowice_2024_06": """
            WITH s AS (
                SELECT price_per_m2
                FROM offers
                WHERE report_month = '2024-06'
                  AND city = 'katowice'
                  AND price_per_m2 IS NOT NULL
                ORDER BY price_per_m2
            ),
            c AS (SELECT COUNT(*) AS n FROM s)
            SELECT
                ROUND(
                    (SELECT price_per_m2 FROM s
                     LIMIT 1 OFFSET (SELECT (n - 1) / 2 FROM c)),
                2) AS mediana_m2
        """
    }

    with pd.ExcelWriter('Raport_Mieszkania_2024.xlsx', engine='openpyxl') as writer:
        for name, sql in queries.items():
            df = pd.read_sql_query(sql, conn)
            # Nazwa arkusza max 31 znaków (limit Excela)
            sheet = name[:31]
            df.to_excel(writer, sheet_name=sheet, index=False)
            print(f"Zakończono: {name}")

    conn.close()
    print("\nRaport gotowy! Otwórz plik: Raport_Mieszkania_2024.xlsx")

if __name__ == "__main__":
    run_analysis()
