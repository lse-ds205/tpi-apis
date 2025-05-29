-- Carbon Performance Assessment table for TPI database
CREATE TABLE cp_assessment (
    assessment_date DATE NOT NULL,
    company_name VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    is_regional VARCHAR NOT NULL,
    publication_date DATE,
    assumptions VARCHAR,
    cp_unit VARCHAR,
    projection_cutoff DATE,
    benchmark_id VARCHAR,
    PRIMARY KEY (assessment_date, company_name, version, is_regional),
    FOREIGN KEY (company_name, version) REFERENCES company(company_name, version)
); 