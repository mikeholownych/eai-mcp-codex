"""Enhanced Plan Manager with predictive analytics and security integration."""

from datetime import datetime
from typing import Dict, List, Optional, Any

from .plan_manager import PlanManager
from .models import Plan, PlanRequest
from ..analytics.prediction_engine import PerformancePredictionEngine
from ..security.security_analyzer import SecurityAnalyzer
from ..common.logging import get_logger

logger = get_logger("enhanced_plan_manager")


class EnhancedPlanManager(PlanManager):
    """Enhanced plan manager with predictive analytics and security features."""

    def __init__(self, db_path: str = "data/plans.db"):
        super().__init__(db_path)
        self.prediction_engine = PerformancePredictionEngine()
        self.security_analyzer = SecurityAnalyzer()

        # Enhancement flags
        self.enable_predictions = True
        self.enable_security_scanning = True
        self.enable_risk_assessment = True

    async def create_enhanced_plan(self, request: PlanRequest) -> Dict[str, Any]:
        """Create plan with predictive analytics and security assessment."""
        try:
            # Create base plan
            plan = self.create_plan(request)

            enhancements = {
                "plan": plan,
                "predictions": None,
                "security_assessment": None,
                "risk_analysis": None,
                "recommendations": [],
            }

            # Add predictive analytics if enabled
            if self.enable_predictions:
                try:
                    prediction_result = (
                        await self.prediction_engine.predict_workflow_duration(plan)
                    )
                    enhancements["predictions"] = {
                        "estimated_duration_hours": prediction_result.estimated_duration,
                        "confidence_interval": prediction_result.confidence_interval,
                        "confidence_score": prediction_result.confidence_score,
                        "risk_factors": prediction_result.risk_factors,
                        "resource_requirements": prediction_result.resource_requirements,
                        "milestone_predictions": prediction_result.milestone_predictions,
                        "similar_projects": prediction_result.similar_projects,
                    }

                    # Update plan with predicted duration if not set
                    if not plan.estimated_hours:
                        self.update_plan(
                            plan.id,
                            {"estimated_hours": prediction_result.estimated_duration},
                        )
                        plan.estimated_hours = prediction_result.estimated_duration

                    logger.info(
                        f"Generated predictions for plan {plan.id}: {prediction_result.estimated_duration:.1f}h"
                    )

                except Exception as e:
                    logger.error(f"Prediction failed for plan {plan.id}: {e}")
                    enhancements["recommendations"].append(
                        {
                            "type": "prediction_error",
                            "message": "Could not generate duration predictions",
                            "action": "Manual estimation recommended",
                        }
                    )

            # Add security assessment if enabled and code is provided
            if self.enable_security_scanning and hasattr(request, "code_context"):
                try:
                    security_report = (
                        await self.security_analyzer.analyze_code_security(
                            request.code_context, plan
                        )
                    )

                    enhancements["security_assessment"] = {
                        "scan_id": security_report.scan_id,
                        "security_score": security_report.security_score,
                        "vulnerabilities_count": len(security_report.vulnerabilities),
                        "critical_vulnerabilities": len(
                            [
                                v
                                for v in security_report.vulnerabilities
                                if v.severity.value == "critical"
                            ]
                        ),
                        "compliance_status": len(
                            [
                                c
                                for c in security_report.compliance_status
                                if c.status == "pass"
                            ]
                        ),
                        "recommendations": security_report.recommendations[:5],  # Top 5
                    }

                    # Add security considerations to plan recommendations
                    if security_report.security_score < 70:
                        enhancements["recommendations"].append(
                            {
                                "type": "security_concern",
                                "message": f"Security score ({security_report.security_score:.1f}) below threshold",
                                "action": "Address security vulnerabilities before implementation",
                            }
                        )

                    logger.info(
                        f"Security assessment completed for plan {plan.id}: score {security_report.security_score:.1f}"
                    )

                except Exception as e:
                    logger.error(f"Security assessment failed for plan {plan.id}: {e}")
                    enhancements["recommendations"].append(
                        {
                            "type": "security_error",
                            "message": "Could not complete security assessment",
                            "action": "Manual security review recommended",
                        }
                    )

            # Generate comprehensive risk analysis
            if self.enable_risk_assessment:
                risk_analysis = self._generate_risk_analysis(
                    plan,
                    enhancements.get("predictions"),
                    enhancements.get("security_assessment"),
                )
                enhancements["risk_analysis"] = risk_analysis

            # Generate actionable recommendations
            recommendations = self._generate_recommendations(plan, enhancements)
            enhancements["recommendations"].extend(recommendations)

            # Store enhancement metadata
            await self._store_enhancement_metadata(plan.id, enhancements)

            return enhancements

        except Exception as e:
            logger.error(f"Enhanced plan creation failed: {e}")
            # Fallback to basic plan creation
            plan = self.create_plan(request)
            return {
                "plan": plan,
                "predictions": None,
                "security_assessment": None,
                "risk_analysis": None,
                "recommendations": [
                    {
                        "type": "enhancement_error",
                        "message": "Advanced features unavailable",
                        "action": "Plan created with basic features only",
                    }
                ],
            }

    def _generate_risk_analysis(
        self, plan: Plan, predictions: Optional[Dict], security: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate comprehensive risk analysis."""
        risk_factors = []
        overall_risk = "low"

        # Prediction-based risks
        if predictions:
            confidence = predictions.get("confidence_score", 1.0)
            if confidence < 0.7:
                risk_factors.append(
                    {
                        "category": "estimation_uncertainty",
                        "level": "medium",
                        "description": f"Low prediction confidence ({confidence:.2f})",
                        "mitigation": "Add buffer time and monitor progress closely",
                    }
                )
                overall_risk = "medium"

            # Risk factors from prediction engine
            pred_risks = predictions.get("risk_factors", [])
            risk_factors.extend(pred_risks)

            if any(rf.get("level") == "high" for rf in pred_risks):
                overall_risk = "high"

        # Security-based risks
        if security:
            security_score = security.get("security_score", 100)
            critical_vulns = security.get("critical_vulnerabilities", 0)

            if critical_vulns > 0:
                risk_factors.append(
                    {
                        "category": "security_critical",
                        "level": "critical",
                        "description": f"{critical_vulns} critical security vulnerabilities found",
                        "mitigation": "Address critical vulnerabilities before deployment",
                    }
                )
                overall_risk = "critical"
            elif security_score < 70:
                risk_factors.append(
                    {
                        "category": "security_concern",
                        "level": "high",
                        "description": f"Low security score ({security_score:.1f})",
                        "mitigation": "Implement security improvements",
                    }
                )
                if overall_risk != "critical":
                    overall_risk = "high"

        # Plan complexity risks
        task_count = len(plan.tasks) if hasattr(plan, "tasks") else 0
        if task_count > 20:
            risk_factors.append(
                {
                    "category": "complexity",
                    "level": "medium",
                    "description": f"High task count ({task_count})",
                    "mitigation": "Consider breaking into phases",
                }
            )
            if overall_risk == "low":
                overall_risk = "medium"

        # Timeline risks
        if plan.start_date and plan.end_date:
            planned_days = (plan.end_date - plan.start_date).days
            if planned_days < 7 and predictions:
                estimated_hours = predictions.get("estimated_duration_hours", 0)
                if estimated_hours > 40:  # > 1 week of work in < 1 week timeline
                    risk_factors.append(
                        {
                            "category": "timeline_pressure",
                            "level": "high",
                            "description": "Aggressive timeline vs. estimated effort",
                            "mitigation": "Reassess timeline or reduce scope",
                        }
                    )
                    if overall_risk not in ["critical", "high"]:
                        overall_risk = "high"

        return {
            "overall_risk_level": overall_risk,
            "risk_factors": risk_factors,
            "total_risk_factors": len(risk_factors),
            "mitigation_priority": self._calculate_mitigation_priority(overall_risk),
            "review_recommended": overall_risk in ["high", "critical"],
        }

    def _calculate_mitigation_priority(self, risk_level: str) -> str:
        """Calculate mitigation priority based on risk level."""
        priority_map = {
            "low": "monitor",
            "medium": "plan",
            "high": "immediate",
            "critical": "urgent",
        }
        return priority_map.get(risk_level, "monitor")

    def _generate_recommendations(
        self, plan: Plan, enhancements: Dict
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        predictions = enhancements.get("predictions")
        security = enhancements.get("security_assessment")
        risk_analysis = enhancements.get("risk_analysis", {})

        # Prediction-based recommendations
        if predictions:
            confidence = predictions.get("confidence_score", 1.0)
            estimated_hours = predictions.get("estimated_duration_hours", 0)

            if confidence < 0.8:
                recommendations.append(
                    {
                        "type": "estimation",
                        "priority": "medium",
                        "message": "Consider adding buffer time due to prediction uncertainty",
                        "action": f"Add {int(estimated_hours * 0.2)} hours buffer time",
                    }
                )

            # Resource recommendations
            resource_reqs = predictions.get("resource_requirements", {})
            team_size = resource_reqs.get("recommended_team_size", 1)
            if team_size > 1:
                recommendations.append(
                    {
                        "type": "resources",
                        "priority": "high",
                        "message": f"Project requires {team_size} team members",
                        "action": f'Assign {team_size} developers with {resource_reqs.get("skill_level_required", "mid")} skill level',
                    }
                )

        # Security recommendations
        if security:
            if security.get("critical_vulnerabilities", 0) > 0:
                recommendations.append(
                    {
                        "type": "security",
                        "priority": "critical",
                        "message": "Critical security vulnerabilities detected",
                        "action": "Address security issues before proceeding",
                    }
                )
            elif security.get("security_score", 100) < 80:
                recommendations.append(
                    {
                        "type": "security",
                        "priority": "high",
                        "message": "Security improvements needed",
                        "action": "Review and implement security recommendations",
                    }
                )

        # Risk-based recommendations
        overall_risk = risk_analysis.get("overall_risk_level", "low")
        if overall_risk in ["high", "critical"]:
            recommendations.append(
                {
                    "type": "risk_management",
                    "priority": "high",
                    "message": f"Project has {overall_risk} risk level",
                    "action": "Conduct detailed risk review and create mitigation plan",
                }
            )

        # Timeline recommendations
        if plan.start_date and plan.end_date and predictions:
            planned_days = (plan.end_date - plan.start_date).days
            estimated_hours = predictions.get("estimated_duration_hours", 0)
            estimated_days = estimated_hours / 8  # 8 hours per day

            if estimated_days > planned_days * 1.2:
                recommendations.append(
                    {
                        "type": "timeline",
                        "priority": "high",
                        "message": "Estimated effort exceeds planned timeline",
                        "action": f"Consider extending timeline by {int(estimated_days - planned_days)} days",
                    }
                )

        return recommendations

    async def _store_enhancement_metadata(self, plan_id: str, enhancements: Dict):
        """Store enhancement metadata for future analysis."""
        try:
            metadata = {
                "enhanced_at": datetime.utcnow().isoformat(),
                "predictions_enabled": self.enable_predictions,
                "security_enabled": self.enable_security_scanning,
                "risk_assessment_enabled": self.enable_risk_assessment,
                "enhancement_summary": {
                    "predictions_generated": enhancements.get("predictions")
                    is not None,
                    "security_assessed": enhancements.get("security_assessment")
                    is not None,
                    "risk_analyzed": enhancements.get("risk_analysis") is not None,
                    "recommendations_count": len(
                        enhancements.get("recommendations", [])
                    ),
                },
            }

            # Update plan metadata
            current_metadata = self.get_plan(plan_id).metadata or {}
            current_metadata.update({"enhancements": metadata})

            self.update_plan(plan_id, {"metadata": current_metadata})

        except Exception as e:
            logger.error(f"Failed to store enhancement metadata for {plan_id}: {e}")

    async def get_plan_analytics(self, plan_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a plan."""
        plan = self.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found"}

        analytics = {
            "plan_id": plan_id,
            "basic_info": {
                "title": plan.title,
                "status": plan.status.value,
                "priority": plan.priority,
                "created_at": plan.created_at.isoformat(),
                "estimated_hours": plan.estimated_hours,
            },
            "predictions": None,
            "security_status": None,
            "performance_metrics": None,
        }

        # Get latest predictions if available
        if self.enable_predictions:
            try:
                prediction = await self.prediction_engine.predict_workflow_duration(
                    plan
                )
                analytics["predictions"] = {
                    "estimated_duration": prediction.estimated_duration,
                    "confidence": prediction.confidence_score,
                    "risk_factors_count": len(prediction.risk_factors),
                    "milestone_count": len(prediction.milestone_predictions),
                }
            except Exception as e:
                logger.error(f"Failed to get predictions for analytics: {e}")

        # Get prediction engine accuracy metrics
        accuracy_metrics = self.prediction_engine.get_prediction_accuracy()
        analytics["performance_metrics"] = accuracy_metrics

        return analytics

    async def record_plan_completion(self, plan_id: str, actual_hours: float):
        """Record plan completion for improving predictions."""
        try:
            # Update plan status
            self.update_plan(
                plan_id,
                {
                    "status": "completed",
                    "actual_hours": actual_hours,
                    "completed_at": datetime.utcnow(),
                },
            )

            # Record for prediction engine learning
            await self.prediction_engine.record_actual_duration(plan_id, actual_hours)

            logger.info(f"Recorded completion for plan {plan_id}: {actual_hours} hours")

        except Exception as e:
            logger.error(f"Failed to record plan completion: {e}")
