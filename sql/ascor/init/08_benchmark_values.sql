-- Benchmark values table for ASCOR database
CREATE TABLE benchmark_values (
    year INTEGER NOT NULL,
    benchmark_id INTEGER NOT NULL,
    value FLOAT NOT NULL,
    PRIMARY KEY (year, benchmark_id),
    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(benchmark_id)
); 