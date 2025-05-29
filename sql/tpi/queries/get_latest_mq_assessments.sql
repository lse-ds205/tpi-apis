SELECT DISTINCT ON (c.company_name)
    c.company_name as company_id,
    c.company_name as name,
    c.sector_name as sector,
    c.geography,
    EXTRACT(YEAR FROM mq.assessment_date) as latest_assessment_year,
    mq.level as management_quality_score
FROM company c
JOIN mq_assessment mq ON c.company_name = mq.company_name
-- WHERE_CLAUSE_PLACEHOLDER
ORDER BY c.company_name, mq.assessment_date DESC
LIMIT :limit OFFSET :offset; 