from flask import Flask, render_template_string
from perception import PerceptionAgent
from app import MitigationAgent
from geo_enhanced import generate_heatmap_with_planning_areas
from onemap_client import OneMapClient
from trigger_rules_enhanced import EnhancedTriggerRules
import datetime
import markdown

app = Flask(__name__)

# Initialize Agents & Clients
perception = PerceptionAgent()
mitigation_agent = MitigationAgent()
onemap_client = OneMapClient()
rules_engine = EnhancedTriggerRules()

# Pre-load planning areas
print("Loading planning areas...")
onemap_client.load_planning_areas()


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>HFC: Urban Heat Perception Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; font-family: 'Inter', sans-serif; background: #0f0f0f; color: #eee; height: 100vh; overflow: hidden; }
        .container { display: flex; height: 100%; width: 100%; }
        
        /* Main Map Area */
        .main-content { flex: 1; display: flex; flex-direction: column; position: relative; }
        .header { padding: 15px 20px; background: #1a1a1a; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; z-index: 10; }
        iframe { flex-grow: 1; border: none; width: 100%; height: 100%; }
        
        /* Sidebar */
        .sidebar { width: 350px; background: #1a1a1a; border-left: 1px solid #333; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; overflow-y: auto; }
        .sidebar h2 { color: #00ff9d; margin-top: 0; font-size: 1.2rem; }
        .stat-card { background: #252525; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .stat-value { font-size: 2rem; font-weight: bold; }
        .stat-label { color: #aaa; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
        
        /* AI Response Style */
        .ai-response { background: #252525; padding: 15px; border-radius: 8px; border-left: 4px solid #00ff9d; line-height: 1.5; font-size: 0.9rem; }
        .ai-response h3, .ai-response strong { color: #fff; }
        .ai-response ul { padding-left: 20px; }
        .ai-badge { display: inline-block; background: linear-gradient(45deg, #4285f4, #34a853); padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; margin-bottom: 10px; }

    </style>
</head>
<body>
    <div class="container">
        <!-- Map Section -->
        <div class="main-content">
            <div class="header">
                <div>
                    <h1 style="margin:0; font-size: 1.2rem;">HFC Perception Dashboard</h1>
                    <div style="font-size: 0.8em; color: #888;">Real-time Urban Heat Island Monitoring</div>
                </div>
                <div style="text-align: right; font-size: 0.8em; color: #aaa;">
                    Last Update: {{ timestamp }}<br>
                    Active Sensors: {{ count }}
                </div>
            </div>
            <iframe src="/map_content"></iframe>
        </div>

        <!-- AI Sidebar -->
        <div class="sidebar">
            <div class="stat-card">
                <div class="stat-label">Hottest District</div>
                <div class="stat-value" style="color: #ff4444;">{{ hotspot_name }}</div>
                <div style="font-size: 1.5rem;">{{ hotspot_temp }}°C</div>
            </div>

            <h2>Gemini Analysis</h2>
            <div class="ai-response">
                <span class="ai-badge">GEMINI 2.0 FLASH</span>
                <div>{{ ai_analysis | safe }}</div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    # Fetch real-time weather data
    points = perception.get_island_wide_weather("air-temperature")
    
    # Identify Hotspot
    hotspot_name = "N/A"
    hotspot_temp = 0.0
    
    if points:
        hottest = max(points, key=lambda x: x['value'])
        hotspot_name = hottest.get('name', 'Unknown')
        hotspot_temp = hottest.get('value', 0)
    
    # Get AI Assessment from Gemini
    ai_text = mitigation_agent.assess_district(hotspot_name, hotspot_temp)
    ai_html = markdown.markdown(ai_text)
    
    return render_template_string(
        HTML_TEMPLATE, 
        timestamp=datetime.datetime.now().strftime("%H:%M:%S"),
        count=len(points),
        hotspot_name=hotspot_name,
        hotspot_temp=hotspot_temp,
        ai_analysis=ai_html
    )

@app.route('/map_content')
def map_content():
    points = perception.get_island_wide_weather("air-temperature")
    
    # Ensure planning areas are loaded
    if not onemap_client.planning_areas:
         onemap_client.load_planning_areas()
         
    planning_areas_data = onemap_client.planning_areas
    
    # Evaluate risk for all areas
    evaluation_results = rules_engine.evaluate_all()
    risk_data = {r['details']['planning_area']: r['priority'] for r in evaluation_results}

    # Generate Enhanced Heatmap with overlays
    m = generate_heatmap_with_planning_areas(points, planning_areas_data, risk_data)
    
    return m.get_root().render()

if __name__ == '__main__':
    print("Starting HFC Dashboard on port 5000...")
    app.run(debug=True, port=5000)
