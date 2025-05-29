-- Benchmark Projection table for TPI database
CREATE TABLE benchmark_projection (
    benchmark_projection_year INTEGER NOT NULL,
    benchmark_projection_attribute FLOAT,
    benchmark_id VARCHAR NOT NULL,
    sector_name VARCHAR NOT NULL,
    scenario_name VARCHAR NOT NULL,
    PRIMARY KEY (benchmark_projection_year, benchmark_id, sector_name, scenario_name),
    FOREIGN KEY (benchmark_id, sector_name, scenario_name) 
        REFERENCES sector_benchmark(benchmark_id, sector_name, scenario_name)
); 