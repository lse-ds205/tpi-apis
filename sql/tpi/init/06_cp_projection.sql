-- Carbon Performance Projection table for TPI database
CREATE TABLE cp_projection (
    cp_projection_year INTEGER NOT NULL,
    cp_projection_value INTEGER,
    assessment_date DATE NOT NULL,
    company_name VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    is_regional VARCHAR NOT NULL,
    PRIMARY KEY (cp_projection_year, assessment_date, company_name, version, is_regional),
    FOREIGN KEY (assessment_date, company_name, version, is_regional) 
        REFERENCES cp_assessment(assessment_date, company_name, version, is_regional)
); 