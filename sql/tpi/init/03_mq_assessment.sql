-- Management Quality Assessment table for TPI database
CREATE TABLE mq_assessment (
    assessment_date DATE NOT NULL,
    company_name VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    tpi_cycle INTEGER NOT NULL,
    publication_date DATE,
    level VARCHAR,
    performance_change VARCHAR,
    PRIMARY KEY (assessment_date, company_name, version, tpi_cycle),
    FOREIGN KEY (company_name, version) REFERENCES company(company_name, version)
); 