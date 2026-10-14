import os
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import pandas as pd
import requests


def connection():
    """Build the SQLAlchemy connection string from environment variables."""
    user = os.environ["DB_USER"]
    password = quote_plus(os.environ["DB_PASSWORD"])   # escapes characters like '@'
    host = os.environ["DB_HOST"]
    schema = os.environ.get("DB_NAME", "gans")
    port = os.environ.get("DB_PORT", "3306")
    return f'mysql+pymysql://{user}:{password}@{host}:{port}/{schema}'


def get_airport(connection_string):
    return pd.read_sql('SELECT city_id, icao, name FROM city_icao', con=connection_string)


def fetch_flights(icao, api_key):
    """Get tomorrow's departures and arrivals for one airport as a list of dicts."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    times = [("00:00", "11:59"), ("12:00", "23:59")]   # API allows max 12 hours per request

    rows = []
    for start, end in times:
        from_local = f"{tomorrow}T{start}"
        to_local = f"{tomorrow}T{end}"
        response = requests.get(
            f"https://aerodatabox.p.rapidapi.com/flights/airports/icao/{icao}/{from_local}/{to_local}",
            headers={"x-rapidapi-key": api_key, "x-rapidapi-host": "aerodatabox.p.rapidapi.com"},
            params={"withCancelled": "false", "withCodeshared": "true",
                    "withCargo": "false", "withPrivate": "false"},
        )
        if response.status_code == 204:
            continue
        if response.status_code != 200:
            print(f"{icao}: {from_local} -> {to_local}: status code {response.status_code}")
            continue

        flight_json = response.json()
        for depart in flight_json.get("departures", []):
            rows.append({
                "airport_icao": icao,
                "flight_num": depart.get("number"),
                "direction": "departure",
                "origin_icao": icao,
                "destination_icao": depart["movement"]["airport"].get("icao"),
                "scheduled_time": depart["movement"].get("scheduledTime", {}).get("local"),
            })
        for arriv in flight_json.get("arrivals", []):
            rows.append({
                "airport_icao": icao,
                "flight_num": arriv.get("number"),
                "direction": "arrival",
                "origin_icao": arriv["movement"]["airport"].get("icao"),
                "destination_icao": icao,
                "scheduled_time": arriv["movement"].get("scheduledTime", {}).get("local"),
            })
    return rows


def collect_flights(airport_df, api_key):
    records = []
    for icao in airport_df['icao'].unique():
        records.extend(fetch_flights(icao, api_key))

    flight_df = pd.DataFrame(records).drop_duplicates()
    # local times look like "2026-09-29 08:15+02:00" — keep the local clock time
    flight_df["scheduled_time"] = pd.to_datetime(flight_df["scheduled_time"].str[:16])
    return flight_df


def save_flights(flight_df, connection_string):
    return flight_df.to_sql(name='flight_status', con=connection_string,
                            if_exists='append', index=False)


def insert_flights(request):
    """HTTP entry point: read airports, fetch tomorrow's flights, save them."""
    api_key = os.environ["rapid_api_key"]
    connection_string = connection()
    airport_df = get_airport(connection_string)
    flight_df = collect_flights(airport_df, api_key)
    rows_saved = save_flights(flight_df, connection_string)

    return f"Saved {rows_saved} flight rows"
