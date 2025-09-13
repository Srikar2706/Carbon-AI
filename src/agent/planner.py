"""
Planner component of the agentic loop
Detects issues in raw data and plans normalization strategy
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import re

@dataclass
class DetectionResult:
    """Result of data quality detection"""
    issues: List[Dict[str, Any]]
    severity: str  # low, medium, high, critical
    recommended_actions: List[str]
    confidence: float

class DataPlanner:
    """Planner agent that detects data quality issues and plans fixes"""
    
    def __init__(self):
        self.issue_patterns = {
            "missing_energy": {
                "pattern": r"^\s*$",
                "field": "energy_raw",
                "severity": "high",
                "action": "impute_from_gpu_hours"
            },
            "missing_pue": {
                "pattern": r"^\s*$",
                "field": "pue_raw", 
                "severity": "medium",
                "action": "use_default_pue"
            },
            "missing_tokens": {
                "pattern": r"^\s*$",
                "field": "tokens_raw",
                "severity": "medium", 
                "action": "mark_na"
            },
            "unknown_region": {
                "pattern": r"UNKNOWN",
                "field": "region",
                "severity": "medium",
                "action": "use_market_average"
            },
            "invalid_utilization": {
                "pattern": r"^$|^[^0-9]*$|^[0-9]+$",
                "field": "utilization_raw",
                "severity": "high",
                "action": "validate_and_fix"
            },
            "mixed_units": {
                "pattern": r"(MWh|kWh)",
                "field": "energy_raw",
                "severity": "low",
                "action": "normalize_units"
            },
            "fuzzy_tokens": {
                "pattern": r"[0-9.]+[kKmMbB]",
                "field": "tokens_raw", 
                "severity": "low",
                "action": "parse_tokens"
            }
        }
    
    def detect_issues(self, raw_record: Dict[str, Any]) -> DetectionResult:
        """Detect data quality issues in a raw record"""
        issues = []
        recommended_actions = []
        max_severity = "low"
        
        for issue_type, config in self.issue_patterns.items():
            field_value = raw_record.get(config["field"], "")
            
            if config["field"] == "region" and field_value == "UNKNOWN":
                issues.append({
                    "type": issue_type,
                    "field": config["field"],
                    "value": field_value,
                    "severity": config["severity"],
                    "description": f"Unknown region: {field_value}"
                })
                recommended_actions.append(config["action"])
                max_severity = self._update_severity(max_severity, config["severity"])
            
            elif config["field"] in ["energy_raw", "pue_raw", "tokens_raw"]:
                if not field_value or field_value.strip() == "":
                    issues.append({
                        "type": issue_type,
                        "field": config["field"],
                        "value": field_value,
                        "severity": config["severity"],
                        "description": f"Missing {config['field']}"
                    })
                    recommended_actions.append(config["action"])
                    max_severity = self._update_severity(max_severity, config["severity"])
            
            elif config["field"] == "utilization_raw":
                if not self._is_valid_utilization(field_value):
                    issues.append({
                        "type": issue_type,
                        "field": config["field"],
                        "value": field_value,
                        "severity": config["severity"],
                        "description": f"Invalid utilization format: {field_value}"
                    })
                    recommended_actions.append(config["action"])
                    max_severity = self._update_severity(max_severity, config["severity"])
            
            elif config["field"] == "energy_raw" and field_value:
                # Check for mixed units
                if "MWh" in field_value and "kWh" in field_value:
                    issues.append({
                        "type": issue_type,
                        "field": config["field"],
                        "value": field_value,
                        "severity": config["severity"],
                        "description": "Mixed energy units detected"
                    })
                    recommended_actions.append(config["action"])
                    max_severity = self._update_severity(max_severity, config["severity"])
            
            elif config["field"] == "tokens_raw" and field_value:
                # Check for fuzzy token format
                if re.search(config["pattern"], field_value):
                    issues.append({
                        "type": issue_type,
                        "field": config["field"],
                        "value": field_value,
                        "severity": config["severity"],
                        "description": f"Fuzzy token format: {field_value}"
                    })
                    recommended_actions.append(config["action"])
                    max_severity = self._update_severity(max_severity, config["severity"])
        
        # Calculate confidence based on issue severity and count
        confidence = self._calculate_confidence(issues, max_severity)
        
        return DetectionResult(
            issues=issues,
            severity=max_severity,
            recommended_actions=list(set(recommended_actions)),
            confidence=confidence
        )
    
    def _is_valid_utilization(self, value: str) -> bool:
        """Check if utilization value is valid"""
        if not value or value.strip() == "":
            return False
        
        # Remove percentage sign and check if numeric
        cleaned = re.sub(r'%', '', str(value).strip())
        try:
            util = float(cleaned)
            return 0 <= util <= 100
        except ValueError:
            return False
    
    def _update_severity(self, current: str, new: str) -> str:
        """Update severity level (critical > high > medium > low)"""
        severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return new if severity_levels[new] > severity_levels[current] else current
    
    def _calculate_confidence(self, issues: List[Dict], severity: str) -> float:
        """Calculate confidence in detection results"""
        base_confidence = 0.9
        
        # Reduce confidence for more issues
        issue_penalty = min(len(issues) * 0.1, 0.5)
        
        # Reduce confidence for higher severity (more complex fixes needed)
        severity_penalty = {"low": 0.0, "medium": 0.1, "high": 0.2, "critical": 0.3}[severity]
        
        return max(0.1, base_confidence - issue_penalty - severity_penalty)
    
    def plan_normalization_strategy(self, detection_result: DetectionResult) -> Dict[str, Any]:
        """Plan the normalization strategy based on detected issues"""
        strategy = {
            "priority_actions": [],
            "fallback_actions": [],
            "validation_rules": [],
            "expected_quality": 100.0
        }
        
        # Prioritize actions based on severity
        for issue in detection_result.issues:
            if issue["severity"] in ["critical", "high"]:
                strategy["priority_actions"].append({
                    "action": self._get_action_for_issue(issue["type"]),
                    "field": issue["field"],
                    "reason": issue["description"]
                })
            else:
                strategy["fallback_actions"].append({
                    "action": self._get_action_for_issue(issue["type"]),
                    "field": issue["field"],
                    "reason": issue["description"]
                })
        
        # Add validation rules
        strategy["validation_rules"] = [
            "utilization_must_be_0_to_100",
            "energy_must_be_positive",
            "pue_must_be_1_to_3",
            "gpu_hours_must_be_positive"
        ]
        
        # Estimate expected quality score
        quality_penalty = len(detection_result.issues) * 10
        strategy["expected_quality"] = max(0, 100 - quality_penalty)
        
        return strategy
    
    def _get_action_for_issue(self, issue_type: str) -> str:
        """Get the appropriate action for an issue type"""
        action_map = {
            "missing_energy": "impute_from_gpu_hours",
            "missing_pue": "use_default_pue", 
            "missing_tokens": "mark_na",
            "unknown_region": "use_market_average",
            "invalid_utilization": "validate_and_fix",
            "mixed_units": "normalize_units",
            "fuzzy_tokens": "parse_tokens"
        }
        return action_map.get(issue_type, "manual_review")
