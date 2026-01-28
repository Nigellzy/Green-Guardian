
import requests
import json
import os
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OneMapClient:
    """
    Client for Singapore OneMap API to map coordinates to Planning Areas.
    """
    
    BASE_URL = "https://www.onemap.gov.sg/api/public"
    
    def __init__(self, token=None):
        self.token = token or os.environ.get("ONEMAP_TOKEN")
        self.planning_areas = []
        self.spatial_index = None
        
    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.token
        return headers

    def load_planning_areas(self, year="2019"):
        """Fetches and caches planning area polygons."""
        if self.planning_areas:
            logger.info("Using cached planning areas.")
            return

        endpoint = f"{self.BASE_URL}/popapi/getAllPlanningarea"
        params = {"year": year}
        
        try:
            logger.info(f"Fetching planning areas from {endpoint}...")
            response = requests.get(endpoint, headers=self._get_headers(), params=params)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict):
                data = data.get("SearchResults", data.get("results", []))
            
            parsed_areas = []
            for item in data:
                try:
                    geo_json_raw = item.get('geojson')
                    geo_json = json.loads(geo_json_raw) if isinstance(geo_json_raw, str) else geo_json_raw
                    polygon = shape(geo_json)
                    parsed_areas.append({
                        "name": item.get("pln_area_n", "UNKNOWN"),
                        "geometry": polygon,
                        "raw": item
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse planning area {item.get('pln_area_n')}: {e}")
            
            self.planning_areas = parsed_areas
            logger.info(f"Successfully loaded {len(self.planning_areas)} planning areas.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error serving OneMap API request: {e}")
            raise

    def get_theme_data(self, query_name):
        """
        Fetches data for a specific theme (e.g., 'nationalparks', 'hotels').
        
        Args:
            query_name (str): The specific query name for the theme.
            
        Returns:
            list: List of result items (dicts) with 'LatLng' and properties.
        """
        if not self.token:
            logger.warning("Token might be required for themes, but attempting without...")
        
        endpoint = f"{self.BASE_URL}/themesvc/retrieveTheme"
        params = {"queryName": query_name}
        if self.token:
            params["token"] = self.token
        
        try:
            logger.info(f"Fetching theme '{query_name}'...")
            response = requests.get(endpoint, headers=self._get_headers(), params=params)
            if response.status_code != 200:
                logger.error(f"Failed to fetch theme {query_name}: {response.status_code}")
                return []
                
            data = response.json()
            results = data.get("SrchResults") or data.get("SrchCmd") or []
            
            if isinstance(results, list):
                logger.info(f"Theme '{query_name}' returned {len(results)} items.")
                return results
            else:
                logger.warning(f"Unexpected theme structure for '{query_name}': {type(results)}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching theme {query_name}: {e}")
            return []

    def get_all_themes_info(self):
        """
        Fetches the list of all available themes.
        Returns:
             list: List of dicts with 'THEMENAME' and 'QUERYNAME'.
        """
        endpoint = f"{self.BASE_URL}/themesvc/getAllThemesInfo"
        try:
            # This endpoint often requires no params but headers might help if token needed.
            response = requests.get(endpoint, headers=self._get_headers())
            if response.status_code != 200:
                logger.error(f"Failed to get themes info: {response.status_code}")
                return []
            
            data = response.json()
            return data.get("Theme_Names", [])
        except Exception as e:
            logger.error(f"Error listing themes: {e}")
            return []

    def get_planning_area(self, lat, lon):
        """
        Maps a single (lat, lon) point to a Singapore Planning Area.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            str: Name of the Planning Area (e.g., 'BEDOK'), or None if not found/outside SG.
        """
        if not self.planning_areas:
            self.load_planning_areas()
            
        point = Point(lon, lat)
        
        for area in self.planning_areas:
            if area["geometry"].contains(point):
                return area["name"]
        
        return None

    def map_points(self, points):
        """
        Batch processes a list of points.
        
        Args:
            points (list): List of dicts {'lat': float, 'lon': float} 
                           OR list of tuples [(lat, lon), ...]
                           
        Returns:
            list: List of dicts including the original lat/lon and 'planning_area'.
        """
        results = []
        for p in points:
            if isinstance(p, dict):
                lat, lon = p['lat'], p['lon']
            else:
                lat, lon = p[0], p[1]
                
            area = self.get_planning_area(lat, lon)
            
            results.append({
                "lat": lat,
                "lon": lon,
                "planning_area": area
            })
            
        return results

# Example Usage Block (if run as script)
if __name__ == "__main__":
    import os
    
    # Test data representing some weather stations or random points
    test_points = [
        (1.2963, 103.8502), # SMU (Approx, Museum/Rochor)
        (1.3521, 103.8198), # MacRitchie (Central Water Catchment)
        (1.3644, 103.9915), # Changi Airport
        (1.5000, 104.0000)  # Outside SG
    ]
    
    token = os.environ.get("ONEMAP_TOKEN")
    
    if not token:
        print("WARNING: No ONEMAP_TOKEN environment variable found.")
        print("Please set it via: export ONEMAP_TOKEN='your_token_here'")
    
    print(f"Initializing OneMap Client with token: {token[:5]}..." if token else "Initializing OneMap Client WITHOUT token...")
    client = OneMapClient(token=token)
    
    try:
        mapped = client.map_points(test_points)
        print(json.dumps(mapped, indent=2))
    except Exception as e:
        print(f"Failed: {e}")

