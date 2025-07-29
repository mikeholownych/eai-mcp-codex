"""
Threat Detection and Anomaly Detection System

Advanced security threat detection using machine learning and rule-based approaches:
- Real-time anomaly detection for user behavior and system events
- Threat intelligence integration
- Pattern recognition for attack detection
- Automated threat scoring and risk assessment
- Integration with security incident response
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Set, Tuple, Callable, Protocol
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import ipaddress
import hashlib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from user_agents import parse as parse_user_agent

from ..common.redis_client import RedisClient
from .audit_logging import AuditLogger, AuditEventType, AuditEventSeverity

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Types of security threats"""
    BRUTE_FORCE = "brute_force"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    SUSPICIOUS_IP = "suspicious_ip"
    RATE_LIMIT_ABUSE = "rate_limit_abuse"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    INJECTION_ATTACK = "injection_attack"
    CREDENTIAL_STUFFING = "credential_stuffing"
    ACCOUNT_TAKEOVER = "account_takeover"
    BOT_ACTIVITY = "bot_activity"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    TIME_BASED_ANOMALY = "time_based_anomaly"
    VOLUME_ANOMALY = "volume_anomaly"


class DetectionMethod(str, Enum):
    """Detection methods used"""
    RULE_BASED = "rule_based"
    STATISTICAL_ANOMALY = "statistical_anomaly"
    MACHINE_LEARNING = "machine_learning"
    THREAT_INTELLIGENCE = "threat_intelligence"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"


