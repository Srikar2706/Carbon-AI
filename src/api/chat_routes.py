"""
Chat API routes for AI Carbon Assistant
"""
import os
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import anthropic
from ..database.init_db import get_db
from sqlalchemy.orm import Session

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    success: bool

def get_claude_client():
    """Get Claude API client"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="Claude API key not configured. Please set ANTHROPIC_API_KEY environment variable."
        )
    return anthropic.Anthropic(api_key=api_key)

def create_system_prompt(context: Optional[Dict[str, Any]] = None) -> str:
    """Create system prompt with carbon efficiency data context"""
    
    base_prompt = """You are an AI Carbon Assistant for the Agentic AI Carbon Ranker dashboard. You help users understand carbon efficiency data, vendor rankings, and environmental impact metrics.

Your role is to:
1. Analyze and explain carbon efficiency rankings
2. Interpret environmental metrics (tCO₂e, Green Scores, utilization rates)
3. Provide insights about vendor performance
4. Answer questions about data quality and methodology
5. Suggest improvements for carbon efficiency

Always be helpful, accurate, and focus on environmental sustainability. Use the provided data context to give specific, data-driven answers."""

    if context:
        # Add data context to the prompt
        context_str = f"""

CURRENT DATA CONTEXT:
- Total Companies: {context.get('summary', {}).get('total_companies', 'N/A')}
- Total Carbon Emissions: {context.get('summary', {}).get('total_tco2e', 'N/A')} tCO₂e
- Average Utilization: {context.get('summary', {}).get('avg_utilization', 'N/A')}%
- Average Data Quality: {context.get('summary', {}).get('avg_data_quality', 'N/A')}%

TOP PERFORMERS:
- Best Green Score: {context.get('bestPerformers', {}).get('green_score', {}).get('company', 'N/A')} ({context.get('bestPerformers', {}).get('green_score', {}).get('score', 'N/A')}/100)
- Lowest Emissions: {context.get('bestPerformers', {}).get('lowest_emissions', {}).get('company', 'N/A')} ({context.get('bestPerformers', {}).get('lowest_emissions', {}).get('tco2e', 'N/A')} tCO₂e)

VENDOR RANKINGS:
"""
        
        # Add top 5 vendors from leaderboard
        leaderboard = context.get('leaderboard', [])
        for i, vendor in enumerate(leaderboard[:5], 1):
            context_str += f"{i}. {vendor.get('company', 'N/A')} - Green Score: {vendor.get('green_score', 'N/A')}/100, Emissions: {vendor.get('tco2e', 'N/A')} tCO₂e, Utilization: {vendor.get('utilization', 'N/A')}%\n"
        
        base_prompt += context_str

    return base_prompt

@router.post("/api/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat with AI Carbon Assistant using Claude API
    """
    try:
        # Get Claude client
        client = get_claude_client()
        
        # Create system prompt with context
        system_prompt = create_system_prompt(request.context)
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": request.message
                }
            ]
        )
        
        # Extract response text
        ai_response = response.content[0].text if response.content else "I'm sorry, I couldn't generate a response."
        
        return ChatResponse(
            response=ai_response,
            success=True
        )
        
    except anthropic.APIError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Claude API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )

@router.get("/api/chat/health")
async def chat_health_check():
    """Health check for chat service"""
    try:
        # Check if API key is configured
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return {
                "status": "error",
                "message": "Claude API key not configured"
            }
        
        return {
            "status": "healthy",
            "message": "Chat service is ready"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Chat service error: {str(e)}"
        }
