import os
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
from lat_lon_parser import parse
from urllib.parse import quote_plus

CITIES = ['Berlin', 'Hamburg', 'New_Delhi']


def connection():
    """Build the SQLAlchemy connection string from environment variables."""
    user = os.environ["DB_USER"]
    password = quote_plus(os.environ["DB_PASSWORD"])   # escapes characters like '@'
    host = os.environ["DB_HOST"]
    schema = os.environ.get("DB_NAME", "gans")
    port = os.environ.get("DB_PORT", "3306")
    return f'mysql+pymysql://{user}:{password}@{host}:{port}/{schema}'


def info(city='Berlin'):
    """Scrape one city's Wikipedia page for its details."""
    url = 'https://en.wikipedia.org/wiki/' + city
    headers = {'User-Agent': 'Chrome/134.0.0.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    city = soup.find(class_='mw-page-title-main').get_text()
    latitude = soup.find_all(class_='latitude')[0].get_text()
    longitude = soup.find_all(class_='longitude')[0].get_text()
    country = soup.find_all(class_='infobox-data')[0].get_text()

    population = None
    year = None
    for header in soup.find_all('th', class_='infobox-header'):
        if header.get_text(strip=True).startswith('Population'):
            year = re.search(r'\d{4}', header.get_text(strip=True)).group()
            row = header.find_parent('tr')
            next_row = row.find_next_sibling('tr')
            population = next_row.find('td').get_text(strip=True)
            break

    return city, latitude, longitude, country, population, year


def collect_cities(cities):
    """Scrape every city and return the city and population DataFrames."""
    city_d = {}
    population_d = {}

    for i in cities:
        city, latitude, longitude, country, population, year = info(i)
        city_d[i] = {
            'latitude': parse(latitude),
            'longitude': parse(longitude),
            'country': country,
        }
        population_d[i] = {'population': population, 'year': year}

    city_df = pd.DataFrame(city_d).T.reset_index().rename(columns={'index': 'name'})
    population_df = pd.DataFrame(population_d).T.reset_index().rename(columns={'index': 'name'})
    return city_df, population_df


def save_cities(city_df, connection_string):
    return city_df.to_sql('city', if_exists='append', con=connection_string, index=False)


def save_population(population_df, connection_string):
    city_lookup = pd.read_sql('SELECT city_id, name FROM city', con=connection_string)
    population_df_final = population_df.merge(city_lookup, on='name', how='left')
    return population_df_final.to_sql('population', if_exists='append',
                                      con=connection_string, index=False)


def get_cities(connection_string):
    return pd.read_sql('SELECT city_id, name, latitude, longitude FROM city',
                       con=connection_string)


def fetch_nearby_airports(city_id, lat, lon, api_key):
    """Find airports within 50 km of one city as a list of dicts."""
    response = requests.get(
        "https://aerodatabox.p.rapidapi.com/airports/search/location",
        headers={"x-rapidapi-key": api_key, "x-rapidapi-host": "aerodatabox.p.rapidapi.com"},
        params={"withFlightInfoOnly": True, "radiusKm": 50, "limit": 10, "lat": lat, "lon": lon},
    )
    if response.status_code == 204:
        return []
    response.raise_for_status()

    return [{"city_id": city_id, "icao": item["icao"], "name": item["name"]}
            for item in response.json()["items"]]


def collect_airports(city_df, api_key):
    records = []
    for _, city in city_df.iterrows():
        records.extend(fetch_nearby_airports(
            city['city_id'], city['latitude'], city['longitude'], api_key))
    return pd.DataFrame(records)


def save_airports(airport_df, connection_string):
    return airport_df.to_sql(name='city_icao', con=connection_string,
                             if_exists='append', index=False)


def insert(request):
    """HTTP entry point: scrape cities, save city and population rows, save nearby airports."""
    city_df, population_df = collect_cities(CITIES)
    connection_string = connection()
    save_cities(city_df, connection_string)
    save_population(population_df, connection_string)
    city_id_df = get_cities(connection_string)
    api_key = os.environ["rapid_api_key"]

    airport_df = collect_airports(city_id_df, api_key)
    save_airports(airport_df, connection_string)

    return "Data successfully added"
