-- Company table for TPI database
CREATE TABLE company (
    company_name VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    geography VARCHAR,
    isin VARCHAR,
    ca100_focus VARCHAR,
    size_classification VARCHAR,
    geography_code VARCHAR,
    sedol VARCHAR,
    sector_name VARCHAR,
    PRIMARY KEY (company_name, version)
); 