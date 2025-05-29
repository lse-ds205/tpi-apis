-- Company answer table for TPI database
CREATE TABLE company_answer (
    question_code VARCHAR NOT NULL,
    company_name VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    question_text VARCHAR,
    response VARCHAR,
    PRIMARY KEY (question_code, company_name, version),
    FOREIGN KEY (company_name, version) REFERENCES company(company_name, version)
); 