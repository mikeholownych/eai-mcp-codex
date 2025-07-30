"""Predictive Analytics & Machine Learning Engine for Performance Prediction."""

import numpy as np
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, cast
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from pathlib import Path

from ..common.logging import get_logger
from ..plan_management.models import Plan

logger = get_logger("prediction_engine")


class RiskLevel(str, Enum):
    """Risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PredictionResult:
    """Result of performance prediction."""

    estimated_duration: float  # in hours
    confidence_interval: Tuple[float, float]  # (lower, upper) bounds
    confidence_score: float  # 0-1
    risk_factors: List[Dict[str, Any]]
    resource_requirements: Dict[str, Any]
    milestone_predictions: List[Dict[str, Any]]
    similar_projects: List[str]
    prediction_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HistoricalDataPoint:
    """Historical project data point."""

    project_id: str
    complexity_score: float
    team_size: int
    duration_hours: float
    success_rate: float
    technology_stack: List[str]
    features: Dict[str, float]
    completion_date: datetime


@dataclass
class AnomalyDetection:
    """Anomaly detection result."""

    is_anomaly: bool
    anomaly_score: float
    anomaly_type: str
    description: str
    recommended_action: str


class FeatureExtractor:
    """Extracts features from plans for ML predictions."""

    def __init__(self):
        self.complexity_weights = {
            "task_count": 0.3,
            "dependency_complexity": 0.25,
            "technology_diversity": 0.2,
            "integration_points": 0.15,
            "team_experience": 0.1,
        }

    def extract_features(self, plan: Plan) -> Dict[str, float]:
        """Extract numerical features from a plan."""
        features: Dict[str, float] = {}

        # Basic metrics
        features["task_count"] = (
            float(len(plan.tasks)) if hasattr(plan, "tasks") else 0.0
        )
        features["estimated_hours"] = float(plan.estimated_hours or 0)
        features["priority_score"] = self._priority_to_score(plan.priority)

        # Complexity metrics
        features["complexity_score"] = self._calculate_complexity_score(plan)
        features["dependency_score"] = self._calculate_dependency_score(plan)
        features["integration_complexity"] = self._calculate_integration_complexity(
            plan
        )

        # Text-based features
        features["description_length"] = float(len(plan.description))
        features["title_complexity"] = float(len(plan.title.split()))

        # Risk indicators
        features["risk_keywords"] = self._count_risk_keywords(plan.description)
        features["technical_debt_indicators"] = self._count_technical_debt_keywords(
            plan.description
        )

        # Timeline features
        if plan.start_date and plan.end_date:
            features["planned_duration"] = (
                plan.end_date - plan.start_date
            ).total_seconds() / 3600.0
        else:
            features["planned_duration"] = features["estimated_hours"]

        # Derived features
        features["velocity_indicator"] = features["task_count"] / max(
            features["planned_duration"], 1
        )
        features["scope_density"] = features["description_length"] / max(
            features["task_count"], 1
        )

        return features

    def _priority_to_score(self, priority: str) -> float:
        """Convert priority to numerical score."""
        priority_map = {
            "low": 0.25,
            "medium": 0.5,
            "high": 0.75,
            "urgent": 1.0,
            "critical": 1.0,
        }
        return priority_map.get(priority.lower(), 0.5)

    def _calculate_complexity_score(self, plan: Plan) -> float:
        """Calculate overall complexity score."""
        base_complexity = 0.5

        # Adjust based on description complexity
        description = plan.description.lower()
        complexity_keywords = [
            "algorithm",
            "optimization",
            "machine learning",
            "ai",
            "blockchain",
            "microservices",
            "distributed",
            "real-time",
            "concurrent",
            "parallel",
            "security",
            "encryption",
            "compliance",
            "integration",
            "migration",
        ]

        keyword_count = sum(
            1 for keyword in complexity_keywords if keyword in description
        )
        complexity_adjustment = min(keyword_count * 0.1, 0.4)

        return min(base_complexity + complexity_adjustment, 1.0)

    def _calculate_dependency_score(self, plan: Plan) -> float:
        """Calculate dependency complexity score."""
        # Simplified implementation - would analyze task dependencies in real system
        task_count = len(plan.tasks) if hasattr(plan, "tasks") else 0

        if task_count == 0:
            return 0.0
        elif task_count < 5:
            return 0.2
        elif task_count < 15:
            return 0.5
        else:
            return 0.8

    def _calculate_integration_complexity(self, plan: Plan) -> float:
        """Calculate integration complexity score."""
        integration_keywords = [
            "api",
            "integration",
            "third-party",
            "external",
            "service",
            "database",
            "cloud",
            "aws",
            "azure",
            "gcp",
            "webhook",
        ]

        description = plan.description.lower()
        integration_count = sum(
            1 for keyword in integration_keywords if keyword in description
        )

        return min(integration_count * 0.15, 1.0)

    def _count_risk_keywords(self, text: str) -> float:
        """Count risk-indicating keywords."""
        risk_keywords = [
            "legacy",
            "deprecated",
            "experimental",
            "beta",
            "unknown",
            "complex",
            "difficult",
            "challenging",
            "risky",
            "uncertain",
        ]

        text_lower = text.lower()
        return sum(1 for keyword in risk_keywords if keyword in text_lower)

    def _count_technical_debt_keywords(self, text: str) -> float:
        """Count technical debt indicators."""
        debt_keywords = [
            "refactor",
            "cleanup",
            "technical debt",
            "legacy code",
            "workaround",
            "hack",
            "temporary",
            "quick fix",
        ]

        text_lower = text.lower()
        return sum(1 for keyword in debt_keywords if keyword in text_lower)


class TimeSeriesPredictor:
    """Time series prediction model for project duration."""

    def __init__(self):
        self.model_weights = None
        self.historical_data = []
        self.is_trained = False

    def train(self, historical_data: List[HistoricalDataPoint]):
        """Train the prediction model on historical data."""
        self.historical_data = historical_data

        if len(historical_data) < 3:
            logger.warning(
                "Insufficient historical data for training. Using default weights."
            )
            self._use_default_weights()
            return

        # Simple linear regression implementation
        feature_matrix = []
        duration_vector = []

        for data_point in historical_data:
            features = list(data_point.features.values())
            feature_matrix.append(features)
            duration_vector.append(data_point.duration_hours)

        # Convert to numpy arrays
        X = np.array(feature_matrix)
        y = np.array(duration_vector)

        # Add bias term
        X = np.column_stack([np.ones(X.shape[0]), X])

        try:
            # Solve normal equations: weights = (X^T * X)^-1 * X^T * y
            XtX = np.dot(X.T, X)
            Xty = np.dot(X.T, y)
            self.model_weights = np.linalg.solve(XtX, Xty)
            self.is_trained = True
            logger.info(f"Model trained on {len(historical_data)} data points")
        except np.linalg.LinAlgError:
            logger.warning("Model training failed. Using default weights.")
            self._use_default_weights()

    def predict(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Predict duration and confidence."""
        if not self.is_trained:
            return self._default_prediction(features)

        # Prepare feature vector
        feature_vector = [1.0]  # bias term
        feature_vector.extend(features.values())

        # Make prediction
        prediction = np.dot(self.model_weights, feature_vector)

        # Calculate confidence based on historical variance
        confidence = self._calculate_confidence(features)

        return max(0.1, prediction), confidence

    def _use_default_weights(self):
        """Use default weights when training is not possible."""
        # Default feature weights based on domain knowledge
        self.model_weights = [
            10.0,  # bias
            2.0,  # task_count
            1.0,  # estimated_hours coefficient
            5.0,  # priority_score
            8.0,  # complexity_score
            3.0,  # dependency_score
            4.0,  # integration_complexity
            0.1,  # description_length
            1.0,  # title_complexity
            2.0,  # risk_keywords
            1.5,  # technical_debt_indicators
            0.8,  # planned_duration
            -2.0,  # velocity_indicator (negative - higher velocity = less time)
            0.05,  # scope_density
        ]
        self.is_trained = True

    def _default_prediction(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Make prediction using heuristics when no training data is available."""
        base_hours = features.get("task_count", 1) * 8  # 8 hours per task
        complexity_multiplier = 1.0 + features.get("complexity_score", 0.5)

        prediction = base_hours * complexity_multiplier
        confidence = 0.6  # Lower confidence for heuristic predictions

        return prediction, confidence

    def _calculate_confidence(self, features: Dict[str, float]) -> float:
        """Calculate prediction confidence based on feature similarity to training data."""
        if not self.historical_data:
            return 0.6

        # Find similarity to historical projects
        similarities = []
        for data_point in self.historical_data:
            similarity = self._calculate_feature_similarity(
                features, data_point.features
            )
            similarities.append(similarity)

        # Confidence based on maximum similarity
        max_similarity = max(similarities) if similarities else 0.0
        base_confidence = 0.5 + (max_similarity * 0.4)  # 0.5 to 0.9

        return min(0.95, max(0.3, base_confidence))

    def _calculate_feature_similarity(
        self, features1: Dict[str, float], features2: Dict[str, float]
    ) -> float:
        """Calculate cosine similarity between feature vectors."""
        common_keys = set(features1.keys()) & set(features2.keys())
        if not common_keys:
            return 0.0

        vec1 = np.array([features1[key] for key in common_keys])
        vec2 = np.array([features2[key] for key in common_keys])

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norms = np.linalg.norm(vec1) * np.linalg.norm(vec2)

        if norms == 0:
            return 0.0

        return dot_product / norms


class AnomalyDetectionSystem:
    """Detects anomalies in project patterns and performance."""

    def __init__(self):
        self.thresholds = {
            "duration_variance": 2.0,  # Standard deviations
            "complexity_threshold": 0.8,
            "risk_score_threshold": 5.0,
        }

    def detect_anomalies(
        self,
        plan: Plan,
        features: Dict[str, float],
        prediction: PredictionResult,
        historical_data: List[HistoricalDataPoint],
    ) -> List[AnomalyDetection]:
        """Detect various types of anomalies."""
        anomalies = []

        # Duration anomaly detection
        duration_anomaly = self._detect_duration_anomaly(prediction, historical_data)
        if duration_anomaly:
            anomalies.append(duration_anomaly)

        # Complexity anomaly detection
        complexity_anomaly = self._detect_complexity_anomaly(features)
        if complexity_anomaly:
            anomalies.append(complexity_anomaly)

        # Risk score anomaly detection
        risk_anomaly = self._detect_risk_anomaly(features)
        if risk_anomaly:
            anomalies.append(risk_anomaly)

        # Scope creep detection
        scope_anomaly = self._detect_scope_anomaly(features)
        if scope_anomaly:
            anomalies.append(scope_anomaly)

        return anomalies

    def _detect_duration_anomaly(
        self, prediction: PredictionResult, historical_data: List[HistoricalDataPoint]
    ) -> Optional[AnomalyDetection]:
        """Detect if predicted duration is anomalous."""
        if not historical_data:
            return None

        historical_durations = [dp.duration_hours for dp in historical_data]
        mean_duration = np.mean(historical_durations)
        std_duration = np.std(historical_durations)

        if std_duration == 0:
            return None

        z_score = abs(prediction.estimated_duration - mean_duration) / std_duration

        if z_score > self.thresholds["duration_variance"]:
            return AnomalyDetection(
                is_anomaly=True,
                anomaly_score=min(z_score / self.thresholds["duration_variance"], 5.0),
                anomaly_type="duration_outlier",
                description=f"Predicted duration ({prediction.estimated_duration:.1f}h) is {z_score:.1f} standard deviations from historical average",
                recommended_action="Review project scope and complexity assessment",
            )

        return None

    def _detect_complexity_anomaly(
        self, features: Dict[str, float]
    ) -> Optional[AnomalyDetection]:
        """Detect unusually high complexity."""
        complexity_score = features.get("complexity_score", 0.0)

        if complexity_score > self.thresholds["complexity_threshold"]:
            return AnomalyDetection(
                is_anomaly=True,
                anomaly_score=complexity_score,
                anomaly_type="high_complexity",
                description=f"Project complexity score ({complexity_score:.2f}) exceeds normal threshold",
                recommended_action="Consider breaking down into smaller phases or adding expert resources",
            )

        return None

    def _detect_risk_anomaly(
        self, features: Dict[str, float]
    ) -> Optional[AnomalyDetection]:
        """Detect high risk indicators."""
        risk_score = features.get("risk_keywords", 0) + features.get(
            "technical_debt_indicators", 0
        )

        if risk_score > self.thresholds["risk_score_threshold"]:
            return AnomalyDetection(
                is_anomaly=True,
                anomaly_score=min(
                    risk_score / self.thresholds["risk_score_threshold"], 5.0
                ),
                anomaly_type="high_risk",
                description=f"High risk indicator count ({risk_score}) detected in project description",
                recommended_action="Conduct detailed risk assessment and mitigation planning",
            )

        return None

    def _detect_scope_anomaly(
        self, features: Dict[str, float]
    ) -> Optional[AnomalyDetection]:
        """Detect potential scope creep indicators."""
        scope_density = features.get("scope_density", 0)
        task_count = features.get("task_count", 0)

        # High scope density might indicate unclear requirements
        if scope_density > 100 and task_count > 10:
            return AnomalyDetection(
                is_anomaly=True,
                anomaly_score=min(scope_density / 100, 3.0),
                anomaly_type="scope_uncertainty",
                description="High ratio of description length to task count suggests unclear requirements",
                recommended_action="Refine requirements and break down tasks more granularly",
            )

        return None


class PerformancePredictionEngine:
    """Main engine for predicting project performance and identifying risks."""

    def __init__(self, db_path: str = "data/predictions.db"):
        self.db_path = db_path
        self.feature_extractor = FeatureExtractor()
        self.ml_model = TimeSeriesPredictor()
        self.anomaly_detector = AnomalyDetectionSystem()
        self._ensure_database()
        self._load_historical_data()

    def _ensure_database(self):
        """Create database for storing predictions and historical data."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS historical_projects (
                    project_id TEXT PRIMARY KEY,
                    plan_data TEXT NOT NULL,
                    features TEXT NOT NULL,
                    actual_duration REAL NOT NULL,
                    success_rate REAL DEFAULT 1.0,
                    completion_date TIMESTAMP NOT NULL,
                    team_size INTEGER DEFAULT 1,
                    technology_stack TEXT DEFAULT '[]',
                    complexity_score REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    predicted_duration REAL NOT NULL,
                    confidence_score REAL NOT NULL,
                    risk_factors TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actual_duration REAL,
                    accuracy_score REAL
                );
                
                CREATE INDEX IF NOT EXISTS idx_predictions_plan ON predictions(plan_id);
                CREATE INDEX IF NOT EXISTS idx_historical_completion ON historical_projects(completion_date);
            """
            )

    def _load_historical_data(self):
        """Load historical data and train the model."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT project_id, features, actual_duration, success_rate, 
                       technology_stack, completion_date, team_size, complexity_score
                FROM historical_projects
                ORDER BY completion_date DESC
                LIMIT 100
            """
            )

            historical_data = []
            for row in cursor.fetchall():
                try:
                    features = json.loads(row[1])
                    tech_stack = json.loads(row[4])
                    completion_date = datetime.fromisoformat(row[5])

                    data_point = HistoricalDataPoint(
                        project_id=row[0],
                        features=features,
                        duration_hours=row[2],
                        success_rate=row[3],
                        technology_stack=tech_stack,
                        completion_date=completion_date,
                        team_size=row[6],
                        complexity_score=row[7],
                    )
                    historical_data.append(data_point)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(
                        f"Failed to parse historical data for project {row[0]}: {e}"
                    )

            if historical_data:
                self.ml_model.train(historical_data)
                logger.info(
                    f"Loaded {len(historical_data)} historical projects for training"
                )

    async def predict_workflow_duration(self, plan: Plan) -> PredictionResult:
        """Predict workflow duration with confidence intervals and risk factors."""
        try:
            # Extract features from plan
            features = self.feature_extractor.extract_features(plan)

            # Make prediction
            predicted_duration, confidence = self.ml_model.predict(features)

            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(
                predicted_duration, confidence
            )

            # Identify risk factors
            risk_factors = self._identify_risk_factors(plan, features)

            # Calculate resource requirements
            resource_requirements = self._calculate_resource_requirements(
                predicted_duration, features
            )

            # Generate milestone predictions
            milestone_predictions = self._generate_milestone_predictions(
                predicted_duration, features
            )

            # Find similar projects
            similar_projects = self._find_similar_projects(features)

            # Create prediction result
            prediction_result = PredictionResult(
                estimated_duration=predicted_duration,
                confidence_interval=confidence_interval,
                confidence_score=confidence,
                risk_factors=risk_factors,
                resource_requirements=resource_requirements,
                milestone_predictions=milestone_predictions,
                similar_projects=similar_projects,
            )

            # Detect anomalies
            anomalies = self.anomaly_detector.detect_anomalies(
                plan, features, prediction_result, self.ml_model.historical_data
            )

            # Add anomalies to risk factors
            for anomaly in anomalies:
                if anomaly.is_anomaly:
                    prediction_result.risk_factors.append(
                        {
                            "type": "anomaly",
                            "level": (
                                "high" if anomaly.anomaly_score > 2.0 else "medium"
                            ),
                            "description": anomaly.description,
                            "recommendation": anomaly.recommended_action,
                            "score": anomaly.anomaly_score,
                        }
                    )

            # Store prediction
            await self._store_prediction(plan.id, prediction_result, features)

            return prediction_result

        except Exception as e:
            logger.error(f"Prediction failed for plan {plan.id}: {e}")
            # Return fallback prediction
            return self._fallback_prediction(plan)

    def _calculate_confidence_interval(
        self, prediction: float, confidence: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval for prediction."""
        # Confidence interval based on prediction uncertainty
        uncertainty = prediction * (1.0 - confidence) * 0.5

        lower_bound = max(0.1, prediction - uncertainty)
        upper_bound = prediction + uncertainty

        return (lower_bound, upper_bound)

    def _identify_risk_factors(
        self, plan: Plan, features: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Identify risk factors that could affect project duration."""
        risk_factors = []

        # High complexity risk
        complexity_score = features.get("complexity_score", 0.0)
        if complexity_score > 0.7:
            risk_factors.append(
                {
                    "type": "complexity",
                    "level": RiskLevel.HIGH.value,
                    "description": "Project has high technical complexity",
                    "impact": "May require additional time for research and implementation",
                    "mitigation": "Allocate buffer time and consider expert consultation",
                    "probability": 0.7,
                }
            )

        # Dependency risk
        dependency_score = features.get("dependency_score", 0.0)
        if dependency_score > 0.6:
            risk_factors.append(
                {
                    "type": "dependencies",
                    "level": RiskLevel.MEDIUM.value,
                    "description": "Project has complex dependencies",
                    "impact": "Dependencies may cause delays or require coordination",
                    "mitigation": "Create detailed dependency map and contingency plans",
                    "probability": 0.5,
                }
            )

        # Integration risk
        integration_complexity = features.get("integration_complexity", 0.0)
        if integration_complexity > 0.5:
            risk_factors.append(
                {
                    "type": "integration",
                    "level": RiskLevel.MEDIUM.value,
                    "description": "Project requires multiple integrations",
                    "impact": "Integration testing and troubleshooting may extend timeline",
                    "mitigation": "Plan integration testing phases and API documentation review",
                    "probability": 0.4,
                }
            )

        # Scope uncertainty risk
        risk_keywords = features.get("risk_keywords", 0)
        if risk_keywords > 3:
            risk_factors.append(
                {
                    "type": "scope_uncertainty",
                    "level": RiskLevel.HIGH.value,
                    "description": "Project contains uncertainty indicators",
                    "impact": "Requirements may change, leading to scope creep",
                    "mitigation": "Define clear acceptance criteria and change management process",
                    "probability": 0.6,
                }
            )

        # Technical debt risk
        tech_debt = features.get("technical_debt_indicators", 0)
        if tech_debt > 2:
            risk_factors.append(
                {
                    "type": "technical_debt",
                    "level": RiskLevel.MEDIUM.value,
                    "description": "Project involves technical debt cleanup",
                    "impact": "Legacy code may require additional refactoring time",
                    "mitigation": "Allocate time for code review and refactoring",
                    "probability": 0.5,
                }
            )

        return risk_factors

    def _calculate_resource_requirements(
        self, duration: float, features: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate resource requirements based on prediction."""
        complexity_score = features.get("complexity_score", 0.5)
        task_count = features.get("task_count", 1)

        # Estimate team size needed
        if duration > 160:  # > 4 weeks
            recommended_team_size = max(2, int(task_count / 5))
        elif duration > 80:  # > 2 weeks
            recommended_team_size = max(1, int(task_count / 8))
        else:
            recommended_team_size = 1

        # Skill requirements based on complexity
        skill_level = (
            "senior"
            if complexity_score > 0.7
            else "mid" if complexity_score > 0.4 else "junior"
        )

        return {
            "recommended_team_size": recommended_team_size,
            "skill_level_required": skill_level,
            "estimated_budget_hours": duration * recommended_team_size,
            "specializations_needed": self._identify_specializations(features),
            "tools_required": self._identify_tools_needed(features),
            "timeline_buffer_percentage": min(50, max(20, complexity_score * 50)),
        }

    def _identify_specializations(self, features: Dict[str, float]) -> List[str]:
        """Identify required specializations based on features."""
        specializations = ["general_development"]

        complexity_score = features.get("complexity_score", 0.0)
        integration_complexity = features.get("integration_complexity", 0.0)

        if complexity_score > 0.7:
            specializations.append("senior_architect")

        if integration_complexity > 0.5:
            specializations.append("integration_specialist")

        if features.get("risk_keywords", 0) > 2:
            specializations.append("technical_lead")

        return specializations

    def _identify_tools_needed(self, features: Dict[str, float]) -> List[str]:
        """Identify tools needed based on project features."""
        tools = ["development_environment", "version_control"]

        if features.get("integration_complexity", 0) > 0.3:
            tools.extend(["api_testing_tools", "integration_monitoring"])

        if features.get("complexity_score", 0) > 0.6:
            tools.extend(["performance_profilers", "architecture_tools"])

        return tools

    def _generate_milestone_predictions(
        self, duration: float, features: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate milestone predictions."""
        complexity_score = features.get("complexity_score", 0.5)

        # Standard milestone breakdown
        milestones = [
            {"name": "Planning & Design", "percentage": 0.15},
            {"name": "Development Phase 1", "percentage": 0.35},
            {"name": "Development Phase 2", "percentage": 0.35},
            {"name": "Testing & QA", "percentage": 0.10},
            {"name": "Deployment & Documentation", "percentage": 0.05},
        ]

        # Adjust based on complexity
        if complexity_score > 0.7:
            milestones[0]["percentage"] = 0.25  # More planning time
            milestones[3]["percentage"] = 0.15  # More testing time
            milestones[1]["percentage"] = 0.30
            milestones[2]["percentage"] = 0.25

        milestone_predictions = []
        cumulative_hours = 0.0

        for milestone in milestones:
            percentage = cast(float, milestone.get("percentage", 0.0))
            milestone_hours = duration * percentage
            cumulative_hours += milestone_hours

            milestone_predictions.append(
                {
                    "name": milestone["name"],
                    "estimated_hours": milestone_hours,
                    "cumulative_hours": cumulative_hours,
                    "percentage_complete": (cumulative_hours / duration) * 100,
                    "confidence": 0.8
                    - (complexity_score * 0.2),  # Lower confidence for complex projects
                }
            )

        return milestone_predictions

    def _find_similar_projects(self, features: Dict[str, float]) -> List[str]:
        """Find similar historical projects."""
        if not self.ml_model.historical_data:
            return []

        similarities = []
        for data_point in self.ml_model.historical_data:
            similarity = self.ml_model._calculate_feature_similarity(
                features, data_point.features
            )
            similarities.append((data_point.project_id, similarity))

        # Sort by similarity and return top 3
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [project_id for project_id, _ in similarities[:3]]

    def _fallback_prediction(self, plan: Plan) -> PredictionResult:
        """Provide fallback prediction when main prediction fails."""
        estimated_hours = plan.estimated_hours or 40  # Default to 1 week

        return PredictionResult(
            estimated_duration=estimated_hours,
            confidence_interval=(estimated_hours * 0.7, estimated_hours * 1.5),
            confidence_score=0.5,
            risk_factors=[
                {
                    "type": "prediction_uncertainty",
                    "level": RiskLevel.MEDIUM.value,
                    "description": "Limited data available for accurate prediction",
                    "impact": "Prediction may be less accurate",
                    "mitigation": "Monitor progress closely and adjust estimates",
                    "probability": 0.8,
                }
            ],
            resource_requirements={
                "recommended_team_size": 1,
                "skill_level_required": "mid",
                "estimated_budget_hours": estimated_hours,
                "specializations_needed": ["general_development"],
                "tools_required": ["development_environment"],
                "timeline_buffer_percentage": 30,
            },
            milestone_predictions=[],
            similar_projects=[],
        )

    async def _store_prediction(
        self, plan_id: str, prediction: PredictionResult, features: Dict[str, float]
    ):
        """Store prediction in database for future analysis."""
        prediction_id = f"pred_{plan_id}_{int(datetime.utcnow().timestamp())}"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO predictions (
                        prediction_id, plan_id, predicted_duration, confidence_score, risk_factors
                    ) VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        prediction_id,
                        plan_id,
                        prediction.estimated_duration,
                        prediction.confidence_score,
                        json.dumps(prediction.risk_factors),
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to store prediction: {e}")

    async def record_actual_duration(self, plan_id: str, actual_duration: float):
        """Record actual duration for a completed project to improve predictions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update prediction accuracy
                conn.execute(
                    """
                    UPDATE predictions 
                    SET actual_duration = ?, 
                        accuracy_score = 1.0 - ABS(predicted_duration - ?) / predicted_duration
                    WHERE plan_id = ? AND actual_duration IS NULL
                """,
                    (actual_duration, actual_duration, plan_id),
                )

                logger.info(
                    f"Recorded actual duration {actual_duration}h for plan {plan_id}"
                )
        except Exception as e:
            logger.error(f"Failed to record actual duration: {e}")

    def get_prediction_accuracy(self) -> Dict[str, float]:
        """Get overall prediction accuracy metrics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT AVG(accuracy_score) as avg_accuracy,
                           COUNT(*) as total_predictions,
                           COUNT(actual_duration) as completed_predictions
                    FROM predictions
                    WHERE accuracy_score IS NOT NULL
                """
                )

                row = cursor.fetchone()
                if row and row[0] is not None:
                    return {
                        "average_accuracy": row[0],
                        "total_predictions": row[1],
                        "completed_predictions": row[2],
                        "completion_rate": row[2] / max(row[1], 1),
                    }
        except Exception as e:
            logger.error(f"Failed to get prediction accuracy: {e}")

        return {
            "average_accuracy": 0.0,
            "total_predictions": 0,
            "completed_predictions": 0,
            "completion_rate": 0.0,
        }