@dataclass
class ThreatEvent:
    """Represents a detected threat event"""
    event_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    detection_method: DetectionMethod
    timestamp: datetime
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    risk_score: float = 0.0
    confidence: float = 0.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_blocked: bool = False
    is_resolved: bool = False
    false_positive: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission"""
        return {
            "event_id": self.event_id,
            "threat_type": self.threat_type.value,
            "threat_level": self.threat_level.value,
            "detection_method": self.detection_method.value,
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "user_agent": self.user_agent,
            "endpoint": self.endpoint,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata,
            "is_blocked": self.is_blocked,
            "is_resolved": self.is_resolved,
            "false_positive": self.false_positive
        }


@dataclass
class UserBehaviorProfile:
    """User behavior profile for anomaly detection"""
    user_id: str
    typical_ips: Set[str] = field(default_factory=set)
    typical_countries: Set[str] = field(default_factory=set)
    typical_user_agents: Set[str] = field(default_factory=set)
    typical_login_hours: List[int] = field(default_factory=list)
    typical_endpoints: Dict[str, int] = field(default_factory=dict)
    avg_request_rate: float = 0.0
    avg_session_duration: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    total_requests: int = 0
    failed_logins: int = 0
    successful_logins: int = 0


class ThreatDetector(Protocol):
    """Protocol for threat detectors"""
    async def detect(self, event_data: Dict[str, Any]) -> Optional[ThreatEvent]:
        ...


class BruteForceDetector:
    """Detects brute force attacks"""
    
    def __init__(self, redis_client: RedisClient, 
                 max_attempts: int = 5, 
                 time_window: int = 300,  # 5 minutes
                 lockout_duration: int = 900):  # 15 minutes
        self.redis_client = redis_client
        self.max_attempts = max_attempts
        self.time_window = time_window
        self.lockout_duration = lockout_duration
    
    async def detect(self, event_data: Dict[str, Any]) -> Optional[ThreatEvent]:
        """Detect brute force attempts"""
        if event_data.get("event_type") != "auth.login.failure":
            return None
        
        source_ip = event_data.get("source_ip")
        user_id = event_data.get("user_id")
        
        if not source_ip:
            return None
        
        # Track failed attempts by IP
        key = f"brute_force:{source_ip}"
        current_time = int(time.time())
        
        # Add current attempt
        await self.redis_client.client.zadd(key, {str(current_time): current_time})
        await self.redis_client.client.expire(key, self.time_window)
        
        # Count attempts in time window
        cutoff = current_time - self.time_window
        await self.redis_client.client.zremrangebyscore(key, 0, cutoff)
        attempt_count = await self.redis_client.client.zcard(key)
        
        if attempt_count >= self.max_attempts:
            # Brute force detected
            event_id = f"bf_{int(current_time)}_{hashlib.md5(source_ip.encode()).hexdigest()[:8]}"
            
            return ThreatEvent(
                event_id=event_id,
                threat_type=ThreatType.BRUTE_FORCE,
                threat_level=ThreatLevel.HIGH,
                detection_method=DetectionMethod.RULE_BASED,
                timestamp=datetime.utcnow(),
                source_ip=source_ip,
                user_id=user_id,
                risk_score=min(attempt_count / self.max_attempts, 1.0) * 10,
                confidence=0.9,
                evidence={
                    "failed_attempts": attempt_count,
                    "time_window": self.time_window,
                    "threshold": self.max_attempts
                }
            )
        
        return None


class AnomalousBehaviorDetector:
    """Detects anomalous user behavior using statistical analysis"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}
        self.anomaly_threshold = 2.0  # Standard deviations
    
    async def detect(self, event_data: Dict[str, Any]) -> Optional[ThreatEvent]:
        """Detect anomalous behavior"""
        user_id = event_data.get("user_id")
        if not user_id:
            return None
        
        # Load or create user profile
        profile = await self._get_user_profile(user_id)
        
        # Analyze current event for anomalies
        anomalies = []
        
        # IP address anomaly
        current_ip = event_data.get("source_ip")
        if current_ip and current_ip not in profile.typical_ips:
            if len(profile.typical_ips) > 0:  # Only flag if we have historical data
                anomalies.append({
                    "type": "new_ip",
                    "severity": 0.7,
                    "evidence": {"current_ip": current_ip, "typical_ips": list(profile.typical_ips)[:5]}
                })
        
        # Geographic anomaly
        current_country = await self._get_country_from_ip(current_ip)
        if current_country and current_country not in profile.typical_countries:
            if len(profile.typical_countries) > 0:
                anomalies.append({
                    "type": "geographic_anomaly",
                    "severity": 0.8,
                    "evidence": {"current_country": current_country, "typical_countries": list(profile.typical_countries)}
                })
        
        # Time-based anomaly
        current_hour = datetime.utcnow().hour
        if profile.typical_login_hours:
            if current_hour not in profile.typical_login_hours:
                # Calculate how far from typical hours
                min_distance = min(abs(current_hour - h) for h in profile.typical_login_hours)
                if min_distance > 3:  # More than 3 hours from typical
                    anomalies.append({
                        "type": "time_anomaly",
                        "severity": min(min_distance / 12, 1.0),  # Normalize to 0-1
                        "evidence": {"current_hour": current_hour, "typical_hours": profile.typical_login_hours}
                    })
        
        # User agent anomaly
        current_ua = event_data.get("user_agent")
        if current_ua and current_ua not in profile.typical_user_agents:
            if len(profile.typical_user_agents) > 0:
                anomalies.append({
                    "type": "user_agent_anomaly",
                    "severity": 0.5,
                    "evidence": {"current_ua": current_ua[:100]}  # Truncate for storage
                })
        
        # Update profile with current event
        await self._update_user_profile(profile, event_data)
        
        # Generate threat event if anomalies detected
        if anomalies:
            # Calculate overall risk score
            total_severity = sum(a["severity"] for a in anomalies)
            risk_score = min(total_severity * 3, 10)  # Scale to 0-10
            
            # Determine threat level
            if risk_score >= 8:
                threat_level = ThreatLevel.HIGH
            elif risk_score >= 5:
                threat_level = ThreatLevel.MEDIUM
            else:
                threat_level = ThreatLevel.LOW
            
            event_id = f"ab_{int(time.time())}_{hashlib.md5(user_id.encode()).hexdigest()[:8]}"
            
            return ThreatEvent(
                event_id=event_id,
                threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                threat_level=threat_level,
                detection_method=DetectionMethod.BEHAVIORAL_ANALYSIS,
                timestamp=datetime.utcnow(),
                source_ip=current_ip,
                user_id=user_id,
                user_agent=current_ua,
                risk_score=risk_score,
                confidence=min(len(anomalies) * 0.3, 0.9),
                evidence={"anomalies": anomalies, "anomaly_count": len(anomalies)}
            )
        
        return None
    
    async def _get_user_profile(self, user_id: str) -> UserBehaviorProfile:
        """Get or create user behavior profile"""
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        
        # Try to load from Redis
        profile_data = await self.redis_client.client.get(f"user_profile:{user_id}")
        if profile_data:
            data = json.loads(profile_data)
            profile = UserBehaviorProfile(
                user_id=user_id,
                typical_ips=set(data.get("typical_ips", [])),
                typical_countries=set(data.get("typical_countries", [])),
                typical_user_agents=set(data.get("typical_user_agents", [])),
                typical_login_hours=data.get("typical_login_hours", []),
                typical_endpoints=data.get("typical_endpoints", {}),
                avg_request_rate=data.get("avg_request_rate", 0.0),
                avg_session_duration=data.get("avg_session_duration", 0.0),
                last_updated=datetime.fromisoformat(data.get("last_updated", datetime.utcnow().isoformat())),
                total_requests=data.get("total_requests", 0),
                failed_logins=data.get("failed_logins", 0),
                successful_logins=data.get("successful_logins", 0)
            )
        else:
            profile = UserBehaviorProfile(user_id=user_id)
        
        self.user_profiles[user_id] = profile
        return profile
    
    async def _update_user_profile(self, profile: UserBehaviorProfile, event_data: Dict[str, Any]):
        """Update user behavior profile with new event"""
        profile.total_requests += 1
        profile.last_updated = datetime.utcnow()
        
        # Update IP addresses (keep last 10)
        if event_data.get("source_ip"):
            profile.typical_ips.add(event_data["source_ip"])
            if len(profile.typical_ips) > 10:
                profile.typical_ips.pop()
        
        # Update countries
        if event_data.get("source_ip"):
            country = await self._get_country_from_ip(event_data["source_ip"])
            if country:
                profile.typical_countries.add(country)
        
        # Update user agents (keep last 5)
        if event_data.get("user_agent"):
            profile.typical_user_agents.add(event_data["user_agent"])
            if len(profile.typical_user_agents) > 5:
                profile.typical_user_agents.pop()
        
        # Update login hours
        current_hour = datetime.utcnow().hour
        if current_hour not in profile.typical_login_hours:
            profile.typical_login_hours.append(current_hour)
            # Keep typical hours distribution (last 20 logins)
            if len(profile.typical_login_hours) > 20:
                profile.typical_login_hours.pop(0)
        
        # Update endpoints
        endpoint = event_data.get("endpoint")
        if endpoint:
            profile.typical_endpoints[endpoint] = profile.typical_endpoints.get(endpoint, 0) + 1
        
        # Update login counters
        if event_data.get("event_type") == "auth.login.success":
            profile.successful_logins += 1
        elif event_data.get("event_type") == "auth.login.failure":
            profile.failed_logins += 1
        
        # Save to Redis
        await self._save_user_profile(profile)
    
    async def _save_user_profile(self, profile: UserBehaviorProfile):
        """Save user profile to Redis"""
        profile_data = {
            "typical_ips": list(profile.typical_ips),
            "typical_countries": list(profile.typical_countries),
            "typical_user_agents": list(profile.typical_user_agents),
            "typical_login_hours": profile.typical_login_hours,
            "typical_endpoints": profile.typical_endpoints,
            "avg_request_rate": profile.avg_request_rate,
            "avg_session_duration": profile.avg_session_duration,
            "last_updated": profile.last_updated.isoformat(),
            "total_requests": profile.total_requests,
            "failed_logins": profile.failed_logins,
            "successful_logins": profile.successful_logins
        }
        
        await self.redis_client.client.set(
            f"user_profile:{profile.user_id}",
            json.dumps(profile_data),
            ex=86400 * 30  # Expire after 30 days
        )
    
    async def _get_country_from_ip(self, ip_address: str) -> Optional[str]:
        """Get country from IP address using GeoIP"""
        try:
            # This would require GeoIP database
            # For demo purposes, return None
            return None
        except Exception:
            return None


