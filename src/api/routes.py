"""
API routes for the Carbon Ranker dashboard
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database.init_db import get_db
from ..database.models import Rankings, MonthlyCompanyRollup, NormalizedEvents, ProcessingLog
import json

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
