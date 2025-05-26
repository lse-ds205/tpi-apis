SELECT 
    c.company_name,
    c.geography,
    c.sector_name as sector,
    mq.assessment_date,
    mq.level,
    mq.performance_change,
    cp_align.cp_alignment_value as carbon_performance_alignment_2035
FROM company c
JOIN mq_assessment mq ON c.company_name = mq.company_name AND c.version = mq.version
LEFT JOIN cp_alignment cp_align ON c.company_name = cp_align.company_name 
    AND c.version = cp_align.version 
    AND mq.assessment_date = cp_align.assessment_date
WHERE LOWER(c.company_name) = LOWER(:company_name)
ORDER BY mq.assessment_date DESC; 