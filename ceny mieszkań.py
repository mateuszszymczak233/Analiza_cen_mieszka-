import re
from pathlib import Path

import numpy as np
import pandas as pd
import sqlite3


def month_from_filename(name: str) -> str:
    
    m = re.search(r"apartments_pl_(\d{4})_(\d{2})\.csv$", name)
    if not m:
        raise ValueError(f"Unexpected filename format: {name}")
    return f"{m.group(1)}-{m.group(2)}"


def to_bool_series(s: pd.Series) -> pd.Series:

    if s is None:
        return pd.Series([pd.NA] * 0, dtype="Int64")
    x = s.astype(str).str.strip().str.lower()
    x = x.replace({"nan": pd.NA, "none": pd.NA, "": pd.NA})
    mapped = x.map({
        "yes": 1, "no": 0,
        "true": 1, "false": 0,
        "1": 1, "0": 0
    })
    return mapped.astype("Int64")


def main():
    search_dirs = [Path("."), Path("./Uploads")]
    files = []
    for d in search_dirs:
        files.extend(sorted(d.glob("apartments_pl_*.csv")))

    uniq = {}
    for f in files:
        uniq[f.name] = f
    files = [uniq[k] for k in sorted(uniq.keys())]

    if not files:
        raise FileNotFoundError("No apartments_pl_*.csv files found in . or ./Uploads")

    frames = []
    for f in files:
        month = month_from_filename(f.name)
        df = pd.read_csv(f)

        df["report_month"] = month

        frames.append(df)

    all_df = pd.concat(frames, ignore_index=True)

    if "id" in all_df.columns:
        all_df["id"] = all_df["id"].astype(str)

    num_cols = [
        "squareMeters", "rooms", "floor", "floorCount", "buildYear",
        "latitude", "longitude", "centreDistance", "poiCount",
        "schoolDistance", "clinicDistance", "postOfficeDistance",
        "kindergartenDistance", "restaurantDistance", "collegeDistance",
        "pharmacyDistance", "price"
    ]
    for c in num_cols:
        if c in all_df.columns:
            all_df[c] = pd.to_numeric(all_df[c], errors="coerce")

    bool_cols = [
        "hasParkingSpace", "hasBalcony", "hasElevator",
        "hasSecurity", "hasStorageRoom"
    ]
    for c in bool_cols:
        if c in all_df.columns:
            all_df[c] = to_bool_series(all_df[c])

    text_cols = ["city", "type", "ownership", "buildingMaterial", "condition", "report_month"]
    for c in text_cols:
        if c in all_df.columns:
            all_df[c] = all_df[c].astype(str).str.strip()
            all_df[c] = all_df[c].replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})

    if "price" in all_df.columns and "squareMeters" in all_df.columns:
        all_df["price_per_m2"] = all_df["price"] / all_df["squareMeters"]
        all_df.loc[all_df["squareMeters"] <= 0, "price_per_m2"] = np.nan

    if "price" in all_df.columns:
        all_df = all_df[(all_df["price"].isna()) | (all_df["price"] > 0)]
    if "squareMeters" in all_df.columns:
        all_df = all_df[(all_df["squareMeters"].isna()) | (all_df["squareMeters"] > 0)]

    db_name = "apartments_pl.sqlite"
    conn = sqlite3.connect(db_name)

    all_df.to_sql("offers", conn, if_exists="replace", index=False)

    cur = conn.cursor()
    idx_statements = [
        "CREATE INDEX IF NOT EXISTS idx_offers_city ON offers(city);",
        "CREATE INDEX IF NOT EXISTS idx_offers_month ON offers(report_month);",
        "CREATE INDEX IF NOT EXISTS idx_offers_city_month ON offers(city, report_month);",
        "CREATE INDEX IF NOT EXISTS idx_offers_price_per_m2 ON offers(price_per_m2);",
        "CREATE INDEX IF NOT EXISTS idx_offers_rooms ON offers(rooms);",
    ]
    for stmt in idx_statements:
        try:
            cur.execute(stmt)
        except Exception as e:
            print("Index creation failed:", stmt, e)

    n = cur.execute("SELECT COUNT(*) FROM offers;").fetchone()[0]
    cities = cur.execute("SELECT COUNT(DISTINCT city) FROM offers;").fetchone()[0]
    months = cur.execute("SELECT COUNT(DISTINCT report_month) FROM offers;").fetchone()[0]
    sample = cur.execute(
        "SELECT id, city, report_month, squareMeters, rooms, price, price_per_m2 "
        "FROM offers WHERE price IS NOT NULL LIMIT 5;"
    ).fetchall()

    conn.commit()
    conn.close()

    print(f"Saved SQLite DB: {db_name}")
    print(f"Rows: {n:,} | Distinct cities: {cities} | Distinct months: {months}")
    print("Sample rows:")
    for r in sample:
        print(r)


if __name__ == "__main__":
    main()
