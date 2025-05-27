SELECT DISTINCT ON (c.company_name)
    c.company_name as company_id,
    c.company_name as name,
    c.sector_name as sector,
    c.geography,
    EXTRACT(YEAR FROM cp.assessment_date) as latest_assessment_year,
    MAX(CASE WHEN cp.cp_alignment_year = 2025 THEN cp.cp_alignment_value END) as carbon_performance_2025,
    MAX(CASE WHEN cp.cp_alignment_year = 2027 THEN cp.cp_alignment_value END) as carbon_performance_2027,
    MAX(CASE WHEN cp.cp_alignment_year = 2035 THEN cp.cp_alignment_value END) as carbon_performance_2035,
    MAX(CASE WHEN cp.cp_alignment_year = 2050 THEN cp.cp_alignment_value END) as carbon_performance_2050
FROM company c
JOIN cp_alignment cp ON c.company_name = cp.company_name
-- WHERE_CLAUSE_PLACEHOLDER
GROUP BY c.company_name, c.sector_name, c.geography, cp.assessment_date
ORDER BY c.company_name, cp.assessment_date DESC
LIMIT :limit OFFSET :offset; 