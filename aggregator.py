
import pandas as pd
import logging
import os
from perception import DataGovClient
from onemap_client import OneMapClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemperatureAggregator:
    """
    Aggregates real-time temperature data by Singapore Planning Area.
    """
    
    def __init__(self, onemap_token=None):
        self.weather_client = DataGovClient()
        token = onemap_token or os.environ.get("ONEMAP_TOKEN")
        self.onemap_client = OneMapClient(token=token)
        
    def get_aggregated_data(self):
        """
        Fetches weather data, maps it to planning areas, and aggregates statistics.
        Returns:
            pd.DataFrame: DataFrame with columns ['planning_area', 'avg_temp', 'max_temp', 'station_count', 'stations']
        """
        # Fetch raw weather points
        logger.info("Fetching real-time temperature data...")
        points = self.weather_client.get_island_wide_weather("air-temperature")
        
        if not points:
            logger.warning("No temperature data available.")
            return pd.DataFrame()
        
        logger.info(f"Retrieved {len(points)} weather stations.")
        
        # Map points to Planning Areas
        logger.info("Mapping stations to Planning Areas...")
        mapped_data = []
        
        # Ensure Planning Areas are loaded
        self.onemap_client.load_planning_areas()
        
        for p in points:
            lat, lon = p['lat'], p['lng']
            area = self.onemap_client.get_planning_area(lat, lon)
            
            if area:
                mapped_data.append({
                    "planning_area": area,
                    "temperature": p['value'],
                    "station_name": p.get('name', p.get('station_id')),
                    "lat": lat,
                    "lon": lon
                })
            else:
                logger.debug(f"Point {lat},{lon} ({p.get('name')}) not inside any known Planning Area.")

        if not mapped_data:
            logger.warning("No points mapped to valid Planning Areas.")
            return pd.DataFrame()
            
        # Create DataFrame and Aggregate
        df = pd.DataFrame(mapped_data)
        
        result = df.groupby('planning_area').agg(
            avg_temp=('temperature', 'mean'),
            max_temp=('temperature', 'max'),
            station_count=('station_name', 'count'),
            stations=('station_name', lambda x: list(x))
        ).reset_index()
        
        # Round decimals for cleaner output
        result['avg_temp'] = result['avg_temp'].round(1)
        
        # Sort by Max Temp descending
        result = result.sort_values(by='max_temp', ascending=False).reset_index(drop=True)
        
        return result

if __name__ == "__main__":
    agg = TemperatureAggregator()
    
    print("\n--- Aggregating Temperature Data ---\n")
    try:
        df = agg.get_aggregated_data()
        if not df.empty:
            print(df.to_string())
            print(f"\nTotal Planning Areas with Data: {len(df)}")
            
            # Example decision threshold
            HOT_THRESHOLD = 30.0
            hot_areas = df[df['max_temp'] > HOT_THRESHOLD]
            if not hot_areas.empty:
                print(f"\n[ALERT] Areas exceeding {HOT_THRESHOLD}°C:")
                print(hot_areas['planning_area'].tolist())
        else:
            print("No data found.")
    except Exception as e:
        print(f"Error: {e}")
