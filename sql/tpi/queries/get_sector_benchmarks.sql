WITH latest_benchmarks AS (
    SELECT 
        sb.benchmark_id, 
        sb.sector_name, 
        sb.scenario_name, 
        sb.release_date, 
        sb.unit, 
        bp.benchmark_projection_year, 
        bp.benchmark_projection_attribute, 
        DENSE_RANK() OVER (PARTITION BY sb.sector_name ORDER BY release_date DESC) AS date_rank
    FROM sector_benchmark sb
    LEFT JOIN benchmark_projection bp 
    ON sb.benchmark_id = bp.benchmark_id
    AND sb.sector_name = bp.sector_name
    AND sb.scenario_name = bp.scenario_name
    WHERE sb.sector_name = :sector
)

SELECT 
    benchmark_id, 
    sector_name, 
    scenario_name, 
    release_date, 
    unit, 
    benchmark_projection_year, 
    benchmark_projection_attribute
FROM latest_benchmarks
WHERE date_rank = 1 
ORDER BY sector_name ASC, release_date DESC, benchmark_projection_year ASC;