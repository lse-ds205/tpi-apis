SELECT 
    cp.company_name as company_id,
    cp.company_name as name,
    MAX(c.sector_name) as sector,
    MAX(c.geography) as geography,
    EXTRACT(YEAR FROM cp.assessment_date) as latest_assessment_year,
    MAX(CASE WHEN cp.cp_alignment_year = 2025 THEN cp.cp_alignment_value END) as carbon_performance_2025,
    MAX(CASE WHEN cp.cp_alignment_year = 2027 THEN cp.cp_alignment_value END) as carbon_performance_2027,
    MAX(CASE WHEN cp.cp_alignment_year = 2035 THEN cp.cp_alignment_value END) as carbon_performance_2035,
    MAX(CASE WHEN cp.cp_alignment_year = 2050 THEN cp.cp_alignment_value END) as carbon_performance_2050
FROM cp_alignment cp
JOIN company c ON cp.company_name = c.company_name AND cp.version = c.version
WHERE LOWER(cp.company_name) = LOWER(:company_id)
GROUP BY cp.company_name, cp.assessment_date
ORDER BY cp.assessment_date DESC; 