class SuspiciousIPDetector:
    """Detects suspicious IP addresses using threat intelligence"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client
        self.threat_feeds = []
        self.suspicious_ips: Set[str] = set()
        self.ip_reputation_cache: Dict[str, Tuple[float, datetime]] = {}
    
    async def detect(self, event_data: Dict[str, Any]) -> Optional[ThreatEvent]:
        """Detect suspicious IP addresses"""
        source_ip = event_data.get("source_ip")
        if not source_ip:
            return None
        
        # Check if IP is in our suspicious list
        if source_ip in self.suspicious_ips:
            event_id = f"sip_{int(time.time())}_{hashlib.md5(source_ip.encode()).hexdigest()[:8]}"
            
            return ThreatEvent(
                event_id=event_id,
                threat_type=ThreatType.SUSPICIOUS_IP,
                threat_level=ThreatLevel.HIGH,
                detection_method=DetectionMethod.THREAT_INTELLIGENCE,
                timestamp=datetime.utcnow(),
                source_ip=source_ip,
                user_id=event_data.get("user_id"),
                risk_score=8.0,
                confidence=0.95,
                evidence={"reason": "ip_in_threat_feed"}
            )
        
        # Check IP reputation
        reputation_score = await self._get_ip_reputation(source_ip)
        if reputation_score >= 0.7:  # High risk threshold
            threat_level = ThreatLevel.HIGH if reputation_score >= 0.9 else ThreatLevel.MEDIUM
            
            event_id = f"ipr_{int(time.time())}_{hashlib.md5(source_ip.encode()).hexdigest()[:8]}"
            
            return ThreatEvent(
                event_id=event_id,
                threat_type=ThreatType.SUSPICIOUS_IP,
                threat_level=threat_level,
                detection_method=DetectionMethod.THREAT_INTELLIGENCE,
                timestamp=datetime.utcnow(),
                source_ip=source_ip,
                user_id=event_data.get("user_id"),
                risk_score=reputation_score * 10,
                confidence=0.8,
                evidence={"reputation_score": reputation_score}
            )
        
        return None
    
    async def _get_ip_reputation(self, ip_address: str) -> float:
        """Get IP reputation score (0.0 = clean, 1.0 = malicious)"""
        # Check cache first
        if ip_address in self.ip_reputation_cache:
            score, timestamp = self.ip_reputation_cache[ip_address]
            if datetime.utcnow() - timestamp < timedelta(hours=1):  # Cache for 1 hour
                return score
        
        # Default implementation - in production, integrate with threat intelligence APIs
        score = 0.0
        
        # Simple heuristics
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check if private IP
            if ip.is_private:
                score = 0.0
            # Check if known malicious ranges (example)
            elif str(ip).startswith(("10.0.0.", "192.168.1.")):
                score = 0.0
            else:
                # In production, query threat intelligence feeds
                score = 0.1  # Default low risk for unknown IPs
        
        except ValueError:
            score = 0.5  # Invalid IP format
        
        # Cache result
        self.ip_reputation_cache[ip_address] = (score, datetime.utcnow())
        return score
    
    async def add_suspicious_ip(self, ip_address: str, reason: str):
        """Add IP to suspicious list"""
        self.suspicious_ips.add(ip_address)
        
        # Store in Redis
        await self.redis_client.client.sadd("suspicious_ips", ip_address)
        await self.redis_client.client.hset("suspicious_ip_reasons", ip_address, reason)
    
    async def remove_suspicious_ip(self, ip_address: str):
        """Remove IP from suspicious list"""
        self.suspicious_ips.discard(ip_address)
        
        # Remove from Redis
        await self.redis_client.client.srem("suspicious_ips", ip_address)
        await self.redis_client.client.hdel("suspicious_ip_reasons", ip_address)


class RateLimitAbuseDetector:
    """Detects rate limit abuse patterns"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client
        self.abuse_threshold = 10  # Number of rate limit hits to consider abuse
        self.time_window = 3600   # 1 hour window
    
    async def detect(self, event_data: Dict[str, Any]) -> Optional[ThreatEvent]:
        """Detect rate limit abuse"""
        if event_data.get("event_type") != "security.rate_limit.exceeded":
            return None
        
        source_ip = event_data.get("source_ip")
        user_id = event_data.get("user_id")
        
        if not source_ip:
            return None
        
        # Track rate limit violations
        key = f"rate_limit_abuse:{source_ip}"
        current_time = int(time.time())
        
        await self.redis_client.client.zadd(key, {str(current_time): current_time})
        await self.redis_client.client.expire(key, self.time_window)
        
        # Count violations in time window
        cutoff = current_time - self.time_window
        await self.redis_client.client.zremrangebyscore(key, 0, cutoff)
        violation_count = await self.redis_client.client.zcard(key)
        
        if violation_count >= self.abuse_threshold:
            event_id = f"rla_{int(current_time)}_{hashlib.md5(source_ip.encode()).hexdigest()[:8]}"
            
            return ThreatEvent(
                event_id=event_id,
                threat_type=ThreatType.RATE_LIMIT_ABUSE,
                threat_level=ThreatLevel.MEDIUM,
                detection_method=DetectionMethod.RULE_BASED,
                timestamp=datetime.utcnow(),
                source_ip=source_ip,
                user_id=user_id,
                risk_score=min(violation_count / self.abuse_threshold, 1.0) * 7,
                confidence=0.85,
                evidence={
                    "violation_count": violation_count,
                    "time_window": self.time_window,
                    "threshold": self.abuse_threshold
                }
            )
        
        return None


