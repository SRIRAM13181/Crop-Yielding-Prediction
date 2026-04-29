import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
import numpy as np

def load_and_preprocess(file_path):
    """
    Loads a CSV dataset and preprocesses it: 
    - Fills missing values
    - Encodes categorical columns
    - Scales numerical columns

    If the CSV file does not exist, generates a synthetic dataset.
    """
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        print(f"⚠️ File '{file_path}' not found. Generating synthetic dataset.")
        np.random.seed(42)
        n = 300  # more rows for richer synthetic training
        indian_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
            "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal",
            "Andaman and Nicobar Islands", "Chandigarh", "Delhi", "Jammu and Kashmir",
            "Ladakh", "Lakshadweep", "Puducherry"
        ]
        df = pd.DataFrame({
            'Crop': np.random.choice(['Wheat', 'Rice', 'Maize', 'Sugarcane'], n),
            'Soil_Type': np.random.choice(['Loamy', 'Sandy', 'Clay'], n),
            'State': np.random.choice(indian_states, n),
            'Rainfall': np.random.uniform(50, 300, n),
            'Temperature': np.random.uniform(15, 38, n),
            'Humidity': np.random.uniform(30, 95, n),
            'Nitrogen': np.random.uniform(10, 60, n),
            'Phosphorus': np.random.uniform(5, 35, n),
            'Potassium': np.random.uniform(5, 40, n),
            'pH': np.random.uniform(4.5, 8.5, n),
            'Yield': np.random.uniform(2, 10, n)
        })

    
    df.fillna(df.mean(numeric_only=True), inplace=True)

    
    label_enc = LabelEncoder()
    categorical_cols = ['Crop', 'Soil_Type', 'State']
    for col in categorical_cols:
        if col in df.columns:
            df[col] = label_enc.fit_transform(df[col])

    
    num_cols = ['Rainfall', 'Temperature', 'Humidity', 'Nitrogen', 'Phosphorus', 'Potassium', 'pH']
    existing_num_cols = [col for col in num_cols if col in df.columns]
    if existing_num_cols:
        scaler = StandardScaler()
        df[existing_num_cols] = scaler.fit_transform(df[existing_num_cols])

    return df
