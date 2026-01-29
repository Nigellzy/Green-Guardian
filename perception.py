import requests
import datetime
from math import radians, sin, cos, sqrt, atan2

class DataGovClient:
    """
    Client for accessing real-time environmental data from Data.gov.sg.
    Includes Weather (Temp, Humidity, Wind, Rain) and Air Quality (PM2.5, PSI).
    """
    BASE_URL_V2 = "https://api-open.data.gov.sg/v2/real-time/api"

    def _get_data(self, endpoint, params=None):
        try:
            url = f"{self.BASE_URL_V2}/{endpoint}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching {endpoint}: {e}")
            return None

    def get_weather_suite(self):
        """Fetches a comprehensive snapshot of current weather conditions."""
        return {
            "temperature": self._get_data("air-temperature"),
            "humidity": self._get_data("relative-humidity"),
            "wind_direction": self._get_data("wind-direction"),
            "wind_speed": self._get_data("wind-speed"),
            "rainfall": self._get_data("rainfall")
        }

    def get_air_quality(self):
        """Fetches PSI and PM2.5 readings."""
        return {
            "psi": self._get_data("psi"),
            "pm25": self._get_data("pm25")
        }

    def get_island_wide_weather(self, reading_type="air-temperature"):
        """
        Fetches readings for ALL stations for a specific metric (e.g. air-temperature).
        Returns a list of dicts: [{'lat': ..., 'lng': ..., 'value': ...}, ...]
        """
        response = self._get_data(reading_type)
        points = []
        
        if not response:
            return points
            
        try:
           
            data = response.get('data', response)
            stations = data.get('stations', [])
            if not stations and 'metadata' in data:
                 stations = data['metadata'].get('stations', [])
            
            readings = data.get('readings', [])
            if not readings and 'items' in data:
                items = data['items']
                if items:
                    readings = items[0].get('readings', [])

            if not stations or not readings:
                return points

            actual_readings = []
            if isinstance(readings, list) and readings:
                first_r = readings[0]
                if 'data' in first_r and isinstance(first_r['data'], list):
                     actual_readings = first_r['data']
                else:
                    actual_readings = readings

            reading_map = {}
            for r in actual_readings:
                sid = r.get('stationId', r.get('station_id'))
                if sid:
                    reading_map[sid] = r.get('value')
            
            # Combine location and value
            for s in stations:
                sid = s.get('id')
                val = reading_map.get(sid)
                
                if val is not None:
                    loc = s.get('location', {})
                    points.append({
                        "lat": loc.get('latitude'),
                        "lng": loc.get('longitude'),
                        "value": val,
                        "station_id": sid,
                        "name": s.get('name')
                    })
                    
        except Exception as e:
            print(f"Error extracting grid for {reading_type}: {e}")
            
        return points

class PerceptionAgent:
    """
    Aggregates environmental data (Weather & Air Quality) for decision making.
    """
    def __init__(self):
        self.weather_client = DataGovClient()

    def get_environmental_context(self, lat, lng):
        """
        Gathers all relevant environmental data for a specific location.
        """
        weather = self.weather_client.get_weather_suite()
        air = self.weather_client.get_air_quality()
        
        context = {
            "timestamp": datetime.datetime.now().isoformat(),
            "location": {"lat": lat, "lng": lng},
            "weather": self._extract_nearest_reading(weather, lat, lng),
            "air_quality": self._extract_nearest_reading(air, lat, lng)
        }
        
        return context

    def get_island_wide_weather(self, reading_type="air-temperature"):
        """
        Delegates to the weather client to fetch island-wide data.
        """
        return self.weather_client.get_island_wide_weather(reading_type)


    def _extract_nearest_reading(self, data_suite, lat, lng):
        """
        Helper to parse the Data.gov.sg response structure and find the nearest station/region.
        Handles both Station-based (Weather) and Region-based (Air Quality) formats.
        """
        consolidated = {}
        
        if not data_suite:
            return consolidated

        for key, dataset in data_suite.items():
            if not dataset:
                continue
            
            data_block = dataset.get('data', dataset)
            
            locations = []
            location_type = None # 'station' or 'region'
            
            if 'stations' in data_block:
                locations = data_block['stations']
                location_type = 'station'
            elif 'region_metadata' in data_block:
                locations = data_block['region_metadata']
                location_type = 'region'
            
            if not locations:
                continue

            try:
                # 1. Find nearest location (station or region)
                nearest = None
                min_dist = float('inf')
                
                for loc in locations:
                    # Structure varies: loc['location']['latitude'] vs loc['label_location']['latitude']
                    coords = loc.get('location') or loc.get('label_location')
                    if not coords: continue
                    
                    s_lat = coords['latitude']
                    s_lng = coords['longitude']
                    dist = self._haversine(lat, lng, s_lat, s_lng)
                    
                    if dist < min_dist:
                        min_dist = dist
                        nearest = loc
                
                if not nearest:
                    continue
                
                # 2. Extract the relevant reading for this location
                readings_list = data_block.get('readings', [])
                if not readings_list:
                    items = data_block.get('items', [])
                    if items:
                        readings_list = [items[0]['readings']]
                
                if not readings_list:
                    continue
                    
                latest_reading_set = readings_list[0] 
                
                value = None
                
                if location_type == 'station':

                    target_readings = latest_reading_set.get('data', latest_reading_set)
                    if isinstance(target_readings, list):
                        for r in target_readings:
                            if r.get('stationId') == nearest.get('id'):
                                value = r.get('value')
                                break
                                
                elif location_type == 'region':

                    region_name = nearest.get('name')

                    if isinstance(latest_reading_set, dict):
                        metric_key = next(iter(latest_reading_set)) 
                        region_readings = latest_reading_set[metric_key]
                        value = region_readings.get(region_name)

                if value is not None:
                    consolidated[key] = {
                        "value": value,
                        "unit": self._get_unit(key),
                        "station_dist_km": round(min_dist, 2),
                        "source": nearest.get('name', nearest.get('id'))
                    }
                    
            except Exception as e:
                pass
                
        return consolidated

    def _get_unit(self, key):
        units = {
            "temperature": "deg C",
            "humidity": "%",
            "wind_speed": "knots",
            "wind_direction": "deg",
            "rainfall": "mm",
            "pm25": "ug/m3",
            "psi": "index"
        }
        return units.get(key, "")

    def _haversine(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        R = 6371  # Earth radius in km
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c
