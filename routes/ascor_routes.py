from pathlib import Path
from fastapi import APIRouter, HTTPException, Request 
from schemas import CountryDataResponse
from middleware.rate_limiter import limiter
from log_config import get_logger
from utils.database_manager import DatabaseManagerFactory

logger = get_logger(__name__)

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
router = APIRouter(tags=["ASCOR Endpoints"])

# SQL file paths
SQL_DIR = Path(__file__).parent.parent / "sql" / "ascor" / "queries"

@router.get("/countries")
async def get_countries():
    """Get a list of all available countries in the dataset."""
    try:
        logger.info("Getting list of all countries from database")
        db_manager = DatabaseManagerFactory.get_manager("ascor_api")
        
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_all_countries.sql"
        )
        
        countries = result['country_name'].tolist()
        logger.info(f"Found {len(countries)} countries in the database")
        return {"countries": countries}
    except Exception as e:
        logger.exception(f"Error getting countries list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/country-data/{country}/{assessment_year}", response_model=CountryDataResponse)
@limiter.limit("100/minute")
async def get_country_data(request: Request, country: str, assessment_year: int) -> CountryDataResponse:
    """Get assessment data for a specific country and year from the database."""
    try:
        logger.info(f"Processing request for country: {country}, year: {assessment_year}")
        db_manager = DatabaseManagerFactory.get_manager("ascor_api")
        
        # Get assessment data from database
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_country_assessment_data.sql",
            params={
                "country_name": country.strip(),
                "assessment_year": assessment_year
            }
        )
        
        if result.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"No data found for country '{country}' in year {assessment_year}"
            )
        
        # Process the database result into the expected response format
        from schemas import Pillar, Area, Indicator, Metric, MetricSource, IndicatorSource
        
        # Group data by pillar -> area -> indicator -> metric hierarchy
        pillars_data = {}
        
        for _, row in result.iterrows():
            code = row['code']
            element_type = row['element_type']
            response = row['response']
            element_text = row['element_text']
            source = row['source']
            
            # Parse the hierarchical code (e.g., "CF.1.a.i")
            code_parts = code.split('.')
            if len(code_parts) < 1:
                continue
                
            pillar_name = code_parts[0]  # CF, CP, EP
            
            # Initialize pillar if not exists
            if pillar_name not in pillars_data:
                pillars_data[pillar_name] = {}
            
            if element_type == 'area':
                # This is an area (e.g., "CF.1")
                area_code = code
                if area_code not in pillars_data[pillar_name]:
                    pillars_data[pillar_name][area_code] = {
                        'name': element_text or code,
                        'assessment': response or '',
                        'indicators': {}
                    }
            
            elif element_type == 'indicator':
                # This is an indicator (e.g., "CF.1.a")
                # Find the parent area
                area_code = '.'.join(code_parts[:2]) if len(code_parts) >= 2 else code_parts[0]
                
                # Ensure area exists
                if area_code not in pillars_data[pillar_name]:
                    pillars_data[pillar_name][area_code] = {
                        'name': area_code,
                        'assessment': '',
                        'indicators': {}
                    }
                
                pillars_data[pillar_name][area_code]['indicators'][code] = {
                    'name': element_text or code,
                    'assessment': response or 'No data',
                    'metrics': [],
                    'source': IndicatorSource(source_name=source) if source else None
                }
            
            elif element_type == 'metric':
                # This is a metric (e.g., "CF.1.a.i")
                # Find the parent indicator and area
                if len(code_parts) >= 3:
                    area_code = '.'.join(code_parts[:2])
                    indicator_code = '.'.join(code_parts[:3])
                    
                    # Ensure area and indicator exist
                    if area_code not in pillars_data[pillar_name]:
                        pillars_data[pillar_name][area_code] = {
                            'name': area_code,
                            'assessment': '',
                            'indicators': {}
                        }
                    
                    if indicator_code not in pillars_data[pillar_name][area_code]['indicators']:
                        pillars_data[pillar_name][area_code]['indicators'][indicator_code] = {
                            'name': indicator_code,
                            'assessment': 'No data',
                            'metrics': [],
                            'source': None
                        }
                    
                    # Add metric
                    metric = Metric(
                        name=element_text or code,
                        value=response or '',
                        source=MetricSource(source_name=source) if source else None
                    )
                    pillars_data[pillar_name][area_code]['indicators'][indicator_code]['metrics'].append(metric)
        
        # Convert to Pydantic models
        pillars = []
        for pillar_name, areas_data in pillars_data.items():
            areas = []
            for area_code, area_data in areas_data.items():
                indicators = []
                for indicator_code, indicator_data in area_data['indicators'].items():
                    indicator = Indicator(
                        name=indicator_data['name'],
                        assessment=indicator_data['assessment'],
                        metrics=indicator_data['metrics'],
                        source=indicator_data['source']
                    )
                    indicators.append(indicator)
                
                area = Area(
                    name=area_data['name'],
                    assessment=area_data['assessment'],
                    indicators=indicators
                )
                areas.append(area)
            
            pillar = Pillar(name=pillar_name, areas=areas)
            pillars.append(pillar)
        
        response = CountryDataResponse(
            country=country,
            assessment_year=assessment_year,
            pillars=pillars
        )
        
        logger.info(f"Successfully processed data for {country}, {assessment_year}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing data for {country}, {assessment_year}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected server error.")