class MLAnomalyDetector:
    """Machine learning-based anomaly detection"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis_client = redis_client
        self.model = None
        self.scaler = StandardScaler()
        self.feature_window = deque(maxlen=1000)  # Keep last 1000 events for training
        self.is_trained = False
        self.retrain_interval = 3600  # Retrain every hour
        self.last_training = None
    
    async def detect(self, event_data: Dict[str, Any]) -> Optional[ThreatEvent]:
        """Detect anomalies using ML model"""
        features = self._extract_features(event_data)
        if not features:
            return None
        
        # Add to feature window for training
        self.feature_window.append(features)
        
        # Train model if needed
        if not self.is_trained or self._should_retrain():
            await self._train_model()
        
        if not self.model:
            return None
        
        # Predict anomaly
        try:
            features_scaled = self.scaler.transform([features])
            anomaly_score = self.model.decision_function(features_scaled)[0]
            is_anomaly = self.model.predict(features_scaled)[0] == -1
            
            if is_anomaly:
                # Convert anomaly score to risk score (normalize to 0-10)
                risk_score = min(abs(anomaly_score) * 2, 10)  
                
                # Determine threat level based on risk score
                if risk_score >= 8:
                    threat_level = ThreatLevel.HIGH
                elif risk_score >= 5:
                    threat_level = ThreatLevel.MEDIUM
                else:
                    threat_level = ThreatLevel.LOW
                
                event_id = f"ml_{int(time.time())}_{hashlib.md5(str(features).encode()).hexdigest()[:8]}"
                
                return ThreatEvent(
                    event_id=event_id,
                    threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                    threat_level=threat_level,
                    detection_method=DetectionMethod.MACHINE_LEARNING,
                    timestamp=datetime.utcnow(),
                    source_ip=event_data.get("source_ip"),
                    user_id=event_data.get("user_id"),
                    risk_score=risk_score,
                    confidence=0.75,
                    evidence={
                        "anomaly_score": anomaly_score,
                        "features": dict(zip(self._get_feature_names(), features))
                    }
                )
        
        except Exception as e:
            logger.error(f"ML anomaly detection error: {e}")
        
        return None
    
    def _extract_features(self, event_data: Dict[str, Any]) -> Optional[List[float]]:
        """Extract numerical features from event data"""
        try:
            features = []
            
            # Time-based features
            current_time = datetime.utcnow()
            features.append(current_time.hour)  # Hour of day
            features.append(current_time.weekday())  # Day of week
            
            # IP-based features
            source_ip = event_data.get("source_ip", "0.0.0.0")
            try:
                ip = ipaddress.ip_address(source_ip)
                features.append(float(ip.is_private))
                features.append(float(ip.is_loopback))
                features.append(float(ip.is_multicast))
            except ValueError:
                features.extend([0.0, 0.0, 0.0])
            
            # User agent features
            user_agent = event_data.get("user_agent", "")
            if user_agent:
                parsed_ua = parse_user_agent(user_agent)
                features.append(float(parsed_ua.is_mobile))
                features.append(float(parsed_ua.is_bot))
                features.append(len(user_agent))
            else:
                features.extend([0.0, 0.0, 0.0])
            
            # Request features
            features.append(float(event_data.get("event_type") == "auth.login.failure"))
            features.append(float(event_data.get("event_type") == "security.rate_limit.exceeded"))
            features.append(len(event_data.get("endpoint", "")))
            
            return features
        
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return None
    
    def _get_feature_names(self) -> List[str]:
        """Get feature names for interpretation"""
        return [
            "hour_of_day", "day_of_week", "ip_is_private", "ip_is_loopback", 
            "ip_is_multicast", "ua_is_mobile", "ua_is_bot", "ua_length",
            "is_login_failure", "is_rate_limit", "endpoint_length"
        ]
    
    async def _train_model(self):
        """Train the ML model"""
        if len(self.feature_window) < 50:  # Need minimum data
            return
        
        try:
            features_array = np.array(list(self.feature_window))
            
            # Scale features
            self.scaler.fit(features_array)
            features_scaled = self.scaler.transform(features_array)
            
            # Train Isolation Forest for anomaly detection
            self.model = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )
            self.model.fit(features_scaled)
            
            self.is_trained = True
            self.last_training = time.time()
            
            logger.info(f"ML model trained with {len(features_array)} samples")
        
        except Exception as e:
            logger.error(f"ML model training error: {e}")
    
    def _should_retrain(self) -> bool:
        """Check if model should be retrained"""
        if not self.last_training:
            return True
        
        return (time.time() - self.last_training) > self.retrain_interval


class ThreatDetectionEngine:
    """Main threat detection engine coordinating all detectors"""
    
    def __init__(self, redis_client: RedisClient, audit_logger: AuditLogger):
        self.redis_client = redis_client
        self.audit_logger = audit_logger
        
        # Initialize detectors
        self.detectors: List[ThreatDetector] = [
            BruteForceDetector(redis_client),
            AnomalousBehaviorDetector(redis_client),
            SuspiciousIPDetector(redis_client),
            RateLimitAbuseDetector(redis_client),
            MLAnomalyDetector(redis_client)
        ]
        
        # Threat event storage
        self.active_threats: Dict[str, ThreatEvent] = {}
        self.threat_history: deque = deque(maxlen=10000)
        
        # Response handlers
        self.response_handlers: Dict[ThreatType, List[Callable]] = defaultdict(list)
        
        # Statistics
        self.detection_stats = {
            "total_events_processed": 0,
            "threats_detected": 0,
            "false_positives": 0,
            "blocked_threats": 0
        }
    
    async def process_event(self, event_data: Dict[str, Any]) -> List[ThreatEvent]:
        """Process security event through all detectors"""
        self.detection_stats["total_events_processed"] += 1
        detected_threats = []
        
        # Run all detectors
        for detector in self.detectors:
            try:
                threat_event = await detector.detect(event_data)
                if threat_event:
                    detected_threats.append(threat_event)
                    
                    # Store active threat
                    self.active_threats[threat_event.event_id] = threat_event
                    self.threat_history.append(threat_event)
                    
                    # Update statistics
                    self.detection_stats["threats_detected"] += 1
                    
                    # Log threat detection
                    self.audit_logger.log_event(
                        AuditEventType.SECURITY_VIOLATIONS,
                        f"Threat detected: {threat_event.threat_type.value}",
                        severity=self._map_threat_to_audit_severity(threat_event.threat_level),
                        user_id=threat_event.user_id,
                        resource=threat_event.endpoint,
                        details=threat_event.to_dict()
                    )
                    
                    # Store in Redis
                    await self._store_threat_event(threat_event)
                    
                    # Trigger response handlers
                    await self._trigger_response_handlers(threat_event)
            
            except Exception as e:
                logger.error(f"Error in detector {detector.__class__.__name__}: {e}")
        
        return detected_threats
    
    async def get_active_threats(self, 
                               threat_type: Optional[ThreatType] = None,
                               threat_level: Optional[ThreatLevel] = None,
                               source_ip: Optional[str] = None,
                               user_id: Optional[str] = None) -> List[ThreatEvent]:
        """Get active threats with optional filtering"""
        threats = list(self.active_threats.values())
        
        # Apply filters
        if threat_type:
            threats = [t for t in threats if t.threat_type == threat_type]
        
        if threat_level:
            threats = [t for t in threats if t.threat_level == threat_level]
        
        if source_ip:
            threats = [t for t in threats if t.source_ip == source_ip]
        
        if user_id:
            threats = [t for t in threats if t.user_id == user_id]
        
        return threats
    
    async def resolve_threat(self, event_id: str, resolved_by: str, false_positive: bool = False):
        """Mark threat as resolved"""
        if event_id in self.active_threats:
            threat_event = self.active_threats[event_id]
            threat_event.is_resolved = True
            threat_event.false_positive = false_positive
            
            if false_positive:
                self.detection_stats["false_positives"] += 1
            
            # Update in Redis
            await self._store_threat_event(threat_event)
            
            # Remove from active threats
            del self.active_threats[event_id]
            
            # Log resolution
            self.audit_logger.log_event(
                AuditEventType.ADMIN_ACTION,
                f"Threat resolved: {event_id}",
                user_id=resolved_by,
                details={
                    "event_id": event_id,
                    "false_positive": false_positive,
                    "threat_type": threat_event.threat_type.value
                }
            )
    
    async def block_threat(self, event_id: str, blocked_by: str):
        """Block a threat (e.g., block IP, suspend user)"""
        if event_id in self.active_threats:
            threat_event = self.active_threats[event_id]
            threat_event.is_blocked = True
            
            self.detection_stats["blocked_threats"] += 1
            
            # Update in Redis
            await self._store_threat_event(threat_event)
            
            # Log blocking action
            self.audit_logger.log_event(
                AuditEventType.ADMIN_ACTION,
                f"Threat blocked: {event_id}",
                user_id=blocked_by,
                severity=AuditEventSeverity.HIGH,
                details={
                    "event_id": event_id,
                    "threat_type": threat_event.threat_type.value,
                    "source_ip": threat_event.source_ip
                }
            )
    
    def register_response_handler(self, threat_type: ThreatType, handler: Callable):
        """Register response handler for specific threat type"""
        self.response_handlers[threat_type].append(handler)
    
    async def get_threat_statistics(self) -> Dict[str, Any]:
        """Get threat detection statistics"""
        stats = self.detection_stats.copy()
        
        # Add current active threats count
        stats["active_threats"] = len(self.active_threats)
        
        # Add threat type breakdown
        threat_types = defaultdict(int)
        for threat in self.active_threats.values():
            threat_types[threat.threat_type.value] += 1
        stats["active_threats_by_type"] = dict(threat_types)
        
        # Add threat level breakdown
        threat_levels = defaultdict(int)
        for threat in self.active_threats.values():
            threat_levels[threat.threat_level.value] += 1
        stats["active_threats_by_level"] = dict(threat_levels)
        
        return stats
    
    async def _store_threat_event(self, threat_event: ThreatEvent):
        """Store threat event in Redis"""
        try:
            event_data = json.dumps(threat_event.to_dict(), default=str)
            await self.redis_client.client.set(
                f"threat_event:{threat_event.event_id}",
                event_data,
                ex=86400 * 7  # Expire after 7 days
            )
            
            # Add to sorted set for time-based queries
            await self.redis_client.client.zadd(
                "threat_events_timeline",
                {threat_event.event_id: threat_event.timestamp.timestamp()}
            )
        
        except Exception as e:
            logger.error(f"Failed to store threat event: {e}")
    
    async def _trigger_response_handlers(self, threat_event: ThreatEvent):
        """Trigger registered response handlers"""
        handlers = self.response_handlers.get(threat_event.threat_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(threat_event)
                else:
                    handler(threat_event)
            except Exception as e:
                logger.error(f"Response handler error: {e}")
    
    def _map_threat_to_audit_severity(self, threat_level: ThreatLevel) -> AuditEventSeverity:
        """Map threat level to audit severity"""
        mapping = {
            ThreatLevel.LOW: AuditEventSeverity.LOW,
            ThreatLevel.MEDIUM: AuditEventSeverity.MEDIUM,
            ThreatLevel.HIGH: AuditEventSeverity.HIGH,
            ThreatLevel.CRITICAL: AuditEventSeverity.CRITICAL
        }
        return mapping.get(threat_level, AuditEventSeverity.MEDIUM)


# Factory function
async def setup_threat_detection(redis_client: RedisClient, audit_logger: AuditLogger) -> ThreatDetectionEngine:
    """Setup threat detection engine"""
    engine = ThreatDetectionEngine(redis_client, audit_logger)
    
    logger.info("Threat detection engine initialized")
    return engine


# Example response handlers
async def block_suspicious_ip_handler(threat_event: ThreatEvent):
    """Example handler to block suspicious IPs"""
    if threat_event.threat_type == ThreatType.SUSPICIOUS_IP and threat_event.source_ip:
        logger.warning(f"Auto-blocking suspicious IP: {threat_event.source_ip}")
        # Implementation would add IP to firewall blocklist


async def alert_admin_handler(threat_event: ThreatEvent):
    """Example handler to alert administrators"""
    if threat_event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
        logger.critical(f"High-level threat detected: {threat_event.event_id}")
        # Implementation would send email/Slack notification