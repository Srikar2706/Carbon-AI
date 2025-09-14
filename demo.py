#!/usr/bin/env python3
"""
Demo script for the Agentic AI Carbon Ranker MVP
Shows the complete workflow from messy data to vendor rankings
"""

import asyncio
import time
from src.agent.carbon_ranker import CarbonRankerAgent
from src.database.init_db import init_database, SessionLocal
from src.database.models import RawIngest, Rankings, ProcessingLog
from src.data.mock_data import generate_all_mock_data
import pandas as pd

class CarbonRankerDemo:
    """Interactive demo of the Carbon Ranker system"""
    
    def __init__(self):
        self.agent = CarbonRankerAgent()
        self.db = SessionLocal()
    
    async def run_demo(self):
        """Run the complete demo workflow"""
        print("🚀 Starting Agentic AI Carbon Ranker Demo")
        print("=" * 60)
        
        # Step 1: Show messy input data
        await self._show_messy_inputs()
        
        # Step 2: Run agent processing
        await self._run_agent_processing()
        
        # Step 3: Show results and rankings
        await self._show_rankings()
        
        # Step 4: Demonstrate retry scenarios
        await self._demonstrate_retries()
        
        # Step 5: Show procurement decision
        await self._show_procurement_story()
        
        print("\nDemo completed successfully!")
        print("Open http://localhost:8000 to view the dashboard")
    
    async def _show_messy_inputs(self):
        """Step 1: Display messy vendor data"""
        print("\nSTEP 1: Messy Vendor Data Input")
        print("-" * 40)
        
        # Generate and show sample of mock data
        mock_data = generate_all_mock_data()
        
        print("Raw vendor data with inconsistent formats:")
        print(f"Total records: {len(mock_data)}")
        print(f"Companies: {', '.join(mock_data['company'].unique())}")
        
        # Show sample of messy data
        print("\nSample of messy data formats:")
        sample = mock_data.head(3)
        for _, row in sample.iterrows():
            print(f"\n{row['company']} ({row['month']}):")
            print(f"  GPU Hours: '{row['gpu_hours_raw']}'")
            print(f"  Energy: '{row['energy_raw']}'")
            print(f"  Tokens: '{row['tokens_raw']}'")
            print(f"  PUE: '{row['pue_raw']}'")
            print(f"  Region: '{row['region']}'")
        
        print("\n🔍 Issues detected:")
        print("  • Mixed units (MWh vs kWh)")
        print("  • Missing energy data")
        print("  • Fuzzy token formats (11.3B, 5M)")
        print("  • Unknown regions")
        print("  • Inconsistent utilization formats")
        
        input("\nPress Enter to continue to agent processing...")
    
    async def _run_agent_processing(self):
        """Step 2: Run the agentic processing"""
        print("\nSTEP 2: Agentic Processing (Planner → Executor → Critic)")
        print("-" * 60)
        
        print("Initializing database and loading data...")
        init_database()
        
        print("Starting Carbon Ranker Agent...")
        start_time = time.time()
        
        # Run the agent
        await self.agent.process_all_data()
        
        end_time = time.time()
        print(f"Processing completed in {end_time - start_time:.2f} seconds")
        
        # Show processing statistics
        total_processed = self.db.query(RawIngest).count()
        retry_count = self.db.query(ProcessingLog).filter(ProcessingLog.retry_count > 0).count()
        error_count = self.db.query(ProcessingLog).filter(ProcessingLog.success == False).count()
        
        print(f"\nProcessing Statistics:")
        print(f"  • Total records processed: {total_processed}")
        print(f"  • Records requiring retry: {retry_count}")
        print(f"  • Processing errors: {error_count}")
        
        input("\nPress Enter to view results...")
    
    async def _show_rankings(self):
        """Step 3: Display vendor rankings"""
        print("\nSTEP 3: Vendor Rankings & Green Scores")
        print("-" * 50)
        
        # Get latest rankings
        latest_month = self.db.query(Rankings.month).order_by(Rankings.month.desc()).first()
        if not latest_month:
            print("No rankings available")
            return
        
        latest_month = latest_month[0]
        rankings = self.db.query(Rankings).filter(
            Rankings.month == latest_month
        ).order_by(Rankings.overall_rank).all()
        
        print(f"Rankings for {latest_month}:")
        print("\nRank | Company           | Green Score | tCO₂e | gCO₂/1k tokens | Utilization | Data Quality")
        print("-" * 90)
        
        for ranking in rankings:
            g_per_1k = f"{ranking.g_per_1k_tokens:.1f}" if ranking.g_per_1k_tokens else "N/A"
            print(f"{ranking.overall_rank:4d} | {ranking.company:17s} | {ranking.green_score:10.1f} | {ranking.tco2e:5.3f} | {g_per_1k:13s} | {ranking.utilization_avg:10.1f}% | {ranking.data_quality:11.1f}%")
        
        # Highlight best performer
        best = rankings[0]
        print(f"\n🥇 Best Performer: {best.company}")
        print(f"   Green Score: {best.green_score:.1f}/100")
        print(f"   Total Emissions: {best.tco2e:.3f} tCO₂e")
        print(f"   Data Quality: {best.data_quality:.1f}%")
        
        input("\nPress Enter to see retry scenarios...")
    
    async def _demonstrate_retries(self):
        """Step 4: Show retry scenarios"""
        print("\nSTEP 4: Agent Retry Scenarios")
        print("-" * 40)
        
        # Get processing logs with retries
        retry_logs = self.db.query(ProcessingLog).filter(
            ProcessingLog.retry_count > 0
        ).order_by(ProcessingLog.created_at.desc()).limit(5).all()
        
        if retry_logs:
            print("Examples of autonomous retry scenarios:")
            for log in retry_logs:
                print(f"\n{log.company} - {log.month}:")
                print(f"  Stage: {log.stage}")
                print(f"  Action: {log.action}")
                print(f"  Details: {log.details}")
                print(f"  Retry Count: {log.retry_count}")
        else:
            print("No retry scenarios found in this run")
        
        # Show data quality improvements
        print("\nData Quality Improvements:")
        print("  • Missing energy → Imputed from GPU hours")
        print("  • Unknown regions → Market average grid intensity")
        print("  • Invalid PUE → Default 1.3 applied")
        print("  • Fuzzy tokens → Parsed (k/M/B suffixes)")
        print("  • Mixed units → Normalized to kWh")
        
        input("\nPress Enter for procurement story...")
    
    async def _show_procurement_story(self):
        """Step 5: Procurement decision story"""
        print("\n💼 STEP 5: Procurement Decision Story")
        print("-" * 45)
        
        # Get top 3 vendors
        latest_month = self.db.query(Rankings.month).order_by(Rankings.month.desc()).first()[0]
        top_vendors = self.db.query(Rankings).filter(
            Rankings.month == latest_month
        ).order_by(Rankings.overall_rank).limit(3).all()
        
        print("Scenario: DOD procurement team needs to select AI vendor for large-scale deployment")
        print("\nTop 3 candidates based on carbon efficiency:")
        
        for i, vendor in enumerate(top_vendors, 1):
            print(f"\n{i}. {vendor.company}")
            print(f"   Green Score: {vendor.green_score:.1f}/100")
            print(f"   Total Emissions: {vendor.tco2e:.3f} tCO₂e")
            print(f"   Carbon Intensity: {vendor.g_per_1k_tokens:.1f} gCO₂/1k tokens" if vendor.g_per_1k_tokens else "   Carbon Intensity: N/A")
            print(f"   Data Quality: {vendor.data_quality:.1f}%")
        
        # Make recommendation
        best_vendor = top_vendors[0]
        print(f"\nRecommendation: {best_vendor.company}")
        print(f"   • Highest Green Score: {best_vendor.green_score:.1f}/100")
        print(f"   • Lowest carbon intensity per token")
        print(f"   • High data quality: {best_vendor.data_quality:.1f}%")
        
        # Only show savings comparison if there are multiple vendors
        if len(top_vendors) > 1:
            second_best = top_vendors[1]
            savings = ((second_best.tco2e - best_vendor.tco2e) * 12)
            print(f"   • Estimated annual savings vs 2nd place: {savings:.2f} tCO₂e")
        else:
            print(f"   • Only one vendor in dataset - no comparison available")
        
        print(f"\n💡 Key Insights:")
        print(f"   • Agent successfully normalized {len(self.db.query(RawIngest).all())} messy records")
        print(f"   • Autonomous retry logic handled data quality issues")
        print(f"   • Green Score provides objective comparison metric")
        print(f"   • Data quality badges ensure transparency")
        
        print(f"\n🌐 Next Steps:")
        print(f"   • View detailed dashboard at http://localhost:8000")
        print(f"   • Drill down into company-specific metrics")
        print(f"   • Review agent processing decisions")
        print(f"   • Export rankings for procurement documentation")

async def main():
    """Main demo function"""
    demo = CarbonRankerDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
