"""
Executor component of the agentic loop
Executes normalization and computation tasks
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
from ..normalization.engine import DataNormalizer, NormalizationResult

@dataclass
class ExecutionResult:
    """Result of execution phase"""
    success: bool
    normalized_data: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    execution_log: List[Dict[str, Any]]
    errors: List[str]

class DataExecutor:
    """Executor agent that performs normalization and computation"""
    
    def __init__(self):
        self.normalizer = DataNormalizer()
        self.execution_log = []
    
    def execute_normalization(self, raw_record: Dict[str, Any], 
                            grid_intensity: float,
                            strategy: Dict[str, Any]) -> ExecutionResult:
        """Execute normalization based on planned strategy"""
        result = ExecutionResult(
            success=False,
            normalized_data=None,
            metrics=None,
            execution_log=[],
            errors=[]
        )
        
        try:
            # Log execution start
            result.execution_log.append({
                "stage": "normalization_start",
                "action": "begin_normalization",
                "details": f"Processing {raw_record['company']} for {raw_record['month']}"
            })
            
            # Apply priority actions first
            for action in strategy.get("priority_actions", []):
                self._apply_action(raw_record, action, result.execution_log)
            
            # Perform normalization
            normalization_result = self.normalizer.normalize_record(raw_record, grid_intensity)
            
            if normalization_result.success:
                result.normalized_data = normalization_result.data
                result.execution_log.append({
                    "stage": "normalization_complete",
                    "action": "normalization_success",
                    "details": f"Quality score: {normalization_result.quality_score:.1f}"
                })
                
                # Apply fallback actions if needed
                for action in strategy.get("fallback_actions", []):
                    self._apply_action(raw_record, action, result.execution_log)
                
                result.success = True
            else:
                result.errors.extend(normalization_result.errors)
                result.execution_log.append({
                    "stage": "normalization_failed",
                    "action": "normalization_error",
                    "details": f"Errors: {normalization_result.errors}"
                })
        
        except Exception as e:
            result.errors.append(f"Execution error: {str(e)}")
            result.execution_log.append({
                "stage": "execution_error",
                "action": "exception",
                "details": str(e)
            })
        
        return result
    
    def compute_metrics(self, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute carbon efficiency metrics"""
        metrics = {}
        
        try:
            # Basic metrics
            metrics["total_kwh"] = normalized_data["total_kwh"]
            metrics["tco2e"] = normalized_data["tco2e"]
            metrics["utilization_avg"] = normalized_data["utilization"]
            metrics["pue_used"] = normalized_data["pue_used"]
            metrics["data_quality"] = normalized_data["data_quality"]
            
            # Intensity metrics (per 1k tokens)
            if normalized_data["tokens"] and normalized_data["tokens"] > 0:
                metrics["g_per_1k_tokens"] = (normalized_data["tco2e"] * 1_000_000) / (normalized_data["tokens"] / 1000)
            else:
                metrics["g_per_1k_tokens"] = None
            
            # Intensity metrics (per API call)
            if normalized_data["api_calls"] and normalized_data["api_calls"] > 0:
                metrics["g_per_call"] = (normalized_data["tco2e"] * 1_000_000) / normalized_data["api_calls"]
            else:
                metrics["g_per_call"] = None
            
            # Efficiency metrics (tokens per tCO2e)
            if normalized_data["tokens"] and normalized_data["tco2e"] > 0:
                metrics["tokens_per_tco2e"] = normalized_data["tokens"] / normalized_data["tco2e"]
            else:
                metrics["tokens_per_tco2e"] = None
            
            # Additional metrics
            metrics["total_tokens"] = normalized_data["tokens"]
            metrics["total_api_calls"] = normalized_data["api_calls"]
            metrics["intensity_g_per_kwh"] = normalized_data["intensity_g_per_kwh"]
            
        except Exception as e:
            metrics["error"] = f"Metrics computation error: {str(e)}"
        
        return metrics
    
    def _apply_action(self, raw_record: Dict[str, Any], action: Dict[str, Any], log: List[Dict[str, Any]]):
        """Apply a specific action to the raw record"""
        action_type = action["action"]
        field = action["field"]
        reason = action["reason"]
        
        log_entry = {
            "stage": "action_application",
            "action": action_type,
            "field": field,
            "reason": reason,
            "details": f"Applied {action_type} to {field}"
        }
        
        if action_type == "impute_from_gpu_hours":
            # This will be handled by the normalizer
            log_entry["details"] = "Energy will be imputed from GPU hours during normalization"
        
        elif action_type == "use_default_pue":
            log_entry["details"] = "PUE will use default value during normalization"
        
        elif action_type == "mark_na":
            log_entry["details"] = "Field will be marked as N/A in metrics"
        
        elif action_type == "use_market_average":
            log_entry["details"] = "Region will use market average grid intensity"
        
        elif action_type == "validate_and_fix":
            log_entry["details"] = "Field will be validated and corrected during normalization"
        
        elif action_type == "normalize_units":
            log_entry["details"] = "Units will be normalized during parsing"
        
        elif action_type == "parse_tokens":
            log_entry["details"] = "Token format will be parsed during normalization"
        
        log.append(log_entry)
    
    def validate_results(self, normalized_data: Dict[str, Any], 
                        validation_rules: List[str]) -> List[str]:
        """Validate normalized data against rules"""
        validation_errors = []
        
        for rule in validation_rules:
            if rule == "utilization_must_be_0_to_100":
                util = normalized_data.get("utilization", 0)
                if not (0 <= util <= 100):
                    validation_errors.append(f"Utilization {util}% not in range 0-100")
            
            elif rule == "energy_must_be_positive":
                energy = normalized_data.get("total_kwh", 0)
                if energy <= 0:
                    validation_errors.append(f"Energy {energy} kWh must be positive")
            
            elif rule == "pue_must_be_1_to_3":
                pue = normalized_data.get("pue_used", 1.3)
                if not (1.0 <= pue <= 3.0):
                    validation_errors.append(f"PUE {pue} not in range 1.0-3.0")
            
            elif rule == "gpu_hours_must_be_positive":
                gpu_hours = normalized_data.get("gpu_hours", 0)
                if gpu_hours <= 0:
                    validation_errors.append(f"GPU hours {gpu_hours} must be positive")
        
        return validation_errors
