#!/usr/bin/env python3
"""
ROX Competition Demo: LLM-Powered Messy Data Processing
Demonstrates how Claude handles real-world messy environmental/ops data
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

from src.agent.carbon_ranker import CarbonRankerAgent
from src.llm_agents.messy_data_handler import MessyDataHandler

async def main():
    """
    Run the ROX competition demo
    """
    print("DATA TRANSFORMATION DEMO")
    print("=" * 60)
    print("LLM-Powered Messy Data Processing for Carbon Efficiency")
    print("=" * 60)
    
    # Check if API key is available
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        print("Please set your Claude API key in the .env file")
        return
    
    print("Claude API key found")
    print()
    
    # Initialize the carbon ranker agent
    agent = CarbonRankerAgent()
    
    if not agent.llm_cleaner:
        print("LLM data cleaning not available")
        return
    
    print("LLM-powered data cleaning initialized")
    print()
    
    # Run the demo scenarios
    print("Running messy data scenarios...")
    print()
    
    results = await agent.demo_messy_data_scenarios()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    
    # Show key metrics
    total_scenarios = len(results)
    successful_scenarios = sum(1 for r in results.values() if r and r.get('cleaning_stats', {}).get('success_rate', 0) > 0.8)
    
    print(f"Total Scenarios: {total_scenarios}")
    print(f"Successful: {successful_scenarios}")
    print(f"Success Rate: {successful_scenarios/total_scenarios:.1%}")
    
    # Show individual scenario results
    print("\nSCENARIO RESULTS:")
    for scenario, result in results.items():
        if result and result.get('cleaning_stats'):
            stats = result['cleaning_stats']
            print(f"  • {scenario}: {stats['success_rate']:.1%} success, {stats['average_confidence']}% confidence")
        else:
            print(f"  • {scenario}: Failed")
    
    print("\n🚀 READY FOR ROX COMPETITION!")
    print("This system demonstrates:")
    print("  • Real-world messy data handling")
    print("  • LLM-powered data cleaning and normalization")
    print("  • Multi-source data resolution")
    print("  • Intelligent error handling")
    print("  • Robust decision-making under uncertainty")
    print("  • Production-ready architecture")

if __name__ == "__main__":
    asyncio.run(main())
