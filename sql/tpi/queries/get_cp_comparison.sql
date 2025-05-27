SELECT 
    c.company_name as company_id,
    MAX(CASE WHEN EXTRACT(YEAR FROM cp.assessment_date) = :year1 AND cp.cp_alignment_year = 2025 THEN cp.cp_alignment_value END) as latest_cp_2025,
    MAX(CASE WHEN EXTRACT(YEAR FROM cp.assessment_date) = :year2 AND cp.cp_alignment_year = 2025 THEN cp.cp_alignment_value END) as previous_cp_2025,
    MAX(CASE WHEN EXTRACT(YEAR FROM cp.assessment_date) = :year1 AND cp.cp_alignment_year = 2035 THEN cp.cp_alignment_value END) as latest_cp_2035,
    MAX(CASE WHEN EXTRACT(YEAR FROM cp.assessment_date) = :year2 AND cp.cp_alignment_year = 2035 THEN cp.cp_alignment_value END) as previous_cp_2035
FROM company c
JOIN cp_alignment cp ON c.company_name = cp.company_name
WHERE c.company_name = :company_id
    AND EXTRACT(YEAR FROM cp.assessment_date) IN (:year1, :year2)
GROUP BY c.company_name
HAVING COUNT(DISTINCT EXTRACT(YEAR FROM cp.assessment_date)) = 2; 