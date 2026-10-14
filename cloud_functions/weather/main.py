import os
from datetime import datetime
from urllib.parse import quote_plus

import pandas as pd
import requests
from pytz import timezone


def connection():
    """Build the SQLAlchemy connection string from environment variables."""
    user = os.environ["DB_USER"]
    password = quote_plus(os.environ["DB_PASSWORD"])   # escapes characters like '@'
    host = os.environ["DB_HOST"]
    schema = os.environ.get("DB_NAME", "gans")
    port = os.environ.get("DB_PORT", "3306")
    return f'mysql+pymysql://{user}:{password}@{host}:{port}/{schema}'


def get_cities(connection_string):
    return pd.read_sql('SELECT city_id, name, latitude, longitude FROM city',
                       con=connection_string)


def fetch_weather_forecast(city_id, lat, lon, api_key):
    """Get the 5-day / 3-hour forecast for one city as a list of dicts."""
    berlin_timezone = timezone('Europe/Berlin')
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
    )
    response.raise_for_status()
    forecast_json = response.json()
    retrieval_time = datetime.now(berlin_timezone).strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for item in forecast_json["list"]:
        rows.append({
            "city_id": city_id,
            "forecast_time": item.get("dt_txt"),
            "temperature": item["main"].get("temp"),
            "forecast": item["weather"][0].get("main"),
            "rain_in_last_3h": item.get("rain", {}).get("3h", 0),
            "wind_speed": item["wind"].get("speed"),
            "data_retrieved_at": retrieval_time,
        })
    return rows


def collect_forecasts(city_df, api_key):
    records = []
    for _, city in city_df.iterrows():
        records.extend(fetch_weather_forecast(
            city['city_id'], city['latitude'], city['longitude'], api_key))

    forecast_df = pd.DataFrame(records)
    forecast_df["forecast_time"] = pd.to_datetime(forecast_df["forecast_time"])
    forecast_df["data_retrieved_at"] = pd.to_datetime(forecast_df["data_retrieved_at"])
    return forecast_df


def save_forecasts(forecast_df, connection_string):
    return forecast_df.to_sql(name='weather_forecast', con=connection_string,
                              if_exists='append', index=False)


def insert_weather(request):
    """HTTP entry point: read cities, fetch forecasts, save them."""
    api_key = os.environ["api_key"]
    connection_string = connection()
    city_df = get_cities(connection_string)
    forecast_df = collect_forecasts(city_df, api_key)
    rows_saved = save_forecasts(forecast_df, connection_string)

    return f"Saved {rows_saved} weather rows"
