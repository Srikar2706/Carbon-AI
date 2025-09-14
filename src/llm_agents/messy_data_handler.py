"""
Messy Data Handler
Handles real-world messy data from various cloud providers
"""

import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MessyDataHandler:
    """
    Handles messy, real-world environmental/ops data scenarios
    """
    
    def __init__(self):
        self.messy_scenarios = {
            'aws_logs': self._generate_aws_messy_data,
            'azure_logs': self._generate_azure_messy_data,
            'gcp_logs': self._generate_gcp_messy_data,
            'mixed_providers': self._generate_mixed_messy_data,
            'incomplete_data': self._generate_incomplete_data,
            'conflicting_sources': self._generate_conflicting_data
        }
    
    def generate_messy_data(self, scenario: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate messy data for a specific scenario
        """
        if scenario not in self.messy_scenarios:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        return self.messy_scenarios[scenario](count)
    
    def _generate_aws_messy_data(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate messy AWS CloudWatch/operational data
        """
        messy_data = []
        companies = ['amazon', 'AMAZON', 'Amazon Web Services', 'AWS', 'amzn']
        regions = ['us-east-1', 'US East', 'east-us', 'us_east_1', 'us-east-1a']
        
        for i in range(count):
            record = {
                'company': random.choice(companies),
                'timestamp': self._generate_messy_timestamp(),
                'region': random.choice(regions),
                'gpu_hours_raw': f"{random.randint(100, 5000)} GPU hours",
                'energy_consumption': f"{random.randint(500, 20000)} KWH",
                'utilization_percent': f"{random.randint(20, 95)}%",
                'pue_factor': f"PUE: {random.uniform(1.1, 2.5):.2f}",
                'instance_type': random.choice(['p3.2xlarge', 'p3.8xlarge', 'p3.16xlarge']),
                'tokens_processed': f"{random.randint(1000000, 50000000)} tokens",
                'api_calls': f"{random.randint(1000, 100000)} API calls",
                'data_quality_issues': random.choice([
                    'missing_energy_data',
                    'inconsistent_units',
                    'duplicate_entries',
                    'outdated_metrics'
                ])
            }
            messy_data.append(record)
        
        return messy_data
    
    def _generate_azure_messy_data(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate messy Azure operational data
        """
        messy_data = []
        companies = ['microsoft', 'MICROSOFT', 'Microsoft Azure', 'Azure', 'msft']
        regions = ['eastus', 'East US', 'east-us', 'eastus2', 'East US 2']
        
        for i in range(count):
            record = {
                'vendor': random.choice(companies),
                'date': self._generate_messy_date(),
                'location': random.choice(regions),
                'compute_hours': f"{random.randint(200, 8000)} compute hours",
                'power_usage': f"{random.randint(1000, 25000)} kilowatt-hours",
                'efficiency': f"{random.randint(30, 90)}% efficiency",
                'power_usage_effectiveness': f"{random.uniform(1.0, 3.0):.1f}",
                'vm_size': random.choice(['NC6', 'NC12', 'NC24']),
                'tokens_generated': f"{random.randint(500000, 25000000)} tokens",
                'api_requests': f"{random.randint(500, 50000)} requests",
                'data_issues': random.choice([
                    'incomplete_metrics',
                    'unit_inconsistencies',
                    'region_mapping_errors',
                    'timestamp_format_issues'
                ])
            }
            messy_data.append(record)
        
        return messy_data
    
    def _generate_gcp_messy_data(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate messy Google Cloud operational data
        """
        messy_data = []
        companies = ['google', 'GOOGLE', 'Google Cloud', 'GCP', 'goog']
        regions = ['us-central1', 'US Central', 'central-us', 'us-central1-a', 'us-central1-b']
        
        for i in range(count):
            record = {
                'provider': random.choice(companies),
                'time': self._generate_messy_time(),
                'zone': random.choice(regions),
                'gpu_utilization': f"{random.randint(150, 6000)} GPU hours used",
                'energy_consumed': f"{random.randint(800, 18000)} kWh",
                'utilization_rate': f"{random.randint(25, 88)}%",
                'pue': f"{random.uniform(1.05, 2.8):.2f}",
                'machine_type': random.choice(['n1-standard-4', 'n1-standard-8', 'n1-standard-16']),
                'tokens_processed': f"{random.randint(750000, 30000000)} tokens",
                'api_calls_made': f"{random.randint(800, 75000)} calls",
                'quality_flags': random.choice([
                    'data_validation_failed',
                    'missing_energy_metrics',
                    'region_standardization_needed',
                    'unit_conversion_required'
                ])
            }
            messy_data.append(record)
        
        return messy_data
    
    def _generate_mixed_messy_data(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate mixed provider data with various formats
        """
        messy_data = []
        
        # Mix different provider formats
        aws_data = self._generate_aws_messy_data(count // 3)
        azure_data = self._generate_azure_messy_data(count // 3)
        gcp_data = self._generate_gcp_messy_data(count - (count // 3) * 2)
        
        messy_data.extend(aws_data)
        messy_data.extend(azure_data)
        messy_data.extend(gcp_data)
        
        # Shuffle to simulate mixed data
        random.shuffle(messy_data)
        
        return messy_data
    
    def _generate_incomplete_data(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate data with missing fields and incomplete information
        """
        messy_data = []
        
        for i in range(count):
            # Randomly omit fields to simulate incomplete data
            record = {}
            
            if random.random() > 0.1:  # 90% chance
                record['company'] = random.choice(['Amazon', 'Microsoft', 'Google'])
            
            if random.random() > 0.2:  # 80% chance
                record['month'] = self._generate_messy_date()
            
            if random.random() > 0.15:  # 85% chance
                record['region'] = random.choice(['us-east-1', 'eastus', 'us-central1'])
            
            if random.random() > 0.25:  # 75% chance
                record['gpu_hours'] = f"{random.randint(100, 5000)}"
            
            if random.random() > 0.3:  # 70% chance
                record['energy'] = f"{random.randint(500, 20000)}"
            
            if random.random() > 0.4:  # 60% chance
                record['utilization'] = f"{random.randint(20, 95)}%"
            
            if random.random() > 0.5:  # 50% chance
                record['pue'] = f"{random.uniform(1.1, 2.5):.2f}"
            
            record['data_completeness'] = f"{len(record)}/7 fields present"
            messy_data.append(record)
        
        return messy_data
    
    def _generate_conflicting_data(self, count: int) -> List[Dict[str, Any]]:
        """
        Generate data with conflicting information from different sources
        """
        messy_data = []
        
        for i in range(count):
            # Create conflicting records for the same company/timeframe
            base_record = {
                'company': 'Amazon',
                'month': '2024-01',
                'region': 'us-east-1'
            }
            
            # Add conflicting data
            if i % 2 == 0:
                base_record.update({
                    'gpu_hours': '1500',
                    'energy_kwh': '12000',
                    'utilization': '85%',
                    'pue': '1.2',
                    'source': 'cloudwatch_logs'
                })
            else:
                base_record.update({
                    'gpu_hours': '1800',  # Different value
                    'energy_kwh': '15000',  # Different value
                    'utilization': '78%',  # Different value
                    'pue': '1.4',  # Different value
                    'source': 'billing_api'
                })
            
            base_record['conflict_type'] = 'duplicate_different_values'
            messy_data.append(base_record)
        
        return messy_data
    
    def _generate_messy_timestamp(self) -> str:
        """
        Generate various timestamp formats
        """
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%Y-%m-%dT%H:%M:%SZ',
            '%B %d, %Y'
        ]
        
        base_date = datetime.now() - timedelta(days=random.randint(1, 365))
        format_choice = random.choice(formats)
        
        return base_date.strftime(format_choice)
    
    def _generate_messy_date(self) -> str:
        """
        Generate various date formats
        """
        formats = [
            '%Y-%m',
            '%m/%Y',
            '%Y-%m-%d',
            '%B %Y',
            '%Y'
        ]
        
        base_date = datetime.now() - timedelta(days=random.randint(1, 365))
        format_choice = random.choice(formats)
        
        return base_date.strftime(format_choice)
    
    def _generate_messy_time(self) -> str:
        """
        Generate various time formats
        """
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d',
            '%m/%d/%Y %H:%M'
        ]
        
        base_date = datetime.now() - timedelta(days=random.randint(1, 365))
        format_choice = random.choice(formats)
        
        return base_date.strftime(format_choice)
    
    def get_available_scenarios(self) -> List[str]:
        """
        Get list of available messy data scenarios
        """
        return list(self.messy_scenarios.keys())
    
    def create_realistic_messy_scenario(self) -> Dict[str, Any]:
        """
        Create a realistic messy data scenario for demo
        """
        scenario = {
            'name': 'Real-world Cloud Provider Data Chaos',
            'description': 'Simulates the messy reality of operational data from multiple cloud providers',
            'challenges': [
                'Inconsistent company naming conventions',
                'Mixed date/time formats',
                'Different energy unit representations',
                'Regional naming variations',
                'Missing or incomplete data fields',
                'Conflicting values from different sources',
                'Text mixed with numerical data',
                'Outdated or deprecated field names'
            ],
            'data_sources': [
                'AWS CloudWatch logs',
                'Azure Monitor metrics',
                'Google Cloud Operations logs',
                'Billing API responses',
                'Manual data entry',
                'Legacy system exports'
            ],
            'sample_data': self.generate_messy_data('mixed_providers', 5)
        }
        
        return scenario
