
import pandas as pd
import logging
import os
from onemap_client import OneMapClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextEnricher:
    """
    Enriches Planning Area data with context from OneMap Themes.
    Calculates Green Coverage and Commercial/Residential Density.
    """
    
    # Theme Identifiers (OneMap 'queryName')
    THEMES_GREEN = ['nationalparks', 'nparks_parks'] 
    THEMES_COMMERCIAL = ['hotels'] 
    THEMES_RESIDENTIAL = ['kindergartens', 'ssot_hawkercentres'] 
    
    def __init__(self, onemap_token=None):
        token = onemap_token or os.environ.get("ONEMAP_TOKEN")
        self.client = OneMapClient(token=token)
        self.planning_areas = []
        
    def _fetch_and_map(self, theme_list):
        """
        Fetches data for all themes in the list and maps them to Planning Areas.
        Returns a dict: { 'PLANNING_AREA_NAME': count, ... }
        """
        counts = {}
        
        for theme in theme_list:
            items = self.client.get_theme_data(theme)
            for item in items:
                latlng_str = item.get('LatLng', '')
                if not latlng_str or ',' not in latlng_str:
                     continue
                     
                lat, lon = latlng_str.split(',')
                try:
                    lat, lon = float(lat), float(lon)
                    area = self.client.get_planning_area(lat, lon)
                    if area:
                        counts[area] = counts.get(area, 0) + 1
                except ValueError:
                    continue
                    
        return counts

    def get_context_features(self):
        """
        Generates a DataFrame with context features for all Planning Areas.
        """
        logger.info("Loading base Planning Area data...")
        self.client.load_planning_areas()
        
        # Initialize DF with all known areas
        all_areas = [a['name'] for a in self.client.planning_areas]
        df = pd.DataFrame({'planning_area': all_areas})
        
        # Process Greenery Themes
        logger.info("Processing Greenery Themes...")
        green_counts = self._fetch_and_map(self.THEMES_GREEN)
        df['green_count'] = df['planning_area'].map(green_counts).fillna(0)
        
        # Calculate approximate Green Ratio (0-1) relative to max
        max_green = df['green_count'].max()
        df['green_ratio'] = (df['green_count'] / max_green).round(2) if max_green > 0 else 0
        
        # Process Commercial/Residential Themes
        logger.info("Processing Commercial Themes...")
        comm_counts = self._fetch_and_map(self.THEMES_COMMERCIAL)
        logger.info("Processing Residential Themes...")
        res_counts = self._fetch_and_map(self.THEMES_RESIDENTIAL)
        
        df['comm_count'] = df['planning_area'].map(comm_counts).fillna(0)
        df['res_count'] = df['planning_area'].map(res_counts).fillna(0)
        
        def determine_density(row):
            c = row['comm_count']
            r = row['res_count']
            total = c + r
            if total == 0:
                return 'Unknown/Low Density'
            
            comm_ratio = c / total
            if comm_ratio > 0.6:
                return 'Commercial'
            elif comm_ratio < 0.4:
                return 'Residential'
            else:
                return 'Mixed'

        df['density_type'] = df.apply(determine_density, axis=1)
        
        return df[['planning_area', 'green_ratio', 'density_type', 'green_count', 'comm_count', 'res_count']]

if __name__ == "__main__":
    enricher = ContextEnricher()
    
    print("\n--- Generating Context Features ---\n")
    df = enricher.get_context_features()
    
    # Show interesting rows (top green, and some comm vs res)
    print("Top 5 Green Areas:")
    print(df.sort_values(by='green_ratio', ascending=False).head(5)[['planning_area', 'green_ratio', 'green_count']])
    
    print("\nDensity Types Summary:")
    print(df['density_type'].value_counts())
    
    print("\nSample Data:")
    print(df.sample(5).to_string())
