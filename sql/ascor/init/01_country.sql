-- Country table for ASCOR database
CREATE TABLE country (
    country_name VARCHAR NOT NULL PRIMARY KEY,
    iso VARCHAR,
    region VARCHAR,
    bank_lending_group VARCHAR,
    imf_category VARCHAR,
    un_party_type VARCHAR
); 