-- Assessment results table for ASCOR database
CREATE TABLE assessment_results (
    assessment_id INTEGER NOT NULL,
    code VARCHAR NOT NULL,
    response VARCHAR,
    assessment_date DATE NOT NULL,
    publication_date DATE,
    source VARCHAR,
    year INTEGER,
    country_name VARCHAR NOT NULL,
    PRIMARY KEY (assessment_id, code),
    FOREIGN KEY (country_name) REFERENCES country(country_name),
    FOREIGN KEY (code) REFERENCES assessment_elements(code)
); 