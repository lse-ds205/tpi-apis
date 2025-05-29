WITH latest_assessments AS (
    SELECT 
        c.company_name,
        c.geography,
        c.sector_name as sector,
        c.version,
        mq.assessment_date as latest_mq_date,
        mq.level as management_quality_score,
        mq.performance_change as emissions_trend,
        cp.cp_alignment_value as carbon_performance_alignment_2035
    FROM company c
    LEFT JOIN LATERAL (
        SELECT 
            mq.assessment_date,
            mq.level,
            mq.performance_change
        FROM mq_assessment mq
        WHERE mq.company_name = c.company_name 
        AND mq.version = c.version
        ORDER BY mq.assessment_date DESC
        LIMIT 1
    ) mq ON true
    LEFT JOIN LATERAL (
        SELECT 
            cp.cp_alignment_value
        FROM cp_alignment cp
        WHERE cp.company_name = c.company_name 
        AND cp.version = c.version
        AND cp.cp_alignment_year = 2035
        ORDER BY cp.assessment_date DESC
        LIMIT 1
    ) cp ON true
    -- WHERE_CLAUSE_PLACEHOLDER
)
SELECT DISTINCT ON (company_name)
    company_name,
    geography,
    sector,
    latest_mq_date,
    management_quality_score,
    emissions_trend,
    carbon_performance_alignment_2035
FROM latest_assessments
ORDER BY company_name, latest_mq_date DESC NULLS LAST
LIMIT :limit OFFSET :offset; 