SELECT sb.benchmark_id, sb.sector_name, sb.scenario_name, sb.region, sb.release_date, sb.unit, bp.benchmark_projection_year, bp.benchmark_projection_attribute
FROM sector_benchmark sb
LEFT JOIN benchmark_projection bp 
ON sb.benchmark_id = bp.benchmark_id
AND sb.sector_name = bp.sector_name
AND sb.scenario_name = bp.scenario_name
WHERE sb.sector_name = :sector
ORDER BY sb.benchmark_id DESC, release_date DESC, benchmark_projection_year ASC