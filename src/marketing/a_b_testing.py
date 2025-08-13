"""
A/B testing module for marketing campaigns and optimization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from uuid import uuid4
import json
import random
import math
from enum import Enum

from ..common.redis_client import RedisClient
from ..common.database import DatabaseManager

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """A/B test status values"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class VariantType(str, Enum):
    """Variant types for A/B testing"""
    CONTROL = "control"
    VARIANT = "variant"


@dataclass
class Variant:
    """A/B test variant"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    variant_type: VariantType = VariantType.CONTROL
    content: Dict[str, Any] = field(default_factory=dict)
    traffic_percentage: float = 0.0
    is_winner: bool = False
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Experiment:
    """A/B test experiment"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    hypothesis: str = ""
    status: TestStatus = TestStatus.DRAFT
    variants: List[Variant] = field(default_factory=list)
    traffic_split: Dict[str, float] = field(default_factory=dict)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sample_size: Optional[int] = None
    confidence_level: float = 0.95
    primary_metric: str = ""
    secondary_metrics: List[str] = field(default_factory=list)
    target_audience: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TestResult:
    """A/B test results and statistical analysis"""
    experiment_id: str
    variant_id: str
    variant_name: str
    sample_size: int
    conversions: int
    conversion_rate: float
    revenue: float
    average_order_value: float
    statistical_significance: float
    confidence_interval: Tuple[float, float]
    p_value: float
    is_winner: bool
    calculated_at: datetime = field(default_factory=datetime.utcnow)


