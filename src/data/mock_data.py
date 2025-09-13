"""
Mock data generator for different AI vendor formats
Simulates messy, inconsistent operational logs
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

def generate_grid_intensity_data() -> pd.DataFrame:
    """Generate grid carbon intensity data by region"""
    regions = [
        {"region": "US-East", "g_per_kwh": 350, "description": "US East Coast"},
        {"region": "US-West", "g_per_kwh": 180, "description": "US West Coast (renewable heavy)"},
        {"region": "CA-QC", "g_per_kwh": 25, "description": "Quebec, Canada (hydro)"},
        {"region": "EU-NL", "g_per_kwh": 420, "description": "Netherlands"},
        {"region": "EU-NO", "g_per_kwh": 15, "description": "Norway (renewable)"},
        {"region": "AP-SG", "g_per_kwh": 480, "description": "Singapore"},
        {"region": "AP-AU", "g_per_kwh": 750, "description": "Australia (coal heavy)"},
        {"region": "UNKNOWN", "g_per_kwh": 400, "description": "Market average fallback"}
    ]
    return pd.DataFrame(regions)

def generate_vendor_a_data() -> List[Dict[str, Any]]:
    """Vendor A: Clean format, some missing PUE data"""
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(30):  # 30 days of data
        date = base_date + timedelta(days=i)
        data.append({
            "company": "CloudAI-Pro",
            "month": date.strftime("%Y-%m"),
            "region": "US-East",
            "gpu_hours_raw": f"{random.randint(800, 1200)}",
            "energy_raw": f"{random.randint(320, 480)} kWh",  # Clean format
            "tokens_raw": f"{random.randint(8, 15)}.2B",  # Fuzzy format
            "api_calls_raw": f"{random.randint(10000, 50000)}",
            "pue_raw": "1.2" if random.random() > 0.3 else "",  # Some missing
            "utilization_raw": f"{random.randint(65, 95)}%"
        })
    
    return data

def generate_vendor_b_data() -> List[Dict[str, Any]]:
    """Vendor B: Messy format, mixed units, missing energy"""
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        # Sometimes use MWh instead of kWh
        energy_unit = "MWh" if random.random() > 0.7 else "kWh"
        energy_multiplier = 1000 if energy_unit == "MWh" else 1
        energy_value = random.randint(200, 400) * energy_multiplier
        
        data.append({
            "company": "DataForge-LLC",
            "month": date.strftime("%Y-%m"),
            "region": "US-West",
            "gpu_hours_raw": f"{random.randint(600, 1000)} hrs",  # Mixed format
            "energy_raw": f"{energy_value} {energy_unit}" if random.random() > 0.4 else "",  # Often missing
            "tokens_raw": f"{random.randint(5, 12)}M",  # Different token format
            "api_calls_raw": f"{random.randint(8000, 25000)}",
            "pue_raw": f"{random.uniform(1.1, 1.4):.2f}",
            "utilization_raw": f"{random.randint(45, 85)}"
        })
    
    return data

def generate_vendor_c_data() -> List[Dict[str, Any]]:
    """Vendor C: Very messy, lots of missing data, unknown region"""
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        data.append({
            "company": "GreenCompute-Inc",
            "month": date.strftime("%Y-%m"),
            "region": "CA-QC" if random.random() > 0.2 else "UNKNOWN",  # Sometimes unknown
            "gpu_hours_raw": f"{random.randint(400, 800)}",
            "energy_raw": "",  # Always missing - needs imputation
            "tokens_raw": f"{random.randint(3, 8)}.5B tokens",  # Very fuzzy
            "api_calls_raw": f"{random.randint(5000, 15000)} calls",
            "pue_raw": "",  # Always missing
            "utilization_raw": f"{random.randint(30, 70)}%"  # Low utilization
        })
    
    return data

def generate_vendor_d_data() -> List[Dict[str, Any]]:
    """Vendor D: European vendor with different format"""
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        data.append({
            "company": "EuroAI-Systems",
            "month": date.strftime("%Y-%m"),
            "region": "EU-NL",
            "gpu_hours_raw": f"{random.randint(1000, 1500)}",
            "energy_raw": f"{random.randint(500, 750)} kWh",
            "tokens_raw": f"{random.randint(10, 20)}B",  # Clean format
            "api_calls_raw": f"{random.randint(15000, 40000)}",
            "pue_raw": f"{random.uniform(1.3, 1.6):.1f}",
            "utilization_raw": f"{random.randint(70, 90)}%"
        })
    
    return data

def generate_all_mock_data() -> pd.DataFrame:
    """Generate all vendor data and combine into single DataFrame"""
    all_data = []
    
    # Generate data from all vendors
    all_data.extend(generate_vendor_a_data())
    all_data.extend(generate_vendor_b_data())
    all_data.extend(generate_vendor_c_data())
    all_data.extend(generate_vendor_d_data())
    
    return pd.DataFrame(all_data)

def save_mock_data():
    """Save mock data to CSV files"""
    # Create data directory if it doesn't exist
    import os
    os.makedirs("data", exist_ok=True)
    
    # Generate and save raw data
    raw_data = generate_all_mock_data()
    raw_data.to_csv("data/raw_vendor_data.csv", index=False)
    
    # Generate and save grid intensity data
    grid_data = generate_grid_intensity_data()
    grid_data.to_csv("data/grid_intensity.csv", index=False)
    
    print("Mock data generated and saved:")
    print(f"- Raw vendor data: {len(raw_data)} records")
    print(f"- Grid intensity data: {len(grid_data)} regions")
    print(f"- Companies: {raw_data['company'].unique()}")

if __name__ == "__main__":
    save_mock_data()
