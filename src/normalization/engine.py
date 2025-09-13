"""
Data normalization engine for handling messy vendor data
Implements unit conversion, imputation, and validation rules
"""

import re
import json
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class NormalizationResult:
    """Result of normalization process"""
    success: bool
    data: Dict[str, Any]
    quality_score: float
    imputation_log: Dict[str, Any]
    errors: list

class DataNormalizer:
    """Main normalization engine"""
    
    def __init__(self):
        self.default_pue = 1.3
        self.default_gpu_power = 0.4  # kW per GPU
        self.imputation_penalty = 10  # Quality score penalty per imputation
        
    def normalize_gpu_hours(self, raw_value: str) -> Tuple[float, Dict[str, Any]]:
        """Normalize GPU hours from various formats"""
        imputation_log = {}
        
        if not raw_value or raw_value.strip() == "":
            return 0.0, {"error": "Missing GPU hours"}
        
        # Remove common suffixes and clean
        cleaned = re.sub(r'\s*(hrs?|hours?)\s*', '', str(raw_value).strip(), flags=re.IGNORECASE)
        
        try:
            # Extract numeric value
            numeric_match = re.search(r'[\d.]+', cleaned)
            if numeric_match:
                return float(numeric_match.group()), imputation_log
            else:
                return 0.0, {"error": "No numeric value found in GPU hours"}
        except ValueError:
            return 0.0, {"error": "Invalid GPU hours format"}
    
    def normalize_energy(self, raw_value: str) -> Tuple[float, Dict[str, Any]]:
        """Normalize energy consumption from various units"""
        imputation_log = {}
        
        if not raw_value or raw_value.strip() == "":
            return 0.0, {"imputed": "Energy consumption missing"}
        
        # Extract numeric value and unit
        cleaned = str(raw_value).strip()
        
        # Check for MWh (multiply by 1000 to get kWh)
        if 'mwh' in cleaned.lower():
            numeric_match = re.search(r'[\d.]+', cleaned)
            if numeric_match:
                return float(numeric_match.group()) * 1000, imputation_log
        
        # Check for kWh
        elif 'kwh' in cleaned.lower():
            numeric_match = re.search(r'[\d.]+', cleaned)
            if numeric_match:
                return float(numeric_match.group()), imputation_log
        
        # Try to extract just numeric value (assume kWh)
        else:
            numeric_match = re.search(r'[\d.]+', cleaned)
            if numeric_match:
                return float(numeric_match.group()), imputation_log
        
        return 0.0, {"error": "Invalid energy format"}
    
    def normalize_tokens(self, raw_value: str) -> Tuple[float, Dict[str, Any]]:
        """Normalize token counts from various formats (k, M, B)"""
        imputation_log = {}
        
        if not raw_value or raw_value.strip() == "":
            return 0.0, {"imputed": "Token count missing"}
        
        cleaned = str(raw_value).strip().lower()
        
        # Remove common suffixes
        cleaned = re.sub(r'\s*(tokens?|tok)\s*', '', cleaned)
        
        # Extract numeric value and multiplier
        numeric_match = re.search(r'([\d.]+)\s*([kmb]?)', cleaned)
        if not numeric_match:
            return 0.0, {"error": "Invalid token format"}
        
        value = float(numeric_match.group(1))
        multiplier = numeric_match.group(2)
        
        # Apply multiplier
        if multiplier == 'k':
            return value * 1000, imputation_log
        elif multiplier == 'm':
            return value * 1_000_000, imputation_log
        elif multiplier == 'b':
            return value * 1_000_000_000, imputation_log
        else:
            return value, imputation_log
    
    def normalize_api_calls(self, raw_value: str) -> Tuple[int, Dict[str, Any]]:
        """Normalize API call counts"""
        imputation_log = {}
        
        if not raw_value or raw_value.strip() == "":
            return 0, {"imputed": "API calls missing"}
        
        # Remove common suffixes
        cleaned = re.sub(r'\s*(calls?|requests?)\s*', '', str(raw_value).strip(), flags=re.IGNORECASE)
        
        try:
            numeric_match = re.search(r'[\d,]+', cleaned)
            if numeric_match:
                # Remove commas and convert to int
                return int(numeric_match.group().replace(',', '')), imputation_log
            else:
                return 0, {"error": "Invalid API calls format"}
        except ValueError:
            return 0, {"error": "Invalid API calls format"}
    
    def normalize_pue(self, raw_value: str) -> Tuple[float, Dict[str, Any]]:
        """Normalize PUE (Power Usage Effectiveness)"""
        imputation_log = {}
        
        if not raw_value or raw_value.strip() == "":
            return self.default_pue, {"imputed": f"PUE missing, using default {self.default_pue}"}
        
        try:
            # Extract numeric value
            numeric_match = re.search(r'[\d.]+', str(raw_value).strip())
            if numeric_match:
                pue = float(numeric_match.group())
                if pue < 1.0 or pue > 3.0:
                    return self.default_pue, {"imputed": f"PUE {pue} out of range, using default {self.default_pue}"}
                return pue, imputation_log
            else:
                return self.default_pue, {"imputed": f"PUE format invalid, using default {self.default_pue}"}
        except ValueError:
            return self.default_pue, {"imputed": f"PUE invalid, using default {self.default_pue}"}
    
    def normalize_utilization(self, raw_value: str) -> Tuple[float, Dict[str, Any]]:
        """Normalize utilization percentage"""
        imputation_log = {}
        
        if not raw_value or raw_value.strip() == "":
            return 0.0, {"imputed": "Utilization missing"}
        
        # Remove percentage sign and clean
        cleaned = re.sub(r'%', '', str(raw_value).strip())
        
        try:
            numeric_match = re.search(r'[\d.]+', cleaned)
            if numeric_match:
                util = float(numeric_match.group())
                if util > 100:
                    return 100.0, {"imputed": f"Utilization {util}% capped at 100%"}
                return util, imputation_log
            else:
                return 0.0, {"error": "Invalid utilization format"}
        except ValueError:
            return 0.0, {"error": "Invalid utilization format"}
    
    def impute_missing_energy(self, gpu_hours: float, utilization: float) -> float:
        """Impute missing energy consumption using GPU power assumptions"""
        if gpu_hours <= 0 or utilization <= 0:
            return 0.0
        
        # Energy = GPU hours × GPU power (kW) × utilization
        it_kwh = gpu_hours * self.default_gpu_power * (utilization / 100.0)
        return it_kwh
    
    def calculate_total_energy(self, it_kwh: float, pue: float) -> float:
        """Calculate total energy including PUE"""
        return it_kwh * pue
    
    def calculate_emissions(self, total_kwh: float, intensity_g_per_kwh: float) -> float:
        """Calculate CO2 emissions in tonnes"""
        # tCO2e = (kWh × gCO2/kWh) / 1,000,000
        return (total_kwh * intensity_g_per_kwh) / 1_000_000
    
    def calculate_data_quality(self, imputation_log: Dict[str, Any]) -> float:
        """Calculate data quality score (0-100)"""
        base_score = 100.0
        
        # Penalize each imputation
        imputation_count = sum(1 for log in imputation_log.values() 
                              if isinstance(log, dict) and log.get("imputed"))
        base_score -= imputation_count * self.imputation_penalty
        
        # Additional penalties for errors
        error_count = sum(1 for log in imputation_log.values() 
                         if isinstance(log, dict) and log.get("error"))
        base_score -= error_count * (self.imputation_penalty * 2)
        
        return max(0.0, base_score)
    
    def normalize_record(self, raw_record: Dict[str, Any], grid_intensity: float) -> NormalizationResult:
        """Normalize a complete vendor record"""
        result = NormalizationResult(
            success=True,
            data={},
            quality_score=100.0,
            imputation_log={},
            errors=[]
        )
        
        try:
            # Normalize each field
            gpu_hours, gpu_log = self.normalize_gpu_hours(raw_record.get("gpu_hours_raw", ""))
            result.imputation_log["gpu_hours"] = gpu_log
            
            energy_raw, energy_log = self.normalize_energy(raw_record.get("energy_raw", ""))
            result.imputation_log["energy"] = energy_log
            
            tokens, tokens_log = self.normalize_tokens(raw_record.get("tokens_raw", ""))
            result.imputation_log["tokens"] = tokens_log
            
            api_calls, api_log = self.normalize_api_calls(raw_record.get("api_calls_raw", ""))
            result.imputation_log["api_calls"] = api_log
            
            pue, pue_log = self.normalize_pue(raw_record.get("pue_raw", ""))
            result.imputation_log["pue"] = pue_log
            
            utilization, util_log = self.normalize_utilization(raw_record.get("utilization_raw", ""))
            result.imputation_log["utilization"] = util_log
            
            # Impute missing energy if needed
            it_kwh = energy_raw
            if it_kwh <= 0:
                it_kwh = self.impute_missing_energy(gpu_hours, utilization)
                result.imputation_log["energy_imputation"] = {
                    "imputed": f"Energy imputed from GPU hours: {it_kwh:.2f} kWh"
                }
            
            # Calculate total energy and emissions
            total_kwh = self.calculate_total_energy(it_kwh, pue)
            tco2e = self.calculate_emissions(total_kwh, grid_intensity)
            
            # Build normalized data
            result.data = {
                "company": raw_record["company"],
                "month": raw_record["month"],
                "region": raw_record["region"],
                "gpu_hours": gpu_hours,
                "utilization": utilization,
                "it_kwh": it_kwh,
                "total_kwh": total_kwh,
                "intensity_g_per_kwh": grid_intensity,
                "tco2e": tco2e,
                "tokens": tokens,
                "api_calls": api_calls,
                "pue_used": pue,
                "data_quality": self.calculate_data_quality(result.imputation_log)
            }
            
            # Check for critical errors
            if gpu_hours <= 0:
                result.errors.append("Invalid or missing GPU hours")
                result.success = False
            
            if total_kwh <= 0:
                result.errors.append("Invalid energy consumption")
                result.success = False
            
            if utilization > 100:
                result.errors.append("Utilization exceeds 100%")
                result.success = False
            
            result.quality_score = result.data["data_quality"]
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Normalization error: {str(e)}")
            result.quality_score = 0.0
        
        return result
