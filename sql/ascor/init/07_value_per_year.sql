-- Value per year table for ASCOR database
CREATE TABLE value_per_year (
    year INTEGER NOT NULL,
    value FLOAT NOT NULL,
    trend_id INTEGER NOT NULL,
    country_name VARCHAR NOT NULL,
    PRIMARY KEY (year, trend_id, country_name),
    FOREIGN KEY (trend_id, country_name) REFERENCES assessment_trends(trend_id, country_name)
); 