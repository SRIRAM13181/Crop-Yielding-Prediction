"""
Batch Prediction Processor
Handle bulk CSV upload for multiple crop predictions.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Optional
import streamlit as st
from utils import predict_yield


class BatchPredictor:
    """Process batch predictions from CSV files."""
    
    # Expected columns in CSV
    REQUIRED_COLUMNS = {
        'rainfall', 'temperature', 'humidity', 'nitrogen',
        'phosphorus', 'potassium', 'pH', 'soil_type', 'crop', 'state'
    }
    
    # Lookup maps (must match app.py)
    SOIL_MAP = {"Loamy": 0, "Clay": 1, "Sandy": 2}
    CROP_MAP = {"Wheat": 0, "Rice": 1, "Maize": 2, "Sugarcane": 3}
    INDIAN_STATES = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
        "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
        "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
        "Uttar Pradesh", "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands",
        "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
        "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
    ]
    STATE_MAP = {state: idx for idx, state in enumerate(INDIAN_STATES)}
    
    def __init__(self):
        """Initialize batch predictor."""
        pass
    
    def validate_csv(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate CSV structure and data.
        
        Args:
            df: DataFrame from CSV
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check columns
        provided_columns = set(df.columns)
        if not self.REQUIRED_COLUMNS.issubset(provided_columns):
            missing = self.REQUIRED_COLUMNS - provided_columns
            return False, f"Missing columns: {', '.join(missing)}"
        
        # Check rows
        if len(df) == 0:
            return False, "CSV is empty"
        
        if len(df) > 10000:
            return False, f"CSV too large: {len(df)} rows. Maximum 10,000 rows allowed."
        
        # Check data types
        numeric_columns = ['rainfall', 'temperature', 'humidity', 'nitrogen', 
                          'phosphorus', 'potassium', 'pH']
        for col in numeric_columns:
            try:
                pd.to_numeric(df[col])
            except ValueError:
                return False, f"Column '{col}' contains non-numeric values"
        
        # Check categorical values
        invalid_soils = set(df['soil_type']) - set(self.SOIL_MAP.keys())
        if invalid_soils:
            return False, f"Invalid soil types: {invalid_soils}. Valid: {list(self.SOIL_MAP.keys())}"
        
        invalid_crops = set(df['crop']) - set(self.CROP_MAP.keys())
        if invalid_crops:
            return False, f"Invalid crops: {invalid_crops}. Valid: {list(self.CROP_MAP.keys())}"
        
        invalid_states = set(df['state']) - set(self.STATE_MAP.keys())
        if invalid_states:
            return False, f"Invalid states: {', '.join(list(invalid_states)[:5])}... Please check state names."
        
        return True, "Validation passed"
    
    def encode_row(self, row: pd.Series) -> list:
        """
        Encode a row from CSV into feature vector for model.
        
        Args:
            row: DataFrame row
        
        Returns:
            Feature vector [rainfall, temp, humidity, N, P, K, pH, soil_code, crop_code, state_code]
        """
        features = [
            float(row['rainfall']),
            float(row['temperature']),
            float(row['humidity']),
            float(row['nitrogen']),
            float(row['phosphorus']),
            float(row['potassium']),
            float(row['pH']),
            self.SOIL_MAP[row['soil_type']],
            self.CROP_MAP[row['crop']],
            self.STATE_MAP[row['state']],
        ]
        return features
    
    def process_batch(
        self,
        df: pd.DataFrame,
        progress_callback=None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Process batch predictions.
        
        Args:
            df: Input DataFrame
            progress_callback: Optional callback for progress updates
        
        Returns:
            Tuple of (results_df, error_log)
        """
        results = []
        errors = []
        
        total_rows = len(df)
        
        for idx, (_, row) in enumerate(df.iterrows()):
            try:
                # Encode features
                features = self.encode_row(row)
                
                # Predict
                predicted_yield = float(predict_yield(features))
                
                # Store result
                result_row = dict(row)
                result_row['predicted_yield'] = predicted_yield
                results.append(result_row)
                
                # Progress callback
                if progress_callback:
                    progress_callback(idx + 1, total_rows)
            
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                # Add row with error flag
                result_row = dict(row)
                result_row['predicted_yield'] = None
                result_row['error'] = str(e)
                results.append(result_row)
        
        results_df = pd.DataFrame(results)
        
        # Reorder columns: put predicted_yield after input columns
        cols = list(results_df.columns)
        if 'predicted_yield' in cols:
            cols.remove('predicted_yield')
            cols.insert(10, 'predicted_yield')  # After state
        if 'error' in cols:
            cols.remove('error')
            cols.append('error')  # At end
        
        results_df = results_df[cols]
        
        return results_df, errors
    
    def get_summary_stats(self, results_df: pd.DataFrame) -> Dict:
        """
        Get summary statistics for batch predictions.
        
        Args:
            results_df: Results DataFrame
        
        Returns:
            Dictionary with statistics
        """
        successful = results_df[results_df['predicted_yield'].notna()]
        failed = results_df[results_df['predicted_yield'].isna()]
        
        stats = {
            "total_processed": len(results_df),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": f"{(len(successful) / len(results_df) * 100):.1f}%" if len(results_df) > 0 else "0%",
            "avg_yield": successful['predicted_yield'].mean() if len(successful) > 0 else 0,
            "min_yield": successful['predicted_yield'].min() if len(successful) > 0 else 0,
            "max_yield": successful['predicted_yield'].max() if len(successful) > 0 else 0,
        }
        
        return stats


def format_batch_results(results_df: pd.DataFrame) -> str:
    """Format results DataFrame for display."""
    display_cols = ['crop', 'state', 'rainfall', 'temperature', 'nitrogen', 
                   'phosphorus', 'potassium', 'predicted_yield']
    display_cols = [col for col in display_cols if col in results_df.columns]
    
    return results_df[display_cols].to_csv(index=False)
