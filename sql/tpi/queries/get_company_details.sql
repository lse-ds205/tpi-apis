SELECT 
    c.company_name,
    c.geography,
    c.sector_name as sector,
    latest_mq.assessment_date,
    latest_mq.level,
    latest_mq.performance_change,
    latest_cp.cp_alignment_value as carbon_performance_alignment_2035
FROM company c
LEFT JOIN (
    SELECT DISTINCT ON (company_name, version) 
        company_name, version, assessment_date, level, performance_change
    FROM mq_assessment 
    ORDER BY company_name, version, assessment_date DESC
) latest_mq ON c.company_name = latest_mq.company_name AND c.version = latest_mq.version
LEFT JOIN (
    SELECT DISTINCT ON (company_name, version)
        company_name, version, cp_alignment_value
    FROM cp_alignment
    WHERE cp_alignment_year = 2035
    ORDER BY company_name, version, assessment_date DESC
) latest_cp ON c.company_name = latest_cp.company_name AND c.version = latest_cp.version
WHERE LOWER(c.company_name) = LOWER(:company_name)
LIMIT 1; 