"""
API routes for the Carbon Ranker dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..database.init_db import get_db
from ..database.models import Rankings, MonthlyCompanyRollup, NormalizedEvents, ProcessingLog, RawIngest
import json
import pandas as pd
import io
import time
from datetime import datetime

router = APIRouter()

@router.get("/leaderboard")
async def get_leaderboard(db: Session = Depends(get_db)):
    """Get the vendor leaderboard with rankings"""
    try:
        # Get latest rankings
        latest_month = db.query(Rankings.month).order_by(Rankings.month.desc()).first()
        if not latest_month:
            return {"error": "No rankings available"}
        
        latest_month = latest_month[0]
        rankings = db.query(Rankings).filter(
            Rankings.month == latest_month
        ).order_by(Rankings.overall_rank).all()
        
        leaderboard = []
        for ranking in rankings:
            leaderboard.append({
                "company": ranking.company,
                "rank": ranking.overall_rank,
                "green_score": round(ranking.green_score, 1),
                "tco2e": round(ranking.tco2e, 3),
                "g_per_1k_tokens": round(ranking.g_per_1k_tokens, 2) if ranking.g_per_1k_tokens else None,
                "tokens_per_tco2e": round(ranking.tokens_per_tco2e, 0) if ranking.tokens_per_tco2e else None,
                "utilization": round(ranking.utilization_avg, 1),
                "data_quality": round(ranking.data_quality, 1),
                "total_kwh": round(ranking.total_kwh, 1)
            })
        
        return {
            "month": latest_month,
            "leaderboard": leaderboard
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company/{company_name}")
async def get_company_details(company_name: str, db: Session = Depends(get_db)):
    """Get detailed metrics for a specific company"""
    try:
        # Get latest month
        latest_month = db.query(Rankings.month).order_by(Rankings.month.desc()).first()
        if not latest_month:
            raise HTTPException(status_code=404, detail="No data available")
        
        latest_month = latest_month[0]
        
        # Get ranking
        ranking = db.query(Rankings).filter(
            Rankings.company == company_name,
            Rankings.month == latest_month
        ).first()
        
        if not ranking:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get monthly rollup
        rollup = db.query(MonthlyCompanyRollup).filter(
            MonthlyCompanyRollup.company == company_name,
            MonthlyCompanyRollup.month == latest_month
        ).first()
        
        # Get recent events for trend data
        events = db.query(NormalizedEvents).filter(
            NormalizedEvents.company == company_name,
            NormalizedEvents.month == latest_month
        ).order_by(NormalizedEvents.created_at.desc()).limit(10).all()
        
        # Get processing log
        processing_log = db.query(ProcessingLog).filter(
            ProcessingLog.company == company_name,
            ProcessingLog.month == latest_month
        ).order_by(ProcessingLog.created_at.desc()).limit(5).all()
        
        # Build response
        details = {
            "company": company_name,
            "month": latest_month,
            "ranking": {
                "overall_rank": ranking.overall_rank,
                "green_score": round(ranking.green_score, 1),
                "tco2e_rank": ranking.tco2e_rank,
                "intensity_rank": ranking.intensity_rank,
                "efficiency_rank": ranking.efficiency_rank,
                "utilization_rank": ranking.utilization_rank
            },
            "metrics": {
                "total_kwh": round(ranking.total_kwh, 1),
                "tco2e": round(ranking.tco2e, 3),
                "g_per_1k_tokens": round(ranking.g_per_1k_tokens, 2) if ranking.g_per_1k_tokens else None,
                "tokens_per_tco2e": round(ranking.tokens_per_tco2e, 0) if ranking.tokens_per_tco2e else None,
                "utilization_avg": round(ranking.utilization_avg, 1),
                "data_quality": round(ranking.data_quality, 1)
            },
            "rollup": {
                "total_tokens": rollup.total_tokens,
                "total_api_calls": rollup.total_api_calls,
                "pue_used": round(rollup.pue_used, 2),
                "g_per_call": round(rollup.g_per_call, 2) if rollup.g_per_call else None
            } if rollup else None,
            "recent_events": [
                {
                    "date": event.created_at.strftime("%Y-%m-%d %H:%M"),
                    "gpu_hours": event.gpu_hours,
                    "utilization": event.utilization,
                    "total_kwh": round(event.total_kwh, 1),
                    "tco2e": round(event.tco2e, 3),
                    "data_quality": round(event.data_quality, 1)
                }
                for event in events
            ],
            "processing_log": [
                {
                    "stage": log.stage,
                    "action": log.action,
                    "details": log.details,
                    "retry_count": log.retry_count,
                    "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
                for log in processing_log
            ]
        }
        
        return details
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/summary")
async def get_metrics_summary(db: Session = Depends(get_db)):
    """Get summary metrics across all companies"""
    try:
        # Get latest month
        latest_month = db.query(Rankings.month).order_by(Rankings.month.desc()).first()
        if not latest_month:
            return {"error": "No data available"}
        
        latest_month = latest_month[0]
        
        # Get all rankings for the month
        rankings = db.query(Rankings).filter(Rankings.month == latest_month).all()
        
        if not rankings:
            return {"error": "No rankings available"}
        
        # Calculate summary statistics
        total_companies = len(rankings)
        total_tco2e = sum(r.tco2e for r in rankings)
        total_kwh = sum(r.total_kwh for r in rankings)
        avg_utilization = sum(r.utilization_avg for r in rankings) / total_companies
        avg_data_quality = sum(r.data_quality for r in rankings) / total_companies
        
        # Find best and worst performers
        best_green_score = max(rankings, key=lambda r: r.green_score)
        worst_green_score = min(rankings, key=lambda r: r.green_score)
        
        lowest_emissions = min(rankings, key=lambda r: r.tco2e)
        highest_emissions = max(rankings, key=lambda r: r.tco2e)
        
        return {
            "month": latest_month,
            "summary": {
                "total_companies": total_companies,
                "total_tco2e": round(total_tco2e, 3),
                "total_kwh": round(total_kwh, 1),
                "avg_utilization": round(avg_utilization, 1),
                "avg_data_quality": round(avg_data_quality, 1)
            },
            "best_performers": {
                "green_score": {
                    "company": best_green_score.company,
                    "score": round(best_green_score.green_score, 1)
                },
                "lowest_emissions": {
                    "company": lowest_emissions.company,
                    "tco2e": round(lowest_emissions.tco2e, 3)
                }
            },
            "worst_performers": {
                "green_score": {
                    "company": worst_green_score.company,
                    "score": round(worst_green_score.green_score, 1)
                },
                "highest_emissions": {
                    "company": highest_emissions.company,
                    "tco2e": round(highest_emissions.tco2e, 3)
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing/status")
async def get_processing_status(db: Session = Depends(get_db)):
    """Get processing status and recent activity"""
    try:
        # Get recent processing logs
        recent_logs = db.query(ProcessingLog).order_by(
            ProcessingLog.created_at.desc()
        ).limit(20).all()
        
        # Get processing statistics
        total_processed = db.query(ProcessingLog).count()
        retry_count = db.query(ProcessingLog).filter(ProcessingLog.retry_count > 0).count()
        error_count = db.query(ProcessingLog).filter(ProcessingLog.success == False).count()
        
        return {
            "processing_stats": {
                "total_processed": total_processed,
                "retry_count": retry_count,
                "error_count": error_count
            },
            "recent_activity": [
                {
                    "company": log.company,
                    "stage": log.stage,
                    "action": log.action,
                    "details": log.details,
                    "retry_count": log.retry_count,
                    "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
                for log in recent_logs
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    format: str = Form("csv"),
    auto_process: bool = Form(True),
    overwrite_existing: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Upload and process vendor data file"""
    start_time = time.time()
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size (10MB limit)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Validate file extension
        file_extension = file.filename.split('.')[-1].lower()
        allowed_extensions = ['csv', 'json', 'xlsx', 'xls']
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Parse file based on format
        try:
            if file_extension == 'csv':
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            elif file_extension == 'json':
                df = pd.read_json(io.StringIO(content.decode('utf-8')))
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")
        
        # Validate required columns
        required_columns = ['company', 'month', 'region']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Process the data
        records_processed = 0
        companies_added = set()
        warnings = []
        
        for _, row in df.iterrows():
            try:
                # Check if record already exists
                existing = db.query(RawIngest).filter(
                    RawIngest.company == row['company'],
                    RawIngest.month == row['month']
                ).first()
                
                if existing and not overwrite_existing:
                    warnings.append(f"Record for {row['company']} ({row['month']}) already exists, skipping")
                    continue
                
                # Create or update raw ingest record
                raw_data = {
                    'company': str(row['company']),
                    'month': str(row['month']),
                    'region': str(row['region']),
                    'gpu_hours_raw': str(row.get('gpu_hours', '')),
                    'energy_raw': str(row.get('energy', '')),
                    'tokens_raw': str(row.get('tokens', '')),
                    'api_calls_raw': str(row.get('api_calls', '')),
                    'pue_raw': str(row.get('pue', '')),
                    'utilization_raw': str(row.get('utilization', '')),
                    'processed': False
                }
                
                if existing and overwrite_existing:
                    # Update existing record
                    for key, value in raw_data.items():
                        setattr(existing, key, value)
                    existing.created_at = datetime.now()
                else:
                    # Create new record
                    raw_record = RawIngest(**raw_data)
                    db.add(raw_record)
                
                records_processed += 1
                companies_added.add(row['company'])
                
            except Exception as e:
                warnings.append(f"Error processing row for {row.get('company', 'unknown')}: {str(e)}")
                continue
        
        # Commit changes
        db.commit()
        
        # Auto-process if requested
        if auto_process and records_processed > 0:
            try:
                from ..agent.carbon_ranker import CarbonRankerAgent
                agent = CarbonRankerAgent()
                await agent.process_all_data()
            except Exception as e:
                warnings.append(f"Auto-processing failed: {str(e)}")
        
        processing_time = f"{time.time() - start_time:.2f}s"
        
        return {
            "success": True,
            "records_processed": records_processed,
            "companies_added": len(companies_added),
            "processing_time": processing_time,
            "warnings": warnings,
            "message": f"Successfully uploaded {records_processed} records for {len(companies_added)} companies"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/reset")
async def reset_leaderboard(db: Session = Depends(get_db)):
    """Reset the leaderboard by clearing all data"""
    try:
        # Clear all tables in order (respecting foreign key constraints)
        db.query(Rankings).delete()
        db.query(MonthlyCompanyRollup).delete()
        db.query(NormalizedEvents).delete()
        db.query(ProcessingLog).delete()
        db.query(RawIngest).delete()
        
        db.commit()
        
        return {"message": "Leaderboard reset successfully", "success": True}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting leaderboard: {str(e)}")

@router.post("/upload-messy-data")
async def upload_messy_data(
    file: UploadFile = File(...),
    add_to_ranking: str = Form("false"),
    db: Session = Depends(get_db)
):
    """Upload messy data file and process it through LLM cleaning pipeline"""
    try:
        # Check file type
        if not file.filename.endswith(('.json', '.csv', '.txt', '.pdf')):
            raise HTTPException(status_code=400, detail="Only JSON, CSV, TXT, and PDF files are supported")
        
        # Read file content
        content = await file.read()
        
        # Parse based on file type
        if file.filename.endswith('.json'):
            try:
                messy_data = json.loads(content.decode('utf-8'))
                if not isinstance(messy_data, list):
                    messy_data = [messy_data]
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
        elif file.filename.endswith('.csv'):
            try:
                df = pd.read_csv(io.StringIO(content.decode('utf-8')))
                messy_data = df.to_dict('records')
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
        elif file.filename.endswith('.txt'):
            try:
                text_content = content.decode('utf-8')
                # Convert text to structured data for LLM processing
                messy_data = [{"raw_text": text_content, "filename": file.filename}]
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid text file: {str(e)}")
        elif file.filename.endswith('.pdf'):
            try:
                import PyPDF2
                import pdfplumber
                
                # Try pdfplumber first (better for text extraction)
                try:
                    with pdfplumber.open(io.BytesIO(content)) as pdf:
                        text_content = ""
                        for page in pdf.pages:
                            text_content += page.extract_text() or ""
                except:
                    # Fallback to PyPDF2
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                    text_content = ""
                    for page in pdf_reader.pages:
                        text_content += page.extract_text()
                
                if not text_content.strip():
                    raise HTTPException(status_code=400, detail="No text content found in PDF")
                
                # Convert PDF text to structured data for LLM processing
                messy_data = [{"raw_text": text_content, "filename": file.filename}]
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")
        
        # Initialize LLM cleaner
        from ..llm_agents.data_cleaner import LLMDataCleaner
        import os
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM cleaning not available - no API key configured")
        
        llm_cleaner = LLMDataCleaner(api_key)
        
        # Clean the data
        print(f"Processing {len(messy_data)} messy records...")
        cleaned_data = llm_cleaner.clean_messy_data(messy_data)
        
        if not cleaned_data:
            raise HTTPException(status_code=500, detail="LLM cleaning failed - no data returned")
        
        # Get cleaning stats
        stats = llm_cleaner.get_cleaning_stats()
        
        # Convert string to boolean
        add_to_ranking_bool = add_to_ranking.lower() == 'true'
        
        result = {
            "success": True,
            "message": f"Successfully processed {len(cleaned_data)} records",
            "cleaning_stats": stats,
            "records_processed": len(cleaned_data),
            "clean_csv": llm_cleaner.generate_clean_csv_data(cleaned_data),
            "add_to_ranking": add_to_ranking_bool
        }
        
        # Only add to ranking pool if requested
        if add_to_ranking_bool:
            # Store cleaned data in database
            from ..agent.carbon_ranker import CarbonRankerAgent
            agent = CarbonRankerAgent()
            
            # Store the cleaned data
            await agent._store_cleaned_data(cleaned_data, "manual_upload")
            
            # Process through normal pipeline
            print("Processing through normal pipeline...")
            await agent._generate_monthly_rollups()
            await agent._generate_rankings()
            
            result["ranking_updated"] = True
            result["message"] += " and added to ranking pool"
        else:
            result["ranking_updated"] = False
            result["message"] += " (not added to ranking pool)"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing messy data: {str(e)}")
