import os
import datetime
from dotenv import load_dotenv
from google import genai
from perception import PerceptionAgent


# Load environment variables
load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

class MitigationAgent:
    """
    Generates strategic urban heat mitigation assessments using Google Gemini 2.0.
    """
    def assess_district(self, station_name, temperature, env_context=None):
        """
        Generates a strategic district-level assessment.
        """
        prompt = f"""
        You are an AI Urban Planner for Singapore (URA/HDB).
        
        SITUATION:
        Real-time sensors detect a heat hotspot at **{station_name}** measuring **{temperature}°C**.
        
        TASK:
        1. Analyze the severity (Is this normal for Singapore? Is it a heatwave?).
        2. Recommend immediate district-level interventions (e.g., "Deploy mobile misting units", "Check district cooling load", "Issue health advisory").
        3. Suggest long-term mitigation for this specific area.
        
        OUTPUT FORMAT:
        Use Markdown. Keep it brief (bullet points). Tone: Professional, Urgent, Strategic.
        """
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini Error: {e}")
            
            # Rate Limit Handling (Fallback to Simulation)
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                return f"""
### **⚠️ AI Rate Notice**
*Gemini is experiencing high traffic. Showing simulated analysis for **{station_name}**.*

### **1. 🌡️ Severity Analysis**
*   **Status**: Moderate to High Heat Stress.
*   **Context**: Temperature of **{temperature}°C** is above the district norm for this time of day.

### **2. 🚀 Immediate Interventions**
*   **Deploy**: Mobile cooling stations to bus interchanges in the area.
*   **Alert**: Send hydration reminders to community gardening groups via app.
*   **Monitor**: Increase sensor polling rate to 5-minute intervals.

### **3. 🌳 Long-Term Strategy**
*   **Green Facades**: Mandate vertical greening for upcoming BTO projects in {station_name}.
*   **Wind Corridors**: Review urban canyon effects in next Master Plan review.
"""
            
            return f"**System Alert:** Gemini is currently offline ({e}). Manual monitoring required for {station_name}."



