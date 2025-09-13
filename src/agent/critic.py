"""
Critic component of the agentic loop
Validates results and determines if retry is needed
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

@dataclass
class CritiqueResult:
    """Result of critique phase"""
    passed: bool
    issues: List[Dict[str, Any]]
    retry_needed: bool
    retry_reason: Optional[str]
    quality_score: float
    recommendations: List[str]

class DataCritic:
    """Critic agent that validates results and determines retry needs"""
    
    def __init__(self):
        self.max_retries = 3
        self.quality_threshold = 70.0
        self.critical_issues = [
            "negative_energy",
            "invalid_utilization", 
            "missing_critical_data",
            "calculation_error"
        ]
    
    def critique_results(self, execution_result: Any, 
                        normalized_data: Optional[Dict[str, Any]],
                        retry_count: int) -> CritiqueResult:
        """Critique the execution results and determine if retry is needed"""
        
        result = CritiqueResult(
            passed=False,
            issues=[],
            retry_needed=False,
            retry_reason=None,
            quality_score=0.0,
            recommendations=[]
        )
        
        # Check if execution was successful
        if not execution_result.success:
            result.issues.append({
                "type": "execution_failure",
                "severity": "critical",
                "description": "Execution phase failed",
                "details": execution_result.errors
            })
            result.retry_needed = True
            result.retry_reason = "Execution failure"
            return result
        
        if not normalized_data:
            result.issues.append({
                "type": "missing_normalized_data",
                "severity": "critical", 
                "description": "No normalized data produced",
                "details": "Normalization failed to produce valid data"
            })
            result.retry_needed = True
            result.retry_reason = "Missing normalized data"
            return result
        
        # Validate data quality
        quality_score = normalized_data.get("data_quality", 0.0)
        result.quality_score = quality_score
        
        # Check for critical data issues
        critical_issues = self._check_critical_issues(normalized_data)
        result.issues.extend(critical_issues)
        
        # Check for data quality issues
        quality_issues = self._check_quality_issues(normalized_data)
        result.issues.extend(quality_issues)
        
        # Check for calculation anomalies
        anomaly_issues = self._check_anomalies(normalized_data)
        result.issues.extend(anomaly_issues)
        
        # Determine if retry is needed
        result.retry_needed = self._should_retry(
            result.issues, quality_score, retry_count
        )
        
        if result.retry_needed:
            result.retry_reason = self._get_retry_reason(result.issues, quality_score)
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result.issues)
        
        # Determine if overall validation passed
        result.passed = not result.retry_needed and quality_score >= self.quality_threshold
        
        return result
    
    def _check_critical_issues(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for critical data issues that require retry"""
        issues = []
        
        # Check for negative or zero energy
        if data.get("total_kwh", 0) <= 0:
            issues.append({
                "type": "negative_energy",
                "severity": "critical",
                "description": "Total energy consumption is zero or negative",
                "details": f"total_kwh: {data.get('total_kwh', 0)}"
            })
        
        # Check for invalid utilization
        utilization = data.get("utilization", 0)
        if utilization > 100 or utilization < 0:
            issues.append({
                "type": "invalid_utilization",
                "severity": "critical",
                "description": "Utilization percentage is invalid",
                "details": f"utilization: {utilization}%"
            })
        
        # Check for missing critical data
        if data.get("gpu_hours", 0) <= 0:
            issues.append({
                "type": "missing_critical_data",
                "severity": "critical",
                "description": "GPU hours is missing or invalid",
                "details": f"gpu_hours: {data.get('gpu_hours', 0)}"
            })
        
        # Check for calculation errors
        if data.get("tco2e", 0) < 0:
            issues.append({
                "type": "calculation_error",
                "severity": "critical",
                "description": "CO2 emissions calculation error",
                "details": f"tco2e: {data.get('tco2e', 0)}"
            })
        
        return issues
    
    def _check_quality_issues(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for data quality issues"""
        issues = []
        
        # Check data quality score
        quality = data.get("data_quality", 0)
        if quality < self.quality_threshold:
            issues.append({
                "type": "low_quality",
                "severity": "high",
                "description": f"Data quality score below threshold",
                "details": f"quality: {quality:.1f} < {self.quality_threshold}"
            })
        
        # Check for excessive imputations
        imputation_log = data.get("imputation_log", {})
        if isinstance(imputation_log, str):
            try:
                imputation_log = json.loads(imputation_log)
            except:
                imputation_log = {}
        
        imputation_count = sum(1 for log in imputation_log.values() 
                              if isinstance(log, dict) and log.get("imputed"))
        
        if imputation_count > 3:
            issues.append({
                "type": "excessive_imputations",
                "severity": "medium",
                "description": "Too many imputed values",
                "details": f"imputations: {imputation_count}"
            })
        
        return issues
    
    def _check_anomalies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for data anomalies"""
        issues = []
        
        # Check for unusually high utilization
        utilization = data.get("utilization", 0)
        if utilization > 95:
            issues.append({
                "type": "high_utilization",
                "severity": "low",
                "description": "Unusually high utilization",
                "details": f"utilization: {utilization}%"
            })
        
        # Check for unusually high PUE
        pue = data.get("pue_used", 1.3)
        if pue > 2.0:
            issues.append({
                "type": "high_pue",
                "severity": "medium",
                "description": "Unusually high PUE",
                "details": f"pue: {pue}"
            })
        
        # Check for unusually high energy intensity
        intensity = data.get("intensity_g_per_kwh", 400)
        if intensity > 800:
            issues.append({
                "type": "high_intensity",
                "severity": "low",
                "description": "High grid carbon intensity",
                "details": f"intensity: {intensity} g/kWh"
            })
        
        return issues
    
    def _should_retry(self, issues: List[Dict[str, Any]], 
                     quality_score: float, retry_count: int) -> bool:
        """Determine if retry is needed"""
        
        # Don't retry if we've exceeded max retries
        if retry_count >= self.max_retries:
            return False
        
        # Retry if there are critical issues
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        if critical_issues:
            return True
        
        # Retry if quality is too low
        if quality_score < self.quality_threshold:
            return True
        
        # Retry if there are too many high-severity issues
        high_issues = [i for i in issues if i["severity"] == "high"]
        if len(high_issues) > 2:
            return True
        
        return False
    
    def _get_retry_reason(self, issues: List[Dict[str, Any]], quality_score: float) -> str:
        """Get the reason for retry"""
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        if critical_issues:
            return f"Critical issues: {[i['type'] for i in critical_issues]}"
        
        if quality_score < self.quality_threshold:
            return f"Quality score {quality_score:.1f} below threshold {self.quality_threshold}"
        
        high_issues = [i for i in issues if i["severity"] == "high"]
        if high_issues:
            return f"High severity issues: {[i['type'] for i in high_issues]}"
        
        return "Unknown retry reason"
    
    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on issues found"""
        recommendations = []
        
        for issue in issues:
            if issue["type"] == "negative_energy":
                recommendations.append("Check GPU hours and utilization values")
            elif issue["type"] == "invalid_utilization":
                recommendations.append("Validate utilization percentage format")
            elif issue["type"] == "missing_critical_data":
                recommendations.append("Ensure GPU hours are properly parsed")
            elif issue["type"] == "low_quality":
                recommendations.append("Review imputation strategy")
            elif issue["type"] == "excessive_imputations":
                recommendations.append("Consider manual data review")
            elif issue["type"] == "high_pue":
                recommendations.append("Verify PUE value accuracy")
        
        return recommendations
