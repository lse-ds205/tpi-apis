-- Assessment elements table for ASCOR database
CREATE TABLE assessment_elements (
    code VARCHAR NOT NULL PRIMARY KEY,
    text VARCHAR NOT NULL,
    response_type VARCHAR NOT NULL,
    type VARCHAR NOT NULL
); 