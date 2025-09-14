"""
API routes for messy data processing and ROX competition demo
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio

from ..database.init_db import get_db
from ..agent.carbon_ranker import CarbonRankerAgent
from ..llm_agents.messy_data_handler import MessyDataHandler

router = APIRouter()

class MessyDataRequest(BaseModel):
    scenario: str
    count: int = 10

class MessyDataResponse(BaseModel):
    scenario: str
    input_data: List[Dict[str, Any]]
    cleaned_data: List[Dict[str, Any]]
    cleaning_stats: Dict[str, Any]
    success: bool

class DemoResponse(BaseModel):
    scenarios_tested: List[str]
    results: Dict[str, Any]
    summary: Dict[str, Any]
    success: bool

@router.post("/api/messy-data/process", response_model=MessyDataResponse)
async def process_messy_data(
    request: MessyDataRequest,
    db: Session = Depends(get_db)
):
    """
    Process messy data using LLM-powered cleaning
    """
    try:
        # Initialize agents
        agent = CarbonRankerAgent()
        messy_handler = MessyDataHandler()
        
        # Generate messy data
        messy_data = messy_handler.generate_messy_data(request.scenario, request.count)
        
        # Process with LLM
        result = await agent.process_messy_data(messy_data, request.scenario)
        
        if not result:
            raise HTTPException(status_code=500, detail="LLM data cleaning failed")
        
        return MessyDataResponse(
            scenario=request.scenario,
            input_data=messy_data,
            cleaned_data=result['cleaned_data'],
            cleaning_stats=result['cleaning_stats'],
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing messy data: {str(e)}")

@router.get("/api/messy-data/scenarios")
async def get_available_scenarios():
    """
    Get available messy data scenarios
    """
    handler = MessyDataHandler()
    scenarios = handler.get_available_scenarios()
    
    scenario_descriptions = {
        'aws_logs': 'AWS CloudWatch logs with inconsistent formatting',
        'azure_logs': 'Azure Monitor metrics with mixed data types',
        'gcp_logs': 'Google Cloud Operations logs with various formats',
        'mixed_providers': 'Mixed data from multiple cloud providers',
        'incomplete_data': 'Data with missing fields and incomplete information',
        'conflicting_sources': 'Conflicting data from different sources'
    }
    
    return {
        'scenarios': scenarios,
        'descriptions': scenario_descriptions,
        'total_scenarios': len(scenarios)
    }

@router.post("/api/messy-data/demo", response_model=DemoResponse)
async def run_data_transformation_demo(db: Session = Depends(get_db)):
    """
    Run the complete data transformation demo
    """
    try:
        # Initialize agent
        agent = CarbonRankerAgent()
        
        # Run data transformation scenarios
        results = await agent.demo_messy_data_scenarios()
        
        # Create summary
        total_scenarios = len(results)
        successful_scenarios = sum(1 for r in results.values() if r and r.get('cleaning_stats', {}).get('success_rate', 0) > 0.8)
        
        summary = {
            'total_scenarios': total_scenarios,
            'successful_scenarios': successful_scenarios,
            'success_rate': successful_scenarios / total_scenarios if total_scenarios > 0 else 0,
            'average_confidence': sum(r.get('cleaning_stats', {}).get('average_confidence', 0) for r in results.values() if r) / total_scenarios if total_scenarios > 0 else 0
        }
        
        return DemoResponse(
            scenarios_tested=list(results.keys()),
            results=results,
            summary=summary,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running data transformation demo: {str(e)}")

@router.get("/api/messy-data/sample/{scenario}")
async def get_sample_messy_data(scenario: str, count: int = 5):
    """
    Get sample messy data for a specific scenario
    """
    try:
        handler = MessyDataHandler()
        
        if scenario not in handler.get_available_scenarios():
            raise HTTPException(status_code=400, detail=f"Unknown scenario: {scenario}")
        
        sample_data = handler.generate_messy_data(scenario, count)
        
        return {
            'scenario': scenario,
            'count': len(sample_data),
            'sample_data': sample_data,
            'description': f"Sample {scenario} data with {count} records"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sample data: {str(e)}")

@router.get("/api/messy-data/realistic-scenario")
async def get_realistic_scenario():
    """
    Get a realistic messy data scenario for demo
    """
    try:
        handler = MessyDataHandler()
        scenario = handler.create_realistic_messy_scenario()
        
        return scenario
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating realistic scenario: {str(e)}")
