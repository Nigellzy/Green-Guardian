"""
Enhanced Trigger Rules with Context-Based Inference
Provides risk estimates for areas without temperature data using green ratio and density type.
"""

import pandas as pd
import logging
from typing import Dict, List
from data_fusion import DataFusion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTriggerRules:
    """
    Evaluates trigger conditions with fallback to context-based inference.
    """
    
    # Threshold Constants
    TEMP_HIGH = 29.5
    TEMP_CRITICAL = 30.5
    GREEN_LOW = 0.2
    GREEN_CRITICAL = 0.1
    
    def __init__(self, dataset: pd.DataFrame = None):
        if dataset is not None:
            self.df = dataset
        else:
            fusion = DataFusion()
            self.df = fusion.get_unified_dataset()
    
    def evaluate_area(self, planning_area: str) -> Dict:
        """Evaluates trigger rules with context-based fallback."""
        area_data = self.df[self.df['planning_area'] == planning_area]
        
        if area_data.empty:
            return {
                'trigger': False,
                'reason': f"Planning area '{planning_area}' not found.",
                'priority': 'N/A',
                'details': {}
            }
        
        row = area_data.iloc[0]
        temp = row['avg_temperature']
        green = row['green_ratio']
        density = row['density_type']
        
        # If temperature data exists, use temperature-based rules
        if pd.notna(temp):
            return self._evaluate_with_temperature(planning_area, temp, green, density)
        
        # Otherwise, infer risk from context (green ratio + density)
        return self._infer_from_context(planning_area, green, density)
    
    def _evaluate_with_temperature(self, area, temp, green, density):
        """Original temperature-based evaluation."""
        triggers = []
        priority = 'NORMAL'
        
        # Determine priority based on temperature and green/density context
        if temp >= self.TEMP_CRITICAL and green < self.GREEN_CRITICAL and density == 'Commercial':
            triggers.append(f"CRITICAL: Extreme heat ({temp}°C) in commercial zone with minimal green coverage ({green:.0%})")
            priority = 'CRITICAL'
        elif temp >= self.TEMP_HIGH and green < self.GREEN_LOW:
            triggers.append(f"HIGH: Elevated temperature ({temp}°C) with low green ratio ({green:.0%})")
            priority = 'HIGH'
        elif temp >= self.TEMP_CRITICAL:
            triggers.append(f"HIGH: Critical temperature threshold exceeded ({temp}°C)")
            priority = 'HIGH'
        elif temp >= self.TEMP_HIGH and density == 'Commercial' and green < self.GREEN_CRITICAL:
            triggers.append(f"MEDIUM: Elevated heat in commercial area with minimal greenery")
            priority = 'MEDIUM'
        elif temp >= self.TEMP_HIGH and density == 'Residential' and green < self.GREEN_LOW:
            triggers.append(f"MEDIUM: Potential heat island in residential area ({temp}°C, {green:.0%} green)")
            priority = 'MEDIUM'
        
        trigger = len(triggers) > 0
        reason = triggers[0] if triggers else f"Normal conditions ({temp}°C, {green:.0%} green, {density})"
        
        return {
            'trigger': trigger,
            'reason': reason,
            'priority': priority,
            'details': {
                'planning_area': area,
                'avg_temperature': temp,
                'green_ratio': green,
                'density_type': density,
                'all_triggers': triggers,
                'data_source': 'temperature'
            }
        }
    
    def _infer_from_context(self, area, green, density):
        """
        Infers risk level from green ratio and density type when temperature is unavailable.
        """
        priority = 'NORMAL'
        reason = f"INFERRED: Adequate green coverage ({green:.0%}, {density})"
        trigger = False
        
        # Analyze context for risk inference
        if density == 'Commercial' and green < self.GREEN_CRITICAL:
            priority = 'MEDIUM'
            reason = f"INFERRED: Commercial zone with minimal green coverage ({green:.0%}) - likely heat-prone"
            trigger = True
        elif green < self.GREEN_CRITICAL:
            priority = 'MEDIUM'
            reason = f"INFERRED: Very low green coverage ({green:.0%}) suggests heat island risk"
            trigger = True
        elif density == 'Residential' and green < self.GREEN_LOW:
            priority = 'LOW'
            reason = f"INFERRED: Residential area with low green coverage ({green:.0%})"
            trigger = True
        
        return {
            'trigger': trigger,
            'reason': reason,
            'priority': priority,
            'details': {
                'planning_area': area,
                'avg_temperature': None,
                'green_ratio': green,
                'density_type': density,
                'data_source': 'context_inference'
            }
        }
    
    def evaluate_all(self) -> List[Dict]:
        """Evaluates ALL areas (with or without temperature data)."""
        results = []
        
        for _, row in self.df.iterrows():
            result = self.evaluate_area(row['planning_area'])
            results.append(result)
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'NORMAL': 4}
        results.sort(key=lambda x: priority_order.get(x['priority'], 5))
        
        return results
    
    def get_triggered_areas(self) -> pd.DataFrame:
        """Returns DataFrame of triggered areas."""
        results = self.evaluate_all()
        triggered = [r for r in results if r['trigger']]
        
        if not triggered:
            return pd.DataFrame()
        
        return pd.DataFrame([
            {
                'planning_area': r['details']['planning_area'],
                'priority': r['priority'],
                'temperature': r['details']['avg_temperature'],
                'green_ratio': r['details']['green_ratio'],
                'density_type': r['details']['density_type'],
                'data_source': r['details']['data_source'],
                'reason': r['reason']
            }
            for r in triggered
        ])


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ENHANCED TRIGGER RULES WITH CONTEXT INFERENCE")
    print("="*70 + "\n")
    
    engine = EnhancedTriggerRules()
    results = engine.evaluate_all()
    
    # Separate by data source
    temp_based = [r for r in results if r['details'].get('data_source') == 'temperature']
    context_based = [r for r in results if r['details'].get('data_source') == 'context_inference']
    
    print(f"📊 COVERAGE:")
    print(f"  Temperature-based: {len(temp_based)} areas")
    print(f"  Context-inferred: {len(context_based)} areas")
    print(f"  Total: {len(results)} areas\n")
    
    # Show triggered areas
    triggered = [r for r in results if r['trigger']]
    
    if triggered:
        print(f"🔥 TRIGGERED AREAS: {len(triggered)}\n")
        
        # Group by priority
        for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            priority_areas = [r for r in triggered if r['priority'] == priority]
            if priority_areas:
                print(f"\n[{priority}] - {len(priority_areas)} areas:")
                for r in priority_areas[:5]:  # Show first 5
                    source = "📡" if r['details']['data_source'] == 'temperature' else "🧠"
                    print(f"  {source} {r['details']['planning_area']}: {r['reason'][:80]}...")
                if len(priority_areas) > 5:
                    print(f"  ... and {len(priority_areas) - 5} more")
    
    print("\n" + "="*70)
    print(f"✅ {len([r for r in results if not r['trigger']])} areas with NORMAL conditions")
    print("="*70)
