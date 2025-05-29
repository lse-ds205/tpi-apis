-- Carbon Performance Alignment table for TPI database
CREATE TABLE cp_alignment (
    cp_alignment_year INTEGER NOT NULL,
    cp_alignment_value VARCHAR,
    assessment_date DATE NOT NULL,
    company_name VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    is_regional VARCHAR NOT NULL,
    PRIMARY KEY (cp_alignment_year, assessment_date, company_name, version, is_regional),
    FOREIGN KEY (assessment_date, company_name, version, is_regional) 
        REFERENCES cp_assessment(assessment_date, company_name, version, is_regional)
); 