SELECT 
    ar.assessment_id,
    ar.code,
    ar.response,
    ar.assessment_date,
    ar.publication_date,
    ar.source,
    ar.year,
    ar.country_name,
    ae.text as element_text,
    ae.response_type,
    ae.type as element_type
FROM assessment_results ar
JOIN assessment_elements ae ON ar.code = ae.code
JOIN country c ON ar.country_name = c.country_name
WHERE LOWER(c.country_name) = LOWER(:country_name)
AND EXTRACT(YEAR FROM ar.assessment_date) = :assessment_year
ORDER BY ar.code; 