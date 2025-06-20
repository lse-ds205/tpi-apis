-- Benchmarks table for ASCOR database
CREATE TABLE benchmarks (
    benchmark_id INTEGER NOT NULL PRIMARY KEY,
    publication_date DATE,
    emissions_metric VARCHAR,
    emissions_boundary VARCHAR,
    units VARCHAR,
    benchmark_type VARCHAR,
    country_name VARCHAR,
    FOREIGN KEY (country_name) REFERENCES country(country_name)
); 