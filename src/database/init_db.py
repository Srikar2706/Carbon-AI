"""
Database initialization and setup
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, GridIntensity
from ..data.mock_data import generate_grid_intensity_data

# Database configuration
DATABASE_URL = "sqlite:///./carbon_ranker.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database tables and seed with initial data"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Seed grid intensity data
    db = SessionLocal()
    try:
        # Check if grid intensity data already exists
        existing = db.query(GridIntensity).first()
        if not existing:
            grid_data = generate_grid_intensity_data()
            for _, row in grid_data.iterrows():
                grid_intensity = GridIntensity(
                    region=row['region'],
                    g_per_kwh=row['g_per_kwh'],
                    description=row['description']
                )
                db.add(grid_intensity)
            db.commit()
            print("Grid intensity data seeded successfully")
        else:
            print("Grid intensity data already exists")
    except Exception as e:
        print(f"Error seeding grid intensity data: {e}")
        db.rollback()
    finally:
        db.close()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
