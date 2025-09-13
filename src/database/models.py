"""
Rox data models for the Carbon Ranker system
Implements the 4-stage data pipeline: raw → normalized → rollup → rankings
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()

class RawIngest(Base):
    """Raw vendor data as ingested from various sources"""
    __tablename__ = "raw_ingest"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)  # YYYY-MM format
    region = Column(String(20), nullable=False)
    gpu_hours_raw = Column(String(50), nullable=True)
    energy_raw = Column(String(50), nullable=True)
    tokens_raw = Column(String(50), nullable=True)
    api_calls_raw = Column(String(50), nullable=True)
    pue_raw = Column(String(20), nullable=True)
    utilization_raw = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.now())
    processed = Column(Boolean, default=False)

class NormalizedEvents(Base):
    """Normalized and cleaned operational data"""
    __tablename__ = "normalized_events"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)
    region = Column(String(20), nullable=False)
    gpu_hours = Column(Float, nullable=False)
    utilization = Column(Float, nullable=False)  # 0-100 percentage
    it_kwh = Column(Float, nullable=False)  # IT energy consumption
    total_kwh = Column(Float, nullable=False)  # Total including PUE
    intensity_g_per_kwh = Column(Float, nullable=False)  # Grid carbon intensity
    tco2e = Column(Float, nullable=False)  # Total CO2 equivalent in tonnes
    tokens = Column(Float, nullable=True)  # Total tokens processed
    api_calls = Column(Integer, nullable=True)
    pue_used = Column(Float, nullable=False)  # PUE factor applied
    data_quality = Column(Float, nullable=False)  # 0-100 quality score
    imputation_log = Column(Text, nullable=True)  # JSON log of imputations made
    created_at = Column(DateTime, default=func.now())
    raw_ingest_id = Column(Integer, nullable=True)  # Link to source record

class MonthlyCompanyRollup(Base):
    """Monthly aggregated metrics per company"""
    __tablename__ = "monthly_company_rollup"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)
    total_kwh = Column(Float, nullable=False)
    tco2e = Column(Float, nullable=False)
    g_per_1k_tokens = Column(Float, nullable=True)  # Intensity per 1k tokens
    g_per_call = Column(Float, nullable=True)  # Intensity per API call
    tokens_per_tco2e = Column(Float, nullable=True)  # Efficiency metric
    utilization_avg = Column(Float, nullable=False)
    pue_used = Column(Float, nullable=False)
    data_quality = Column(Float, nullable=False)
    total_tokens = Column(Float, nullable=True)
    total_api_calls = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())

class Rankings(Base):
    """Final vendor rankings and Green Scores"""
    __tablename__ = "rankings"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)
    green_score = Column(Float, nullable=False)  # 0-100 composite score
    overall_rank = Column(Integer, nullable=False, index=True)
    tco2e_rank = Column(Integer, nullable=False)
    intensity_rank = Column(Integer, nullable=False)
    efficiency_rank = Column(Integer, nullable=False)
    utilization_rank = Column(Integer, nullable=False)
    total_kwh = Column(Float, nullable=False)
    tco2e = Column(Float, nullable=False)
    g_per_1k_tokens = Column(Float, nullable=True)
    tokens_per_tco2e = Column(Float, nullable=True)
    utilization_avg = Column(Float, nullable=False)
    data_quality = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

class GridIntensity(Base):
    """Grid carbon intensity by region"""
    __tablename__ = "grid_intensity"
    
    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(20), nullable=False, unique=True, index=True)
    g_per_kwh = Column(Float, nullable=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=func.now())

class ProcessingLog(Base):
    """Agent processing decisions and retry attempts"""
    __tablename__ = "processing_log"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(100), nullable=False, index=True)
    month = Column(String(7), nullable=False, index=True)
    stage = Column(String(20), nullable=False)  # planner, executor, critic
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
