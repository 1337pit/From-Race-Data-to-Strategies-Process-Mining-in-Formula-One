"""Download, transform, and export FastF1 lap data."""

import csv
import os
import tempfile
from pathlib import Path

import fastf1
import pandas as pd


YEAR = 2025
GRAND_PRIX = "British Grand Prix"
SESSION_TYPE = "R"
OUTPUT_DIR = Path("silverstone_2025")


def has_value(series):
    return series.notna() & series.astype("string").str.strip().ne("").fillna(False)


def stint_activity(value):
    if pd.isna(value):
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number.is_integer():
        return f"Stint_{int(number)}"
    return f"Stint_{number}"


def prepare_laps(laps):
    columns = [
        "Driver",
        "DriverNumber",
        "Team",
        "LapNumber",
        "LapTime",
        "LapStartTime",
        "Time",
        "Sector1Time",
        "Sector2Time",
        "Sector3Time",
        "Compound",
        "TyreLife",
        "FreshTyre",
        "Stint",
        "PitOutTime",
        "PitInTime",
        "TrackStatus",
        "IsPersonalBest",
    ]
    available_columns = [column for column in columns if column in laps.columns]
    required_columns = {"Driver", "LapNumber", "Stint", "PitInTime", "PitOutTime"}
    missing_columns = required_columns.difference(available_columns)
    if missing_columns:
        raise ValueError(
            "FastF1 laps are missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    df = laps[available_columns].rename(columns={"Time": "StintEndTime"}).copy()
    df = df.sort_values(
        by=["Driver", "LapNumber"], na_position="last", kind="stable"
    ).reset_index(drop=True)
    df["Activity"] = df["Stint"].map(stint_activity)

    pit_in = has_value(df["PitInTime"])
    pit_out = has_value(df["PitOutTime"])

    df.loc[pit_in, "Activity"] = "Pit In"
    df.loc[pit_out, "Activity"] = "Pit Out"

    return df.reset_index(drop=True)


def aggregate_stints(laps):
    is_stint = laps["Activity"].str.fullmatch(
        r"Stint_\d+(?:\.\d+)?", na=False
    )
    stint_rows = laps.loc[is_stint]
    aggregated_stints = []
    for _, group in stint_rows.groupby(["Driver", "Activity"], sort=False):
        last_lap = group.iloc[[-1]].copy()
        last_lap.loc[:, "LapStartTime"] = group.iloc[0]["LapStartTime"]
        aggregated_stints.append(last_lap)

    return pd.concat(
        [laps.loc[~is_stint], *aggregated_stints],
        ignore_index=True,
    ).sort_values(
        by=["Driver", "LapNumber"],
        na_position="last",
        kind="stable",
    ).reset_index(drop=True)


def normalize_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames
        if not fieldnames or "Activity" not in fieldnames:
            raise ValueError("CSV does not contain an Activity column")
        rows = list(reader)

    for row in rows:
        for column, value in row.items():
            row[column] = (value or "").replace("0 days ", "")
        activity = row["Activity"].strip().casefold()
        if activity == "pit in":
            row["Activity"] = "Pit In"
        elif activity == "pit out":
            row["Activity"] = "Pit Out"

    fd, temp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as destination:
            writer = csv.DictWriter(
                destination, fieldnames=fieldnames, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_name, path)
    except Exception:
        if os.path.exists(temp_name):
            os.remove(temp_name)
        raise


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cache_dir = OUTPUT_DIR / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.configure(cache_dir=str(cache_dir))

    print("Recupero della sessione...")
    session = fastf1.get_session(YEAR, GRAND_PRIX, SESSION_TYPE)
    session.load(telemetry=False, weather=False, messages=False)

    print(f"Evento: {session.event['EventName']}")
    print(f"Sessione: {session.name}")
    print(f"\nNumero di giri recuperati: {len(session.laps)}")

    df = prepare_laps(session.laps)
    aggregated_df = aggregate_stints(df)
    detailed_csv = OUTPUT_DIR / "silverstone_2025_laps.csv"
    aggregated_csv = (
        OUTPUT_DIR / "silverstone_2025_laps_stints_aggregated.csv"
    )
    df.to_csv(detailed_csv, index=False)
    aggregated_df.to_csv(aggregated_csv, index=False)
    normalize_csv(detailed_csv)
    normalize_csv(aggregated_csv)

    print(f"\nCSV con attività estese salvato in: {detailed_csv.resolve()}")
    print(f"CSV con stint aggregati salvato in: {aggregated_csv.resolve()}")
    print("\nPiloti presenti:")
    print(sorted(df["Driver"].dropna().unique()))
    print("\nColonne esportate:")
    print(df.columns.tolist())
    print("\nPrime righe del dataset:")
    print(df.head(10).to_string(index=False))
    print("\nNumero di stint registrati per pilota:")
    print(
        aggregated_df.groupby("Driver")["Stint"]
        .nunique()
        .sort_values(ascending=False)
    )
    print("\nAttività esportate:")
    print(df["Activity"].value_counts(dropna=False).sort_index())
    print("\nDownload, trasformazione ed esportazione completati.")


if __name__ == "__main__":
    main()
