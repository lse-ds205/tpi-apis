WITH all_cp_projection_info AS (
    SELECT 
        ca.assessment_date, 
        ca.benchmark_id, 
        ca.company_name, 
        c.sector_name, 
        ca.cp_unit, 
        ca.version, 
        cp.cp_projection_year, 
        cp.cp_projection_value, 
        DENSE_RANK() OVER (PARTITION BY ca.company_name ORDER BY ca.version DESC) AS version_rank, 
        DENSE_RANK() OVER (PARTITION BY ca.company_name ORDER BY ca.assessment_date DESC) AS recency_rank 
    FROM cp_assessment ca
    LEFT JOIN cp_projection cp
    ON ca.assessment_date = cp.assessment_date
    AND ca.company_name = cp.company_name
    AND ca.version = cp.version
    AND ca.is_regional = cp.is_regional
    LEFT JOIN company c
    ON ca.company_name = c.company_name
    AND ca.version = c.version
) 

SELECT 
    assessment_date, 
    benchmark_id, 
    company_name, 
    sector_name, 
    cp_unit, 
    cp_projection_year, 
    cp_projection_value
FROM all_cp_projection_info
WHERE version_rank = 1 AND recency_rank = 1
ORDER BY company_name ASC, assessment_date DESC, cp_projection_year ASC;