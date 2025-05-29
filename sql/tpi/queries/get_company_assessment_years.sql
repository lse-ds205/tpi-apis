SELECT DISTINCT EXTRACT(YEAR FROM mq.assessment_date) as year
FROM company c
JOIN mq_assessment mq ON c.company_name = mq.company_name AND c.version = mq.version
WHERE LOWER(c.company_name) = LOWER(:company_name) -- WHERE_CLAUSE_PLACEHOLDER
ORDER BY year DESC; 