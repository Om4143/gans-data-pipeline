CREATE DATABASE IF NOT EXISTS gans;
USE gans;

-- DESCRIBE city;
-- DESCRIBE population;
-- ALTER TABLE city;
 -- DROP TABLE city;
 -- DROP TABLE population;
 -- DROP TABLE weather_forecast;
 -- DROP TABLE city_icao;
 -- DROP TABLE flight_status

CREATE TABLE IF NOT EXISTS city(
    city_id INT AUTO_INCREMENT, -- Automatically generated ID for each city
    name VARCHAR(255) NOT NULL, -- Name of the city
    latitude FLOAT,   -- latitude
    longitude FLOAT,  -- lonitude
    country VARCHAR(255),    -- country name
    PRIMARY KEY (city_id) -- Primary key to uniquely identify each author
);

-- Create the 'population' table
CREATE TABLE IF NOT EXISTS population (
    #population_id INT AUTO_INCREMENT, -- Automatically generated ID for each year of population
    city_id INT,
    name VARCHAR(255),
    population VARCHAR(255), -- population
    year INT, -- year when population is retrieve.
   # PRIMARY KEY (population_id), -- Primary key to uniquely identify each population year
    FOREIGN KEY (city_id) REFERENCES city(city_id) -- Foreign key to connect each city to its population
);

CREATE TABLE IF NOT EXISTS weather_forecast (
	city_id INT,
	forecast_time DATETIME,
	temperature FLOAT,
	forecast VARCHAR(255),
	rain_in_last_3h FLOAT,
	wind_speed FLOAT,
	data_retrieved_at DATETIME,
	FOREIGN KEY (city_id) REFERENCES city(city_id)
);


CREATE TABLE IF NOT EXISTS city_icao (
	city_id INT,
    icao VARCHAR(255),
    name VARCHAR(255),
    FOREIGN KEY (city_id) REFERENCES city(city_id)
);

CREATE TABLE IF NOT EXISTS flight_status (
    airport_icao VARCHAR(10),       -- airport the flights were looked up for
    flight_num VARCHAR(20),         -- e.g. 'LH 400'
    direction VARCHAR(10),          -- 'departure' or 'arrival'
    origin_icao VARCHAR(10),        -- where the flight leaves from
    destination_icao VARCHAR(10),   -- where the flight lands
    scheduled_time DATETIME,        -- scheduled local time
    INDEX (airport_icao)
);
