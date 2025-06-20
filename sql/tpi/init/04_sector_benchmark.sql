-- Sector benchmark table for TPI database
CREATE TABLE sector_benchmark (
    benchmark_id VARCHAR NOT NULL,
    sector_name VARCHAR NOT NULL,
    scenario_name VARCHAR NOT NULL,
    region VARCHAR,
    release_date DATE,
    unit VARCHAR,
    PRIMARY KEY (benchmark_id, sector_name, scenario_name)
); 