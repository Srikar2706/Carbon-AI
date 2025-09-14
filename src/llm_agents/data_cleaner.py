"""
LLM-Powered Data Cleaner
Uses Claude to clean and normalize messy environmental/ops data
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
import anthropic
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LLMDataCleaner:
    """
    Advanced data cleaner using Claude LLM to handle messy real-world data
    """
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.cleaning_stats = {
            'total_records': 0,
            'cleaned_records': 0,
            'errors': 0,
            'confidence_scores': []
        }
    
    def clean_messy_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean messy environmental/ops data using LLM
        """
        logger.info(f"Starting LLM data cleaning for {len(raw_data)} records")
        
        cleaned_data = []
        batch_size = 5  # Process in small batches for better LLM performance
        
        for i in range(0, len(raw_data), batch_size):
            batch = raw_data[i:i + batch_size]
            cleaned_batch = self._clean_batch(batch)
            cleaned_data.extend(cleaned_batch)
            
        self.cleaning_stats['total_records'] = len(raw_data)
        self.cleaning_stats['cleaned_records'] = len(cleaned_data)
        
        logger.info(f"LLM cleaning complete: {len(cleaned_data)}/{len(raw_data)} records cleaned")
        return cleaned_data
    
    def _clean_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean a batch of records using Claude
        """
        try:
            # Create prompt for Claude
            prompt = self._create_cleaning_prompt(batch)
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=self._get_cleaning_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse Claude's response
            cleaned_data = self._parse_cleaning_response(response.content[0].text)
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error cleaning batch: {e}")
            self.cleaning_stats['errors'] += 1
            # Return original data with error flag
            return [self._add_error_flag(record, str(e)) for record in batch]
    
    def _create_cleaning_prompt(self, batch: List[Dict[str, Any]]) -> str:
        """
        Create a detailed prompt for Claude to clean the data
        """
        prompt = f"""
Please clean and normalize the following messy environmental/ops data records. 
Each record contains operational data from cloud providers (AWS, Azure, GCP) that needs to be standardized.

MESSY DATA TO CLEAN:
{json.dumps(batch, indent=2)}

CLEANING REQUIREMENTS:
1. Standardize company names (e.g., "amazon", "AMAZON", "Amazon Web Services" → "Amazon")
2. Normalize energy units (kWh, KWH, kilowatt-hours → kWh)
3. Clean GPU hours (remove text, keep numbers, standardize units)
4. Fix date formats (various formats → YYYY-MM)
5. Standardize region names (us-east-1, US East, east-us → us-east-1)
6. Clean utilization percentages (remove %, convert to 0-100 scale)
7. Normalize PUE values (remove text, keep decimal numbers)
8. Clean token counts (handle formats like "2.8B tokens", "2800000000", "2.8B" → convert to numbers)
9. Clean API call counts (remove text, keep numbers)
10. Handle missing/invalid data intelligently
11. Add confidence scores (0-100) for each cleaning decision

Return ONLY a valid JSON array with cleaned records. Each record should have:
- company: string (standardized)
- month: string (YYYY-MM format)
- region: string (standardized)
- gpu_hours: number
- energy_kwh: number
- utilization: number (0-100)
- pue: number
- tokens: number (total tokens processed, convert B/M/K suffixes to actual numbers)
- api_calls: number (total API calls made)
- confidence_score: number (0-100)
- cleaning_notes: string (what was cleaned/changed)

Example output format:
[
  {{
    "company": "Amazon",
    "month": "2024-01",
    "region": "us-east-1",
    "gpu_hours": 1250.5,
    "energy_kwh": 8750.25,
    "utilization": 85.5,
    "pue": 1.2,
    "tokens": 2800000000,
    "api_calls": 45000,
    "confidence_score": 95,
    "cleaning_notes": "Standardized company name, converted energy units, cleaned utilization, converted 2.8B tokens to 2800000000"
  }}
]
"""
        return prompt
    
    def _get_cleaning_system_prompt(self) -> str:
        """
        System prompt for Claude data cleaning
        """
        return """
