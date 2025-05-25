import os
import logging
from pipelines import TPIPipeline, ASCORPipeline

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_pipeline(data_dir: str):
    """Run the TPI and ASCOR database pipelines.
    
    Args:
        data_dir (str): Path to the data directory
    """
    try:
        # Initialize pipelines
        tpi_pipeline = TPIPipeline(data_dir, logger)
        ascor_pipeline = ASCORPipeline(data_dir, logger)
        
        # Run TPI pipeline
        logger.info("Starting TPI database pipeline...")
        tpi_pipeline.drop_tables()
        tpi_pipeline.create_tables()
        tpi_pipeline.populate_tables()
        logger.info("TPI database pipeline completed successfully.")
        
        # Run ASCOR pipeline
        logger.info("Starting ASCOR database pipeline...")
        ascor_pipeline.drop_tables()
        ascor_pipeline.create_tables()
        ascor_pipeline.populate_tables()
        logger.info("ASCOR database pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    run_pipeline(data_dir) 