"""
Data Fusion Module
Merges live weather data with OneMap context features into a unified dataset
for consumption by the Agentic AI loop.
"""

import pandas as pd
import logging
import os
from aggregator import TemperatureAggregator
from context_enricher import ContextEnricher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFusion:
    """
    Combines temperature data and context features into a single dataset.
    """
    
    def __init__(self, onemap_token=None):
        """
        Initialize with optional OneMap token.
        If not provided, will use default from context_enricher.
        """
        self.onemap_token = onemap_token
        
    def get_unified_dataset(self):
        """
        Fetches and merges all data sources into a single DataFrame.
        Returns:
            pd.DataFrame: Unified dataset with columns:
                - planning_area: Name of the planning area
                - avg_temperature: Average temperature in °C
                - green_ratio: Green coverage ratio (0-1)
                - density_type: Commercial/Residential/Mixed/Unknown
        """
        logger.info("Starting data fusion process...")
        
        # Fetch temperature data
        logger.info("Fetching temperature data...")
        temp_agg = TemperatureAggregator(onemap_token=self.onemap_token)
        temp_df = temp_agg.get_aggregated_data()
        
        # We continue even if temp_df is empty, as we might still want context data
        if not temp_df.empty:
            temp_df = temp_df[['planning_area', 'avg_temp']].rename(
                columns={'avg_temp': 'avg_temperature'}
            )
        
        # Fetch context features
        logger.info("Fetching context features...")
        enricher = ContextEnricher(onemap_token=self.onemap_token)
        context_df = enricher.get_context_features()
        
        if context_df.empty:
            logger.warning("No context data available.")
            return pd.DataFrame()
        
        context_df = context_df[['planning_area', 'green_ratio', 'density_type']]
        
        # Merge datasets (Outer join to include areas even without temperature data)
        logger.info("Merging datasets...")
        if temp_df.empty:
            unified_df = context_df
            unified_df['avg_temperature'] = pd.NA
        else:
            unified_df = pd.merge(
                temp_df,
                context_df,
                on='planning_area',
                how='outer' 
            )
        
        # Sort by temperature (descending)
        unified_df = unified_df.sort_values(
            by='avg_temperature', 
            ascending=False,
            na_position='last'
        ).reset_index(drop=True)
        
        logger.info(f"Data fusion complete. {len(unified_df)} planning areas in dataset.")
        logger.info(f"Areas with temperature data: {unified_df['avg_temperature'].notna().sum()}")
        
        return unified_df
    
    def export_to_csv(self, filename='unified_dataset.csv'):
        """
        Exports the unified dataset to CSV for external consumption.
        """
        df = self.get_unified_dataset()
        if not df.empty:
            df.to_csv(filename, index=False)
            logger.info(f"Dataset exported to {filename}")
            return filename
        else:
            logger.error("No data to export.")
            return None

if __name__ == "__main__":
    fusion = DataFusion()
    
    print("\n" + "="*60)
    print("UNIFIED DATASET FOR AGENTIC AI LOOP")
    print("="*60 + "\n")
    
    df = fusion.get_unified_dataset()
    
    if not df.empty:
        # Display full dataset
        print(df.to_string(index=False))
        
        print("\n" + "="*60)
        print("DATASET STATISTICS")
        print("="*60)
        print(f"Total Planning Areas: {len(df)}")
        print(f"Areas with Temperature Data: {df['avg_temperature'].notna().sum()}")
        print(f"Temperature Range: {df['avg_temperature'].min():.1f}°C - {df['avg_temperature'].max():.1f}°C")
        print(f"\nDensity Type Distribution:")
        print(df['density_type'].value_counts().to_string())
        
        # Export to CSV
        print("\n" + "="*60)
        fusion.export_to_csv()
        print("="*60)
    else:
        print("ERROR: No data available.")
