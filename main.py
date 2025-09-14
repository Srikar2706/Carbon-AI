#!/usr/bin/env python3
"""
Agentic AI Carbon Ranker MVP
Main entry point for the application
"""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.api.routes import router
from src.api.chat_routes import router as chat_router
from src.api.messy_data_routes import router as messy_data_router
from src.database.init_db import init_database
from src.agent.carbon_ranker import CarbonRankerAgent

app = FastAPI(
    title="Agentic AI Carbon Ranker",
    description="MVP for ranking AI vendors by carbon efficiency",
    version="1.0.0"
)

# Include API routes
app.include_router(router, prefix="/api")
app.include_router(chat_router)
app.include_router(messy_data_router)

# Mount static files
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount data files
app.mount("/data", StaticFiles(directory="data"), name="data")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard"""
    with open("src/templates/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.on_event("startup")
async def startup_event():
    """Initialize database and run initial processing"""
    init_database()
    
    # Initialize and run the carbon ranker agent
    agent = CarbonRankerAgent()
    await agent.process_all_data()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
