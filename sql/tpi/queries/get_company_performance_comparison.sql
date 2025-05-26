SELECT 
    mq.assessment_date,
    mq.level,
    cp_align.cp_alignment_value as carbon_performance_alignment_2035,
    EXTRACT(YEAR FROM mq.assessment_date) as assessment_year
FROM company c
JOIN mq_assessment mq ON c.company_name = mq.company_name AND c.version = mq.version
LEFT JOIN cp_alignment cp_align ON c.company_name = cp_align.company_name 
    AND c.version = cp_align.version 
    AND mq.assessment_date = cp_align.assessment_date
WHERE LOWER(c.company_name) = LOWER(:company_name)
ORDER BY mq.assessment_date DESC
LIMIT 2; 