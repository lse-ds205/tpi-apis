SELECT 
    mq.company_name,
    c.geography,
    c.sector_name as sector,
    mq.assessment_date,
    mq.level,
    mq.performance_change,
    cp_align.cp_alignment_value as carbon_performance_alignment_2035
FROM mq_assessment mq
JOIN company c ON mq.company_name = c.company_name AND mq.version = c.version
LEFT JOIN cp_alignment cp_align ON mq.company_name = cp_align.company_name 
    AND mq.version = cp_align.version 
    AND cp_align.cp_alignment_year = 2035
WHERE LOWER(mq.company_name) = LOWER(:company_name)
    AND (mq.assessment_date, mq.version) = (
        SELECT assessment_date, MAX(version)
        FROM mq_assessment 
        WHERE LOWER(company_name) = LOWER(:company_name)
            AND assessment_date = (
                SELECT MAX(assessment_date) 
                FROM mq_assessment 
                WHERE LOWER(company_name) = LOWER(:company_name)
            )
        GROUP BY assessment_date
    )
ORDER BY mq.assessment_date DESC; 