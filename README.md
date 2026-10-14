# Gans Data Pipeline

A small data pipeline for a fictional e-scooter company, Gans. It collects city, weather and flight data from public sources and stores it in MySQL, so scooter demand around airports and busy cities can be analysed.

**Blog post:** [Scraping, APIs and Cloud SQL: What My First Data Pipeline Taught Me](https://medium.com/@o.singh.phy/scraping-apis-and-cloud-sql-what-my-first-data-pipeline-taught-me-568787d87cd4?sharedUserId=o.singh.phy)

## Data

| Data | Source | Table |
|---|---|---|
| City, coordinates, country | Wikipedia (scraping) | `city` |
| Population and year | Wikipedia (scraping) | `population` |
| Airports within 50 km of a city | AeroDataBox (RapidAPI) | `city_icao` |
| 5-day / 3-hour weather forecast | OpenWeatherMap | `weather_forecast` |
| Tomorrow's arrivals and departures | AeroDataBox (RapidAPI) | `flight_status` |

## Project structure

```
.
├── notebooks/
│   ├── Gans_City.ipynb        # scrape cities and population, find nearby airports
│   ├── Gans_Weather.ipynb     # fetch weather forecasts for every city
│   └── Gans_Flight.ipynb      # fetch tomorrow's flights for every airport
├── sql/
│   ├── gans.sql               # database schema (local MySQL)
│   └── gans_cloud.sql         # database schema (cloud MySQL)
├── cloud_functions/
│   ├── city/                  # entry point: insert
│   ├── weather/               # entry point: insert_weather
│   └── flight/                # entry point: insert_flights
├── .env.example               # environment variables needed
└── .gitignore
```

## Database schema

```
city (city_id PK, name, latitude, longitude, country)
 ├── population (city_id FK, name, population, year)
 ├── weather_forecast (city_id FK, forecast_time, temperature, forecast,
 │                     rain_in_last_3h, wind_speed, data_retrieved_at)
 └── city_icao (city_id FK, icao, name)
flight_status (airport_icao, flight_num, direction, origin_icao,
               destination_icao, scheduled_time)
```

## Setup

1. Install the dependencies:
   ```bash
   pip install pandas requests beautifulsoup4 lat-long-parser sqlalchemy pymysql cryptography pytz python-dotenv
   ```
2. Create the tables by running `sql/gans.sql` (or `sql/gans_cloud.sql`) in MySQL.
3. Copy `.env.example` to `.env` and add your [OpenWeatherMap](https://openweathermap.org/api) and [RapidAPI](https://rapidapi.com/aedbx-aedbx/api/aerodatabox) keys. The notebooks ask for the MySQL password when they run.

## Run

Run the notebooks in this order, since each needs the tables filled by the one before:

1. `notebooks/Gans_City.ipynb` fills `city`, `population` and `city_icao`
2. `notebooks/Gans_Weather.ipynb` fills `weather_forecast`
3. `notebooks/Gans_Flight.ipynb` fills `flight_status`

To add cities, edit the `cities` list in `Gans_City.ipynb` (use the Wikipedia page name, e.g. `New_Delhi`).

## Cloud functions

Each folder in `cloud_functions/` is an HTTP-triggered Google Cloud Function (entry points: `insert`, `insert_weather`, `insert_flights`). They read `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_NAME` and the API keys (`api_key`, `rapid_api_key`) from environment variables. Deploy with `gcloud functions`, then schedule the calls with Cloud Scheduler.


