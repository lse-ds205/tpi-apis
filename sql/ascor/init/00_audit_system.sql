-- audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    execution_id SERIAL PRIMARY KEY,
    execution_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_user VARCHAR(255) DEFAULT CURRENT_USER,
    process VARCHAR(255) NOT NULL,
    execution_status VARCHAR(50) NOT NULL,
    execution_notes TEXT,
    table_name VARCHAR(255),
    source_file VARCHAR(1024),
    rows_inserted INTEGER
); 