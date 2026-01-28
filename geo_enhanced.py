"""
Enhanced Geo Visualization Module
Adds planning area overlay with risk-based coloring to existing heatmap.
"""

import geopandas as gpd
import folium
from folium.plugins import HeatMap
from folium.features import DivIcon
from folium import GeoJson
import json
from shapely.geometry import mapping

# Risk-based color palette
RISK_COLORS = {
    'CRITICAL': '#8B0000',  # Dark Red
    'HIGH': '#FF4444',      # Red
    'MEDIUM': '#FFA500',    # Orange
    'LOW': '#90EE90',       # Light Green
    'NORMAL': '#32CD32',    # Green
    'NO_DATA': '#808080'    # Gray
}

def visualize_geojson(file_path):
    """Utility to visualize a GeoJSON file."""
    try:
        gdf = gpd.read_file(file_path)
    except Exception as e:
        print(f"Error loading GeoJSON: {e}")
        return None

    # Ensure the data is in WGS84
    if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs(epsg=4326)

    # Calculate center
    bounds = gdf.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles='CartoDB dark_matter')

    folium.GeoJson(
        gdf,
        style_function=lambda x: {
            'fillColor': 'green',
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.4,
        },
        tooltip=folium.GeoJsonTooltip(fields=list(gdf.columns[:3]))
    ).add_to(m)

    m.save("my_map.html")
    print("Success! 'my_map.html' has been created.")
    return m


def generate_heatmap(data_points):
    """
    Generates a Folium map with a HeatMap layer.
    data_points: List of dicts {'lat': float, 'lng': float, 'value': float}
    """
    # Center on Singapore (Satellite View)
    m = folium.Map(
        location=[1.3521, 103.8198], 
        zoom_start=11, 
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery'
    )

    # Add overlay for place names
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name='Labels',
        overlay=True,
        control=True
    ).add_to(m)

    if not data_points:
        return m
        
    # Prepare data for HeatMap
    heat_data = [[p['lat'], p['lng'], p['value']] for p in data_points]
    
    # Add HeatMap layer
    HeatMap(
        heat_data, 
        radius=35,
        blur=25,
        max_zoom=1,
        gradient={
            0.0: '#00008b', # Dark Blue (Cool)
            0.3: '#00ffff', # Cyan
            0.5: '#00ff00', # Lime
            0.7: '#ffff00', # Yellow
            0.9: '#ff0000'  # Red (Hot)
        }
    ).add_to(m)
    
    # Add visible text labels for stations
    for p in data_points:
        temp = p['value']
        name = p.get('name', 'Station')
        text_color = '#ff4444' if temp > 29 else '#00ccff'
        
        folium.Marker(
            location=[p['lat'], p['lng']],
            icon=DivIcon(
                icon_size=(150,36),
                icon_anchor=(75, 18),
                html=f'''<div style="font-size: 10pt; font-weight: bold; color: {text_color}; text-shadow: 1px 1px 2px black; text-align: center;">{name}<br>{temp}°C</div>'''
            )
        ).add_to(m)
        
    return m


def generate_heatmap_with_planning_areas(data_points, planning_areas_data=None, risk_data=None):
    """
    Enhanced heatmap with planning area overlay and risk-based coloring.
    
    Args:
        data_points: List of dicts {'lat': float, 'lng': float, 'value': float}
        planning_areas_data: List of dicts from OneMapClient.planning_areas
        risk_data: Dict mapping planning_area -> priority level (CRITICAL/HIGH/MEDIUM/LOW/NORMAL)
    
    Returns:
        folium.Map object with all layers
    """
    # Start with base heatmap
    m = generate_heatmap(data_points)
    
    # Add planning area overlay if provided
    if planning_areas_data and risk_data:
        m = add_planning_area_overlay(m, planning_areas_data, risk_data)
    
    return m


def add_planning_area_overlay(map_obj, planning_areas_data, risk_data):
    """
    Adds planning area polygons with risk-based coloring to existing map.
    
    Args:
        map_obj: Folium Map object
        planning_areas_data: List of dicts from OneMapClient.planning_areas
        risk_data: Dict mapping planning_area -> priority level
    
    Returns:
        Modified map_obj
    """
    
    # Convert planning areas to GeoJSON
    geojson_features = []
    for area in planning_areas_data:
        feature = {
            "type": "Feature",
            "properties": {
                "pln_area_n": area['name'],
                "priority": risk_data.get(area['name'], 'NO_DATA')
            },
            "geometry": mapping(area['geometry'])
        }
        geojson_features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": geojson_features
    }
    
    # Style function based on risk level
    def style_function(feature):
        priority = feature['properties'].get('priority', 'NO_DATA')
        
        return {
            'fillColor': RISK_COLORS.get(priority, '#808080'),
            'color': '#ffffff',  # White border
            'weight': 2,
            'fillOpacity': 0.35,  # Semi-transparent to see heatmap
            'dashArray': '5, 5'  # Dashed border
        }
    
    # Highlight on hover
    def highlight_function(feature):
        return {
            'fillOpacity': 0.65,
            'weight': 4
        }
    
    # Add GeoJSON layer
    GeoJson(
        geojson,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['pln_area_n', 'priority'],
            aliases=['Planning Area:', 'Risk Level:'],
            style='background-color: white; color: black; font-weight: bold; padding: 10px; border-radius: 5px;'
        ),
        name='Planning Areas'
    ).add_to(map_obj)
    
    # Add legend
    add_risk_legend(map_obj)
    
    # Add layer control
    folium.LayerControl().add_to(map_obj)
    
    return map_obj


def add_risk_legend(map_obj):
    """Adds a legend explaining risk levels."""
    
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; 
                left: 50px; 
                width: 220px; 
                background-color: rgba(255, 255, 255, 0.95); 
                border: 3px solid #333; 
                z-index: 9999; 
                padding: 15px; 
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <h4 style="margin: 0 0 12px 0; font-family: Arial; color: #333;">🔥 Heat Risk Levels</h4>
        <div style="margin: 8px 0; font-family: Arial; font-size: 13px;">
            <span style="background: #8B0000; width: 25px; height: 15px; display: inline-block; margin-right: 8px; border: 1px solid #333;"></span>
            <strong>Critical</strong>
        </div>
        <div style="margin: 8px 0; font-family: Arial; font-size: 13px;">
            <span style="background: #FF4444; width: 25px; height: 15px; display: inline-block; margin-right: 8px; border: 1px solid #333;"></span>
            <strong>High</strong>
        </div>
        <div style="margin: 8px 0; font-family: Arial; font-size: 13px;">
            <span style="background: #FFA500; width: 25px; height: 15px; display: inline-block; margin-right: 8px; border: 1px solid #333;"></span>
            <strong>Medium</strong>
        </div>
        <div style="margin: 8px 0; font-family: Arial; font-size: 13px;">
            <span style="background: #90EE90; width: 25px; height: 15px; display: inline-block; margin-right: 8px; border: 1px solid #333;"></span>
            <strong>Low</strong>
        </div>
        <div style="margin: 8px 0; font-family: Arial; font-size: 13px;">
            <span style="background: #32CD32; width: 25px; height: 15px; display: inline-block; margin-right: 8px; border: 1px solid #333;"></span>
            <strong>Normal</strong>
        </div>
        <div style="margin: 8px 0; font-family: Arial; font-size: 13px;">
            <span style="background: #808080; width: 25px; height: 15px; display: inline-block; margin-right: 8px; border: 1px solid #333;"></span>
            No Data
        </div>
    </div>
    '''
    
    map_obj.get_root().html.add_child(folium.Element(legend_html))
    return map_obj
