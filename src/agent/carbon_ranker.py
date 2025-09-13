"""
Main Carbon Ranker Agent
Orchestrates the Planner → Executor → Critic loop
"""

import asyncio
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from ..database.models import RawIngest, NormalizedEvents, MonthlyCompanyRollup, Rankings, GridIntensity, ProcessingLog
from ..database.init_db import SessionLocal
from .planner import DataPlanner
from .executor import DataExecutor
from .critic import DataCritic
from ..data.mock_data import generate_all_mock_data
import pandas as pd
import json

class CarbonRankerAgent:
    """Main agentic system for carbon ranking"""
    
    def __init__(self):
        self.planner = DataPlanner()
        self.executor = DataExecutor()
        self.critic = DataCritic()
        self.db = SessionLocal()
    
    async def process_all_data(self):
        """Main entry point - process all vendor data"""
        print("🤖 Starting Carbon Ranker Agent...")
        
        # Generate and load mock data
        await self._load_mock_data()
        
        # Process each raw record
        raw_records = self.db.query(RawIngest).filter(RawIngest.processed == False).all()
        
        for record in raw_records:
            await self._process_record(record)
        
        # Generate monthly rollups
        await self._generate_monthly_rollups()
        
        # Generate rankings
        await self._generate_rankings()
        
        print("✅ Carbon Ranker Agent processing complete!")
    
    async def _load_mock_data(self):
        """Load mock data into database"""
        print("📊 Loading mock vendor data...")
        
        # Check if data already exists
        existing = self.db.query(RawIngest).first()
        if existing:
            print("Mock data already loaded")
            return
        
        # Generate mock data
        mock_data = generate_all_mock_data()
        
        # Load into database
        for _, row in mock_data.iterrows():
            raw_record = RawIngest(
                company=row['company'],
                month=row['month'],
                region=row['region'],
                gpu_hours_raw=row['gpu_hours_raw'],
                energy_raw=row['energy_raw'],
                tokens_raw=row['tokens_raw'],
                api_calls_raw=row['api_calls_raw'],
                pue_raw=row['pue_raw'],
                utilization_raw=row['utilization_raw']
            )
            self.db.add(raw_record)
        
        self.db.commit()
        print(f"✅ Loaded {len(mock_data)} mock records")
    
    async def _process_record(self, raw_record: RawIngest):
        """Process a single raw record through the agent loop"""
        print(f"🔄 Processing {raw_record.company} - {raw_record.month}")
        
        retry_count = 0
        max_retries = 3
        
        while retry_count <= max_retries:
            try:
                # Get grid intensity for region
                grid_intensity = self._get_grid_intensity(raw_record.region)
                
                # Convert to dict for processing
                record_dict = {
                    "company": raw_record.company,
                    "month": raw_record.month,
                    "region": raw_record.region,
                    "gpu_hours_raw": raw_record.gpu_hours_raw,
                    "energy_raw": raw_record.energy_raw,
                    "tokens_raw": raw_record.tokens_raw,
                    "api_calls_raw": raw_record.api_calls_raw,
                    "pue_raw": raw_record.pue_raw,
                    "utilization_raw": raw_record.utilization_raw
                }
                
                # PLANNER: Detect issues and plan strategy
                detection_result = self.planner.detect_issues(record_dict)
                strategy = self.planner.plan_normalization_strategy(detection_result)
                
                self._log_processing(raw_record, "planner", "detection", 
                                   f"Detected {len(detection_result.issues)} issues", retry_count)
                
                # EXECUTOR: Execute normalization
                execution_result = self.executor.execute_normalization(
                    record_dict, grid_intensity, strategy
                )
                
                if not execution_result.success:
                    self._log_processing(raw_record, "executor", "normalization_failed",
                                       f"Errors: {execution_result.errors}", retry_count)
                    retry_count += 1
                    continue
                
                # CRITIC: Validate results
                critique_result = self.critic.critique_results(
                    execution_result, execution_result.normalized_data, retry_count
                )
                
                self._log_processing(raw_record, "critic", "validation",
                                   f"Quality: {critique_result.quality_score:.1f}, Issues: {len(critique_result.issues)}", 
                                   retry_count)
                
                # Check if retry is needed
                if critique_result.retry_needed and retry_count < max_retries:
                    print(f"  🔄 Retry {retry_count + 1}/{max_retries}: {critique_result.retry_reason}")
                    retry_count += 1
                    continue
                
                # Save successful result
                if execution_result.normalized_data:
                    await self._save_normalized_data(raw_record, execution_result.normalized_data)
                    raw_record.processed = True
                    self.db.commit()
                    
                    print(f"  ✅ Success: Quality {critique_result.quality_score:.1f}")
                    break
                
            except Exception as e:
                print(f"  ❌ Error processing record: {str(e)}")
                self._log_processing(raw_record, "error", "exception", str(e), retry_count)
                retry_count += 1
        
        if retry_count > max_retries:
            print(f"  ⚠️ Max retries exceeded for {raw_record.company}")
            raw_record.processed = True  # Mark as processed to avoid infinite loop
            self.db.commit()
    
    def _get_grid_intensity(self, region: str) -> float:
        """Get grid carbon intensity for a region"""
        grid_data = self.db.query(GridIntensity).filter(GridIntensity.region == region).first()
        if grid_data:
            return grid_data.g_per_kwh
        
        # Fallback to market average
        fallback = self.db.query(GridIntensity).filter(GridIntensity.region == "UNKNOWN").first()
        return fallback.g_per_kwh if fallback else 400.0
    
    async def _save_normalized_data(self, raw_record: RawIngest, normalized_data: Dict[str, Any]):
        """Save normalized data to database"""
        normalized_event = NormalizedEvents(
            company=normalized_data["company"],
            month=normalized_data["month"],
            region=normalized_data["region"],
            gpu_hours=normalized_data["gpu_hours"],
            utilization=normalized_data["utilization"],
            it_kwh=normalized_data["it_kwh"],
            total_kwh=normalized_data["total_kwh"],
            intensity_g_per_kwh=normalized_data["intensity_g_per_kwh"],
            tco2e=normalized_data["tco2e"],
            tokens=normalized_data["tokens"],
            api_calls=normalized_data["api_calls"],
            pue_used=normalized_data["pue_used"],
            data_quality=normalized_data["data_quality"],
            imputation_log=json.dumps(normalized_data.get("imputation_log", {})),
            raw_ingest_id=raw_record.id
        )
        self.db.add(normalized_event)
        self.db.commit()
    
    def _log_processing(self, raw_record: RawIngest, stage: str, action: str, 
                       details: str, retry_count: int):
        """Log processing decisions"""
        log_entry = ProcessingLog(
            company=raw_record.company,
            month=raw_record.month,
            stage=stage,
            action=action,
            details=details,
            retry_count=retry_count
        )
        self.db.add(log_entry)
        self.db.commit()
    
    async def _generate_monthly_rollups(self):
        """Generate monthly company rollups"""
        print("📈 Generating monthly rollups...")
        
        # Clear existing rollups
        self.db.query(MonthlyCompanyRollup).delete()
        
        # Get all normalized events
        events = self.db.query(NormalizedEvents).all()
        
        # Group by company and month
        rollup_data = {}
        for event in events:
            key = (event.company, event.month)
            if key not in rollup_data:
                rollup_data[key] = []
            rollup_data[key].append(event)
        
        # Create rollups
        for (company, month), event_list in rollup_data.items():
            rollup = self._create_monthly_rollup(company, month, event_list)
            self.db.add(rollup)
        
        self.db.commit()
        print(f"✅ Generated {len(rollup_data)} monthly rollups")
    
    def _create_monthly_rollup(self, company: str, month: str, events: List[NormalizedEvents]) -> MonthlyCompanyRollup:
        """Create a monthly rollup from events"""
        total_kwh = sum(e.total_kwh for e in events)
        total_tco2e = sum(e.tco2e for e in events)
        total_tokens = sum(e.tokens or 0 for e in events)
        total_api_calls = sum(e.api_calls or 0 for e in events)
        avg_utilization = sum(e.utilization for e in events) / len(events)
        avg_pue = sum(e.pue_used for e in events) / len(events)
        avg_quality = sum(e.data_quality for e in events) / len(events)
        
        # Calculate intensity metrics
        g_per_1k_tokens = None
        if total_tokens > 0:
            g_per_1k_tokens = (total_tco2e * 1_000_000) / (total_tokens / 1000)
        
        g_per_call = None
        if total_api_calls > 0:
            g_per_call = (total_tco2e * 1_000_000) / total_api_calls
        
        tokens_per_tco2e = None
        if total_tco2e > 0:
            tokens_per_tco2e = total_tokens / total_tco2e
        
        return MonthlyCompanyRollup(
            company=company,
            month=month,
            total_kwh=total_kwh,
            tco2e=total_tco2e,
            g_per_1k_tokens=g_per_1k_tokens,
            g_per_call=g_per_call,
            tokens_per_tco2e=tokens_per_tco2e,
            utilization_avg=avg_utilization,
            pue_used=avg_pue,
            data_quality=avg_quality,
            total_tokens=total_tokens,
            total_api_calls=total_api_calls
        )
    
    async def _generate_rankings(self):
        """Generate final vendor rankings"""
        print("🏆 Generating vendor rankings...")
        
        # Clear existing rankings
        self.db.query(Rankings).delete()
        
        # Get latest month's rollups
        latest_month = self.db.query(MonthlyCompanyRollup.month).order_by(MonthlyCompanyRollup.month.desc()).first()
        if not latest_month:
            print("No rollup data available for rankings")
            return
        
        latest_month = latest_month[0]
        rollups = self.db.query(MonthlyCompanyRollup).filter(
            MonthlyCompanyRollup.month == latest_month
        ).all()
        
        if not rollups:
            print("No rollups found for latest month")
            return
        
        # Calculate Green Scores and ranks
        rankings_data = []
        for rollup in rollups:
            green_score = self._calculate_green_score(rollup)
            rankings_data.append({
                "rollup": rollup,
                "green_score": green_score
            })
        
        # Sort by Green Score (higher is better)
        rankings_data.sort(key=lambda x: x["green_score"], reverse=True)
        
        # Create ranking records
        for i, data in enumerate(rankings_data):
            rollup = data["rollup"]
            green_score = data["green_score"]
            
            # Calculate individual ranks (lower is better for emissions)
            tco2e_rank = sum(1 for r in rankings_data if r["rollup"].tco2e < rollup.tco2e) + 1
            intensity_rank = sum(1 for r in rankings_data 
                               if r["rollup"].g_per_1k_tokens and rollup.g_per_1k_tokens 
                               and r["rollup"].g_per_1k_tokens < rollup.g_per_1k_tokens) + 1
            efficiency_rank = sum(1 for r in rankings_data 
                                if r["rollup"].tokens_per_tco2e and rollup.tokens_per_tco2e
                                and r["rollup"].tokens_per_tco2e > rollup.tokens_per_tco2e) + 1
            utilization_rank = sum(1 for r in rankings_data 
                                 if r["rollup"].utilization_avg > rollup.utilization_avg) + 1
            
            ranking = Rankings(
                company=rollup.company,
                month=rollup.month,
                green_score=green_score,
                overall_rank=i + 1,
                tco2e_rank=tco2e_rank,
                intensity_rank=intensity_rank,
                efficiency_rank=efficiency_rank,
                utilization_rank=utilization_rank,
                total_kwh=rollup.total_kwh,
                tco2e=rollup.tco2e,
                g_per_1k_tokens=rollup.g_per_1k_tokens,
                tokens_per_tco2e=rollup.tokens_per_tco2e,
                utilization_avg=rollup.utilization_avg,
                data_quality=rollup.data_quality
            )
            self.db.add(ranking)
        
        self.db.commit()
        print(f"✅ Generated rankings for {len(rankings_data)} companies")
    
    def _calculate_green_score(self, rollup: MonthlyCompanyRollup) -> float:
        """Calculate Green Score (0-100, higher is better)"""
        # Normalize metrics (lower is better for emissions, higher is better for utilization)
        max_tco2e = max(r.tco2e for r in self.db.query(MonthlyCompanyRollup).all())
        max_intensity = max(r.g_per_1k_tokens for r in self.db.query(MonthlyCompanyRollup).all() 
                          if r.g_per_1k_tokens is not None)
        max_utilization = 100.0  # Theoretical maximum
        
        # Calculate normalized scores (0-1, higher is better)
        tco2e_score = 1 - (rollup.tco2e / max_tco2e) if max_tco2e > 0 else 0
        intensity_score = 1 - (rollup.g_per_1k_tokens / max_intensity) if rollup.g_per_1k_tokens and max_intensity > 0 else 0
        utilization_score = rollup.utilization_avg / max_utilization
        
        # Weighted composite score: 40% tCO2e + 40% intensity + 20% utilization
        green_score = (0.4 * tco2e_score + 0.4 * intensity_score + 0.2 * utilization_score) * 100
        
        return min(100.0, max(0.0, green_score))