class ABTesting:
    """A/B testing engine for marketing optimization"""
    
    def __init__(self, redis_client: RedisClient, db_manager: DatabaseManager):
        self.redis_client = redis_client
        self.db_manager = db_manager
        self.experiments: Dict[str, Experiment] = {}
        self.variant_assignments: Dict[str, str] = {}  # user_id -> variant_id
        
    async def create_experiment(self, experiment_data: Dict[str, Any]) -> Experiment:
        """Create a new A/B test experiment"""
        try:
            # Create variants
            variants = []
            for variant_data in experiment_data.get("variants", []):
                variant = Variant(
                    name=variant_data["name"],
                    variant_type=VariantType(variant_data.get("type", "variant")),
                    content=variant_data.get("content", {}),
                    traffic_percentage=variant_data.get("traffic_percentage", 0.0)
                )
                variants.append(variant)
            
            # Create experiment
            experiment = Experiment(
                name=experiment_data["name"],
                description=experiment_data.get("description", ""),
                hypothesis=experiment_data.get("hypothesis", ""),
                variants=variants,
                traffic_split=experiment_data.get("traffic_split", {}),
                primary_metric=experiment_data.get("primary_metric", "conversion_rate"),
                secondary_metrics=experiment_data.get("secondary_metrics", []),
                target_audience=experiment_data.get("target_audience", {}),
                confidence_level=experiment_data.get("confidence_level", 0.95)
            )
            
            self.experiments[experiment.id] = experiment
            await self._store_experiment(experiment)
            
            logger.info(f"Created A/B test experiment: {experiment.name}")
            return experiment
            
        except Exception as e:
            logger.error(f"Failed to create experiment: {e}")
            raise
    
    async def start_experiment(self, experiment_id: str) -> bool:
        """Start an A/B test experiment"""
        try:
            if experiment_id not in self.experiments:
                logger.error(f"Experiment not found: {experiment_id}")
                return False
            
            experiment = self.experiments[experiment_id]
            
            # Validate experiment before starting
            if not self._validate_experiment(experiment):
                logger.error(f"Experiment validation failed: {experiment_id}")
                return False
            
            # Set start date and status
            experiment.start_date = datetime.utcnow()
            experiment.status = TestStatus.ACTIVE
            
            # Store updated experiment
            await self._store_experiment(experiment)
            
            logger.info(f"Started A/B test experiment: {experiment.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start experiment: {e}")
            return False
    
    async def stop_experiment(self, experiment_id: str) -> bool:
        """Stop an A/B test experiment"""
        try:
            if experiment_id not in self.experiments:
                logger.error(f"Experiment not found: {experiment_id}")
                return False
            
            experiment = self.experiments[experiment_id]
            experiment.status = TestStatus.STOPPED
            experiment.end_date = datetime.utcnow()
            
            # Calculate final results
            await self._calculate_final_results(experiment_id)
            
            await self._store_experiment(experiment)
            
            logger.info(f"Stopped A/B test experiment: {experiment.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop experiment: {e}")
            return False
    
    async def get_variant(self, experiment_id: str, user_id: str) -> Optional[Variant]:
        """Get the variant assignment for a user in an experiment"""
        try:
            if experiment_id not in self.experiments:
                return None
            
            experiment = self.experiments[experiment_id]
            
            if experiment.status != TestStatus.ACTIVE:
                return None
            
            # Check if user already has a variant assignment
            assignment_key = f"ab_test:{experiment_id}:{user_id}"
            existing_variant = await self.redis_client.get(assignment_key)
            
            if existing_variant:
                variant_id = existing_variant.decode()
                return next((v for v in experiment.variants if v.id == variant_id), None)
            
            # Assign new variant based on traffic split
            variant = await self._assign_variant(experiment, user_id)
            
            if variant:
                # Store assignment
                await self.redis_client.setex(
                    assignment_key,
                    86400 * 30,  # 30 days TTL
                    variant.id
                )
                
                # Track assignment
                await self._track_variant_assignment(experiment_id, user_id, variant.id)
            
            return variant
            
        except Exception as e:
            logger.error(f"Failed to get variant: {e}")
            return None
    
    async def track_conversion(self, experiment_id: str, user_id: str, 
                             metric_name: str, value: float = 1.0) -> bool:
        """Track a conversion or metric for A/B testing"""
        try:
            if experiment_id not in self.experiments:
                return False
            
            # Get user's variant assignment
            assignment_key = f"ab_test:{experiment_id}:{user_id}"
            variant_id = await self.redis_client.get(assignment_key)
            
            if not variant_id:
                return False
            
            variant_id = variant_id.decode()
            
            # Track the conversion
            conversion_key = f"ab_conversion:{experiment_id}:{variant_id}:{metric_name}"
            await self.redis_client.hincrby(conversion_key, "count", 1)
            await self.redis_client.hincrbyfloat(conversion_key, "value", value)
            
            # Track user conversion
            user_conversion_key = f"ab_user_conversion:{experiment_id}:{user_id}"
            await self.redis_client.hset(
                user_conversion_key,
                metric_name,
                json.dumps({
                    "value": value,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
            
            logger.debug(f"Tracked conversion: {metric_name}={value} for user {user_id} in variant {variant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track conversion: {e}")
            return False
    
    async def get_experiment_results(self, experiment_id: str) -> List[TestResult]:
        """Get current results for an A/B test experiment"""
        try:
            if experiment_id not in self.experiments:
                return []
            
            experiment = self.experiments[experiment_id]
            results = []
            
            for variant in experiment.variants:
                result = await self._calculate_variant_results(experiment, variant)
                if result:
                    results.append(result)
            
            # Sort by conversion rate
            results.sort(key=lambda x: x.conversion_rate, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get experiment results: {e}")
            return []
    
    async def _assign_variant(self, experiment: Experiment, user_id: str) -> Optional[Variant]:
        """Assign a variant to a user based on traffic split"""
        try:
            if not experiment.variants:
                return None
            
            # Use consistent hashing for user assignment
            user_hash = hash(user_id) % 100
            
            current_percentage = 0
            for variant in experiment.variants:
                current_percentage += variant.traffic_percentage
                if user_hash < current_percentage:
                    return variant
            
            # Fallback to first variant
            return experiment.variants[0]
            
        except Exception as e:
            logger.error(f"Failed to assign variant: {e}")
            return None
    
    async def _track_variant_assignment(self, experiment_id: str, user_id: str, variant_id: str):
        """Track variant assignment for analytics"""
        try:
            assignment_key = f"ab_assignment:{experiment_id}:{variant_id}"
            await self.redis_client.hincrby(assignment_key, "count", 1)
            
            # Store user assignment
            user_assignments_key = f"ab_user_assignments:{experiment_id}"
            await self.redis_client.hset(user_assignments_key, user_id, variant_id)
            
        except Exception as e:
            logger.error(f"Failed to track variant assignment: {e}")
    
    async def _calculate_variant_results(self, experiment: Experiment, variant: Variant) -> Optional[TestResult]:
        """Calculate statistical results for a variant"""
        try:
            # Get assignment count
            assignment_key = f"ab_assignment:{experiment.id}:{variant.id}"
            assignment_data = await self.redis_client.hgetall(assignment_key)
            
            if not assignment_data:
                return None
            
            sample_size = int(assignment_data.get(b"count", 0))
            if sample_size == 0:
                return None
            
            # Get conversion data
            conversion_key = f"ab_conversion:{experiment.id}:{variant.id}:{experiment.primary_metric}"
            conversion_data = await self.redis_client.hgetall(conversion_key)
            
            if not conversion_data:
                return None
            
            conversions = int(conversion_data.get(b"count", 0))
            total_value = float(conversion_data.get(b"value", 0))
            
            # Calculate basic metrics
            conversion_rate = (conversions / sample_size) * 100 if sample_size > 0 else 0
            revenue = total_value
            average_order_value = total_value / conversions if conversions > 0 else 0
            
            # Calculate statistical significance (simplified)
            statistical_significance = self._calculate_statistical_significance(
                sample_size, conversions, experiment.variants[0].id == variant.id
            )
            
            # Calculate confidence interval (simplified)
            confidence_interval = self._calculate_confidence_interval(
                sample_size, conversions, experiment.confidence_level
            )
            
            # Calculate p-value (simplified)
            p_value = self._calculate_p_value(sample_size, conversions, experiment.variants[0].id == variant.id)
            
            result = TestResult(
                experiment_id=experiment.id,
                variant_id=variant.id,
                variant_name=variant.name,
                sample_size=sample_size,
                conversions=conversions,
                conversion_rate=conversion_rate,
                revenue=revenue,
                average_order_value=average_order_value,
                statistical_significance=statistical_significance,
                confidence_interval=confidence_interval,
                p_value=p_value,
                is_winner=False  # Will be determined later
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate variant results: {e}")
            return None
    
    def _calculate_statistical_significance(self, sample_size: int, conversions: int, is_control: bool) -> float:
        """Calculate statistical significance (simplified implementation)"""
        try:
            if sample_size == 0 or conversions == 0:
                return 0.0
            
            # This is a simplified calculation
            # In practice, you'd use proper statistical tests like chi-square or t-test
            conversion_rate = conversions / sample_size
            standard_error = math.sqrt((conversion_rate * (1 - conversion_rate)) / sample_size)
            
            # Z-score approximation
            z_score = conversion_rate / standard_error if standard_error > 0 else 0
            
            # Convert to significance level (simplified)
            significance = min(95.0, max(0.0, z_score * 10))
            
            return significance
            
        except Exception as e:
            logger.error(f"Failed to calculate statistical significance: {e}")
            return 0.0
    
    def _calculate_confidence_interval(self, sample_size: int, conversions: int, confidence_level: float) -> Tuple[float, float]:
        """Calculate confidence interval (simplified implementation)"""
        try:
            if sample_size == 0:
                return (0.0, 0.0)
            
            conversion_rate = conversions / sample_size
            
            # Simplified confidence interval calculation
            # In practice, you'd use proper statistical formulas
            margin_of_error = 1.96 * math.sqrt((conversion_rate * (1 - conversion_rate)) / sample_size)
            
            lower_bound = max(0.0, conversion_rate - margin_of_error)
            upper_bound = min(1.0, conversion_rate + margin_of_error)
            
            return (lower_bound * 100, upper_bound * 100)
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence interval: {e}")
            return (0.0, 0.0)
    
    def _calculate_p_value(self, sample_size: int, conversions: int, is_control: bool) -> float:
        """Calculate p-value (simplified implementation)"""
        try:
            if sample_size == 0:
                return 1.0
            
            # This is a simplified p-value calculation
            # In practice, you'd use proper statistical tests
            conversion_rate = conversions / sample_size
            
            # Simplified p-value based on conversion rate and sample size
            if is_control:
                # Control group - baseline
                p_value = 0.5
            else:
                # Variant group - compare to control
                # Simplified: lower p-value for higher conversion rates
                p_value = max(0.01, 1.0 - (conversion_rate * 0.8))
            
            return p_value
            
        except Exception as e:
            logger.error(f"Failed to calculate p-value: {e}")
            return 1.0
    
    async def _calculate_final_results(self, experiment_id: str):
        """Calculate final results and determine winner"""
        try:
            results = await self.get_experiment_results(experiment_id)
            
            if not results:
                return
            
            # Find the winner based on primary metric
            winner = max(results, key=lambda x: x.conversion_rate)
            
            # Mark winner
            for result in results:
                result.is_winner = (result.variant_id == winner.variant_id)
            
            # Update experiment variants
            experiment = self.experiments[experiment_id]
            for variant in experiment.variants:
                variant.is_winner = (variant.id == winner.variant_id)
            
            logger.info(f"Experiment {experiment_id} completed. Winner: {winner.variant_name}")
            
        except Exception as e:
            logger.error(f"Failed to calculate final results: {e}")
    
    def _validate_experiment(self, experiment: Experiment) -> bool:
        """Validate experiment before starting"""
        try:
            # Check if experiment has variants
            if not experiment.variants:
                logger.error("Experiment must have at least one variant")
                return False
            
            # Check if traffic split adds up to 100%
            total_traffic = sum(v.traffic_percentage for v in experiment.variants)
            if abs(total_traffic - 100.0) > 0.01:
                logger.error(f"Traffic split must equal 100%, got {total_traffic}%")
                return False
            
            # Check if primary metric is specified
            if not experiment.primary_metric:
                logger.error("Primary metric must be specified")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Experiment validation failed: {e}")
            return False
    
    async def _store_experiment(self, experiment: Experiment):
        """Store experiment in database"""
        try:
            # Implementation would depend on your database schema
            logger.debug(f"Storing experiment in database: {experiment.id}")
        except Exception as e:
            logger.error(f"Failed to store experiment: {e}")
