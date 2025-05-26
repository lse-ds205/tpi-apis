from models import AscorBase, TpiBase, logger
from utils.database_creation_utils import get_engine
from sqlalchemy import text

def create_tables(db_name: str) -> None:
    """
    Create all tables in the specified database, dropping existing ones first
    Args:
        db_name: Name of the database to create tables in
    """
    try:
        engine = get_engine(db_name)
        # Drop tables in correct order to handle dependencies
        with engine.connect() as conn:
            if db_name == "ascor_api":
                # Drop ASCOR tables
                conn.execute(text("""
                    DROP TABLE IF EXISTS value_per_year CASCADE;
                    DROP TABLE IF EXISTS trend_values CASCADE;
                    DROP TABLE IF EXISTS assessment_trends CASCADE;
                    DROP TABLE IF EXISTS assessment_results CASCADE;
                    DROP TABLE IF EXISTS assessment_elements CASCADE;
                    DROP TABLE IF EXISTS benchmark_values CASCADE;
                    DROP TABLE IF EXISTS benchmarks CASCADE;
                    DROP TABLE IF EXISTS country CASCADE;
                """))
                conn.commit()
                AscorBase.metadata.create_all(engine)
            elif db_name == "tpi_api":
                # Drop TPI tables
                conn.execute(text("""
                    DROP TABLE IF EXISTS cp_projection CASCADE;
                    DROP TABLE IF EXISTS cp_alignment CASCADE;
                    DROP TABLE IF EXISTS cp_assessment CASCADE;
                    DROP TABLE IF EXISTS mq_assessment CASCADE;
                    DROP TABLE IF EXISTS company_answer CASCADE;
                    DROP TABLE IF EXISTS company CASCADE;
                    DROP TABLE IF EXISTS benchmark_projection CASCADE;
                    DROP TABLE IF EXISTS sector_benchmark CASCADE;
                """))
                conn.commit()
                TpiBase.metadata.create_all(engine)
        logger.info(f"Created tables in database: {db_name}")
    except Exception as e:
        logger.error(f"Failed to create tables in {db_name}: {str(e)}")
        raise

if __name__ == "__main__":
    create_tables("ascor_api")
    create_tables("tpi_api")
    print("All tables created successfully in both databases.") 