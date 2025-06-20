-- Trend values table for ASCOR database
CREATE TABLE trend_values (
    trend_id INTEGER NOT NULL,
    country_name VARCHAR NOT NULL,
    year INTEGER NOT NULL,
    value FLOAT NOT NULL,
    PRIMARY KEY (trend_id, country_name, year),
    FOREIGN KEY (trend_id, country_name) REFERENCES assessment_trends(trend_id, country_name)
); 