You are an expert data cleaning agent specializing in environmental and operational data from cloud providers.

Your expertise includes:
- Cloud provider data formats (AWS, Azure, GCP)
- Energy consumption metrics and units
- GPU utilization and compute metrics
- Data center efficiency metrics (PUE)
- Regional naming conventions
- Date/time standardization

You excel at:
- Handling inconsistent data formats
- Resolving conflicting information
- Making intelligent assumptions for missing data
- Providing confidence scores for cleaning decisions
- Maintaining data integrity while improving quality

Always return valid JSON and explain your cleaning decisions in the cleaning_notes field.
"""
    
    def _parse_cleaning_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse Claude's cleaning response
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                cleaned_data = json.loads(json_str)
                
                # Validate and add metadata
                for record in cleaned_data:
                    record['cleaned_at'] = datetime.now().isoformat()
                    record['cleaning_method'] = 'claude_llm'
                    
                    # Track confidence scores
                    if 'confidence_score' in record:
                        self.cleaning_stats['confidence_scores'].append(record['confidence_score'])
                
                return cleaned_data
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logger.error(f"Error parsing cleaning response: {e}")
            raise
    
    def _add_error_flag(self, record: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """
        Add error flag to record when cleaning fails
        """
        record['cleaning_error'] = error_msg
        record['cleaned_at'] = datetime.now().isoformat()
        record['cleaning_method'] = 'error_fallback'
        record['confidence_score'] = 0
        return record
    
    def get_cleaning_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cleaning process
        """
        avg_confidence = 0
        if self.cleaning_stats['confidence_scores']:
            avg_confidence = sum(self.cleaning_stats['confidence_scores']) / len(self.cleaning_stats['confidence_scores'])
        
        # Calculate success rate more meaningfully
        # If we have more cleaned records than input records, it means we extracted multiple records from single inputs
        # In this case, success rate should be 100% if we got any records, or based on errors
        if self.cleaning_stats['cleaned_records'] >= self.cleaning_stats['total_records']:
            # Multiple records extracted from single inputs - success rate based on errors
            success_rate = 1.0 - (self.cleaning_stats['errors'] / max(1, self.cleaning_stats['total_records']))
        else:
            # Normal case - ratio of cleaned to input records
            success_rate = self.cleaning_stats['cleaned_records'] / max(1, self.cleaning_stats['total_records'])
        
        return {
            'total_records': self.cleaning_stats['total_records'],
            'cleaned_records': self.cleaning_stats['cleaned_records'],
            'error_rate': self.cleaning_stats['errors'] / max(1, self.cleaning_stats['total_records']),
            'average_confidence': round(avg_confidence, 2),
            'success_rate': min(1.0, success_rate)  # Cap at 100%
        }
    
    def clean_single_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean a single record (useful for real-time processing)
        """
        cleaned_batch = self._clean_batch([record])
        return cleaned_batch[0] if cleaned_batch else record
    
    def generate_clean_csv_data(self, cleaned_data: List[Dict[str, Any]]) -> str:
        """
        Convert cleaned data into clean CSV format for carbon analysis
        """
        import csv
        import io
        
        # Create CSV content
        output = io.StringIO()
        
        # Define CSV headers matching the original format
        fieldnames = [
            'company', 'month', 'region', 'gpu_hours', 'energy_kwh', 
            'utilization', 'pue', 'tokens', 'api_calls'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write cleaned data rows
        for record in cleaned_data:
            csv_row = {
                'company': record.get('company', ''),
                'month': record.get('month', ''),
                'region': record.get('region', ''),
                'gpu_hours': record.get('gpu_hours', 0),
                'energy_kwh': record.get('energy_kwh', 0),
                'utilization': record.get('utilization', 0),
                'pue': record.get('pue', 1.0),
                'tokens': record.get('tokens', 0),
                'api_calls': record.get('api_calls', 0)
            }
            writer.writerow(csv_row)
        
        return output.getvalue()
