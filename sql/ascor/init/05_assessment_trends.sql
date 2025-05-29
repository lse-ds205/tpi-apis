-- Assessment trends table for ASCOR database
CREATE TABLE assessment_trends (
    trend_id INTEGER NOT NULL,
    country_name VARCHAR NOT NULL,
    emissions_metric VARCHAR,
    emissions_boundary VARCHAR,
    units VARCHAR,
    assessment_date DATE,
    publication_date DATE,
    last_historical_year INTEGER,
    PRIMARY KEY (trend_id, country_name),
    FOREIGN KEY (country_name) REFERENCES country(country_name)
); 