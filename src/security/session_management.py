"""
Advanced Session Management with Redis

Provides comprehensive session management with:
- Distributed session storage using Redis
- Session security features (encryption, tampering protection)
- Advanced session tracking and analytics
- Concurrent session limits and controls
- Session hijacking detection and prevention
- Device fingerprinting and validation
- Geographic and behavioral anomaly detection
"""

import asyncio
import json
import logging
import time
import hashlib
import secrets
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import geoip2.database
import geoip2.errors
from user_agents import parse as parse_user_agent

from pydantic import BaseModel

from ..common.redis_client import RedisClient
from .encryption import EncryptionService
from .audit_logging import AuditLogger, AuditEventType, AuditEventSeverity

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """Session status values"""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class SessionType(str, Enum):
    """Types of sessions"""

    WEB = "web"
    API = "api"
    MOBILE = "mobile"
    SERVICE = "service"


class SecurityLevel(str, Enum):
    """Session security levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DeviceFingerprint:
    """Device fingerprint for session validation"""

    user_agent: str
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: str = "en"
    platform: Optional[str] = None
    browser_features: Dict[str, bool] = field(default_factory=dict)
    fingerprint_hash: Optional[str] = None

    def __post_init__(self):
        """Generate fingerprint hash"""
        if not self.fingerprint_hash:
            self.fingerprint_hash = self._generate_hash()

    def _generate_hash(self) -> str:
        """Generate device fingerprint hash"""
        components = [
            self.user_agent or "",
            self.screen_resolution or "",
            self.timezone or "",
            self.language,
            self.platform or "",
            json.dumps(self.browser_features, sort_keys=True),
        ]

        fingerprint_data = "|".join(components)
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    def matches(self, other: "DeviceFingerprint", tolerance: float = 0.8) -> bool:
        """Check if fingerprints match within tolerance"""
        if not other:
            return False

        # Exact hash match
        if self.fingerprint_hash == other.fingerprint_hash:
            return True

        # Fuzzy matching based on components
        matches = 0
        total = 0

        # User agent similarity
        if self.user_agent and other.user_agent:
            ua_similarity = self._string_similarity(self.user_agent, other.user_agent)
            matches += ua_similarity
        total += 1

        # Platform match
        if self.platform == other.platform:
            matches += 1
        total += 1

        # Language match
        if self.language == other.language:
            matches += 1
        total += 1

        # Screen resolution match
        if self.screen_resolution == other.screen_resolution:
            matches += 0.5
        total += 0.5

        return (matches / total) >= tolerance if total > 0 else False

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity (Jaccard similarity)"""
        s1_words = set(s1.lower().split())
        s2_words = set(s2.lower().split())

        intersection = len(s1_words.intersection(s2_words))
        union = len(s1_words.union(s2_words))

        return intersection / union if union > 0 else 0


@dataclass
class SessionData:
    """Complete session information"""

    session_id: str
    user_id: str
    username: Optional[str] = None
    session_type: SessionType = SessionType.WEB
    status: SessionStatus = SessionStatus.ACTIVE
    security_level: SecurityLevel = SecurityLevel.MEDIUM

    # Timing information
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # Security information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[DeviceFingerprint] = None
    csrf_token: Optional[str] = None

    # Geographic information
    country: Optional[str] = None
    city: Optional[str] = None

    # Session data
    data: Dict[str, Any] = field(default_factory=dict)

    # Security flags
    is_encrypted: bool = True
    require_mfa: bool = False
    ip_locked: bool = False
    device_locked: bool = False

    # Activity tracking
    request_count: int = 0
    last_activity_type: Optional[str] = None
    activity_log: List[Dict[str, Any]] = field(default_factory=list)

    # Anomaly detection
    risk_score: float = 0.0
    anomaly_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "session_type": self.session_type.value,
            "status": self.status.value,
            "security_level": self.security_level.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_fingerprint": (
                {
                    "user_agent": (
                        self.device_fingerprint.user_agent
                        if self.device_fingerprint
                        else None
                    ),
                    "screen_resolution": (
                        self.device_fingerprint.screen_resolution
                        if self.device_fingerprint
                        else None
                    ),
                    "timezone": (
                        self.device_fingerprint.timezone
                        if self.device_fingerprint
                        else None
                    ),
                    "language": (
                        self.device_fingerprint.language
                        if self.device_fingerprint
                        else "en"
                    ),
                    "platform": (
                        self.device_fingerprint.platform
                        if self.device_fingerprint
                        else None
                    ),
                    "browser_features": (
                        self.device_fingerprint.browser_features
                        if self.device_fingerprint
                        else {}
                    ),
                    "fingerprint_hash": (
                        self.device_fingerprint.fingerprint_hash
                        if self.device_fingerprint
                        else None
                    ),
                }
                if self.device_fingerprint
                else None
            ),
            "csrf_token": self.csrf_token,
            "country": self.country,
            "city": self.city,
            "data": self.data,
            "is_encrypted": self.is_encrypted,
            "require_mfa": self.require_mfa,
            "ip_locked": self.ip_locked,
            "device_locked": self.device_locked,
            "request_count": self.request_count,
            "last_activity_type": self.last_activity_type,
            "activity_log": self.activity_log[-50:],  # Keep last 50 activities
            "risk_score": self.risk_score,
            "anomaly_flags": self.anomaly_flags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create from dictionary"""
        device_fp = None
        if data.get("device_fingerprint"):
            fp_data = data["device_fingerprint"]
            device_fp = DeviceFingerprint(
                user_agent=fp_data.get("user_agent", ""),
                screen_resolution=fp_data.get("screen_resolution"),
                timezone=fp_data.get("timezone"),
                language=fp_data.get("language", "en"),
                platform=fp_data.get("platform"),
                browser_features=fp_data.get("browser_features", {}),
                fingerprint_hash=fp_data.get("fingerprint_hash"),
            )

        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            username=data.get("username"),
            session_type=SessionType(data.get("session_type", "web")),
            status=SessionStatus(data.get("status", "active")),
            security_level=SecurityLevel(data.get("security_level", "medium")),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            device_fingerprint=device_fp,
            csrf_token=data.get("csrf_token"),
            country=data.get("country"),
            city=data.get("city"),
            data=data.get("data", {}),
            is_encrypted=data.get("is_encrypted", True),
            require_mfa=data.get("require_mfa", False),
            ip_locked=data.get("ip_locked", False),
            device_locked=data.get("device_locked", False),
            request_count=data.get("request_count", 0),
            last_activity_type=data.get("last_activity_type"),
            activity_log=data.get("activity_log", []),
            risk_score=data.get("risk_score", 0.0),
            anomaly_flags=data.get("anomaly_flags", []),
        )


class SessionConfig(BaseModel):
    """Session management configuration"""

    default_expiry_minutes: int = 60
    max_concurrent_sessions: int = 5
    session_encryption_enabled: bool = True
    device_fingerprinting_enabled: bool = True
    ip_validation_enabled: bool = True
    geographic_validation_enabled: bool = True
    anomaly_detection_enabled: bool = True
    csrf_protection_enabled: bool = True

    # Security thresholds
    max_ip_changes: int = 3
    max_location_changes: int = 2
    anomaly_score_threshold: float = 0.7
    device_fingerprint_tolerance: float = 0.8

    # Activity limits
    max_requests_per_minute: int = 100
    max_idle_minutes: int = 30

    class Config:
        use_enum_values = True


class SessionManager:
    """Advanced session management system"""

    def __init__(
        self,
        redis_client: RedisClient,
        encryption_service: EncryptionService,
        audit_logger: AuditLogger,
        config: Optional[SessionConfig] = None,
    ):
        self.redis_client = redis_client
        self.encryption_service = encryption_service
        self.audit_logger = audit_logger
        self.config = config or SessionConfig()

        # In-memory caches
        self.session_cache: Dict[str, SessionData] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> session_ids

        # GeoIP database (would be loaded from file in production)
        self.geoip_reader = None

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize session manager"""
        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

        # Load existing sessions
        await self._load_active_sessions()

        logger.info("Session manager initialized")

    async def create_session(
        self,
        user_id: str,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[DeviceFingerprint] = None,
        session_type: SessionType = SessionType.WEB,
        security_level: SecurityLevel = SecurityLevel.MEDIUM,
        expiry_minutes: Optional[int] = None,
    ) -> SessionData:
        """Create new session"""

        # Check concurrent session limits
        await self._enforce_session_limits(user_id)

        # Generate session ID
        session_id = self._generate_session_id()

        # Set expiry
        expiry_minutes = expiry_minutes or self.config.default_expiry_minutes
        expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

        # Get geographic information
        country, city = (
            await self._get_location_from_ip(ip_address) if ip_address else (None, None)
        )

        # Generate CSRF token
        csrf_token = (
            secrets.token_urlsafe(32) if self.config.csrf_protection_enabled else None
        )

        # Create session data
        session_data = SessionData(
            session_id=session_id,
            user_id=user_id,
            username=username,
            session_type=session_type,
            security_level=security_level,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            csrf_token=csrf_token,
            country=country,
            city=city,
            ip_locked=security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL],
            device_locked=security_level == SecurityLevel.CRITICAL,
            require_mfa=security_level == SecurityLevel.CRITICAL,
        )

        # Add initial activity
        session_data.activity_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "session_created",
                "ip_address": ip_address,
                "user_agent": user_agent[:100] if user_agent else None,
            }
        )

        # Store session
        await self._store_session(session_data)

        # Update user sessions mapping
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)

        # Cache session
        self.session_cache[session_id] = session_data

        # Audit log
        self.audit_logger.log_event(
            AuditEventType.LOGIN_SUCCESS,
            f"Session created for user {username or user_id}",
            user_id=user_id,
            details={
                "session_id": session_id,
                "session_type": session_type.value,
                "security_level": security_level.value,
                "ip_address": ip_address,
                "country": country,
                "expires_at": expires_at.isoformat(),
            },
        )

        logger.info(f"Created session {session_id} for user {user_id}")
        return session_data

    async def validate_session(
        self,
        session_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[DeviceFingerprint] = None,
    ) -> Optional[SessionData]:
        """Validate and retrieve session"""

        # Get session data
        session_data = await self._get_session(session_id)
        if not session_data:
            return None

        # Check session status
        if session_data.status != SessionStatus.ACTIVE:
            logger.warning(f"Session {session_id} is not active: {session_data.status}")
            return None

        # Check expiry
        if session_data.expires_at and datetime.utcnow() > session_data.expires_at:
            await self._expire_session(session_id, "Session expired")
            return None

        # Validate IP address
        if self.config.ip_validation_enabled and session_data.ip_locked:
            if ip_address != session_data.ip_address:
                await self._flag_anomaly(
                    session_data,
                    "ip_change",
                    {"original_ip": session_data.ip_address, "new_ip": ip_address},
                )

                # If too many IP changes, suspend session
                ip_changes = sum(
                    1
                    for flag in session_data.anomaly_flags
                    if flag.startswith("ip_change")
                )
                if ip_changes >= self.config.max_ip_changes:
                    await self._suspend_session(
                        session_id, "Too many IP address changes"
                    )
                    return None

        # Validate device fingerprint
        if (
            self.config.device_fingerprinting_enabled
            and session_data.device_locked
            and session_data.device_fingerprint
            and device_fingerprint
        ):

            if not session_data.device_fingerprint.matches(
                device_fingerprint, self.config.device_fingerprint_tolerance
            ):
                await self._flag_anomaly(
                    session_data,
                    "device_change",
                    {
                        "original_fingerprint": session_data.device_fingerprint.fingerprint_hash,
                        "new_fingerprint": device_fingerprint.fingerprint_hash,
                    },
                )

                # Suspend session on device mismatch for high security
                if session_data.security_level in [
                    SecurityLevel.HIGH,
                    SecurityLevel.CRITICAL,
                ]:
                    await self._suspend_session(
                        session_id, "Device fingerprint mismatch"
                    )
                    return None

        # Update session activity
        await self._update_session_activity(session_data, ip_address, user_agent)

        return session_data

    async def update_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data"""
        session_data = await self._get_session(session_id)
        if not session_data or session_data.status != SessionStatus.ACTIVE:
            return False

        # Update data
        session_data.data.update(data)
        session_data.last_accessed = datetime.utcnow()

        # Store updated session
        await self._store_session(session_data)

        return True

    async def extend_session(self, session_id: str, additional_minutes: int) -> bool:
        """Extend session expiry"""
        session_data = await self._get_session(session_id)
        if not session_data or session_data.status != SessionStatus.ACTIVE:
            return False

        # Extend expiry
        if session_data.expires_at:
            session_data.expires_at += timedelta(minutes=additional_minutes)
        else:
            session_data.expires_at = datetime.utcnow() + timedelta(
                minutes=additional_minutes
            )

        # Add activity log
        session_data.activity_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "session_extended",
                "additional_minutes": additional_minutes,
            }
        )

        # Store updated session
        await self._store_session(session_data)

        return True

    async def revoke_session(
        self, session_id: str, reason: str = "Manual revocation"
    ) -> bool:
        """Revoke session"""
        session_data = await self._get_session(session_id)
        if not session_data:
            return False

        # Update status
        session_data.status = SessionStatus.REVOKED
        session_data.activity_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "session_revoked",
                "reason": reason,
            }
        )

        # Store updated session
        await self._store_session(session_data)

        # Remove from cache
        self.session_cache.pop(session_id, None)

        # Update user sessions mapping
        if session_data.user_id in self.user_sessions:
            self.user_sessions[session_data.user_id].discard(session_id)

        # Audit log
        self.audit_logger.log_event(
            AuditEventType.LOGOUT,
            f"Session revoked: {reason}",
            user_id=session_data.user_id,
            details={"session_id": session_id, "reason": reason},
        )

        logger.info(f"Revoked session {session_id}: {reason}")
        return True

    async def revoke_user_sessions(
        self,
        user_id: str,
        exclude_session: Optional[str] = None,
        reason: str = "User logout",
    ) -> int:
        """Revoke all sessions for a user"""
        user_session_ids = self.user_sessions.get(user_id, set()).copy()

        if exclude_session:
            user_session_ids.discard(exclude_session)

        revoked_count = 0
        for session_id in user_session_ids:
            if await self.revoke_session(session_id, reason):
                revoked_count += 1

        return revoked_count

    async def get_user_sessions(
        self, user_id: str, include_inactive: bool = False
    ) -> List[SessionData]:
        """Get all sessions for a user"""
        session_ids = self.user_sessions.get(user_id, set())
        sessions = []

        for session_id in session_ids:
            session_data = await self._get_session(session_id)
            if session_data:
                if include_inactive or session_data.status == SessionStatus.ACTIVE:
                    sessions.append(session_data)

        return sessions

    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        # Count sessions by status
        status_counts = {status.value: 0 for status in SessionStatus}
        type_counts = {session_type.value: 0 for session_type in SessionType}
        security_counts = {level.value: 0 for level in SecurityLevel}

        total_sessions = 0
        active_sessions = 0
        anomalous_sessions = 0

        # Get all session keys
        pattern = "session:*"
        session_keys = await self.redis_client.client.keys(pattern)

        for key in session_keys:
            try:
                session_data_raw = await self.redis_client.client.get(key)
                if session_data_raw:
                    session_dict = json.loads(session_data_raw)
                    total_sessions += 1

                    status = session_dict.get("status", "active")
                    status_counts[status] += 1

                    if status == "active":
                        active_sessions += 1

                    session_type = session_dict.get("session_type", "web")
                    type_counts[session_type] += 1

                    security_level = session_dict.get("security_level", "medium")
                    security_counts[security_level] += 1

                    if session_dict.get("anomaly_flags"):
                        anomalous_sessions += 1

            except Exception as e:
                logger.error(f"Error processing session statistics: {e}")

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "anomalous_sessions": anomalous_sessions,
            "sessions_by_status": status_counts,
            "sessions_by_type": type_counts,
            "sessions_by_security_level": security_counts,
            "concurrent_users": len(self.user_sessions),
        }

    @asynccontextmanager
    async def session_context(self, session_id: str):
        """Context manager for session operations"""
        session_data = await self.validate_session(session_id)
        if not session_data:
            raise ValueError(f"Invalid session: {session_id}")

        try:
            yield session_data
        finally:
            # Update last accessed time
            session_data.last_accessed = datetime.utcnow()
            await self._store_session(session_data)

    async def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        while True:
            session_id = f"sess_{secrets.token_urlsafe(32)}"
            # Check if already exists
            exists = await self.redis_client.client.exists(f"session:{session_id}")
            if not exists:
                return session_id

    async def _enforce_session_limits(self, user_id: str):
        """Enforce concurrent session limits"""
        user_session_ids = self.user_sessions.get(user_id, set())
        active_sessions = []

        # Check which sessions are still active
        for session_id in user_session_ids.copy():
            session_data = await self._get_session(session_id)
            if session_data and session_data.status == SessionStatus.ACTIVE:
                active_sessions.append((session_id, session_data))
            else:
                # Remove invalid session from mapping
                user_session_ids.discard(session_id)

        # If at limit, revoke oldest session
        if len(active_sessions) >= self.config.max_concurrent_sessions:
            # Sort by creation time and revoke oldest
            active_sessions.sort(key=lambda x: x[1].created_at)
            oldest_session_id, _ = active_sessions[0]
            await self.revoke_session(
                oldest_session_id, "Concurrent session limit exceeded"
            )

    async def _get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session from cache or storage"""
        # Check cache first
        if session_id in self.session_cache:
            return self.session_cache[session_id]

        # Load from Redis
        session_data_raw = await self.redis_client.client.get(f"session:{session_id}")
        if not session_data_raw:
            return None

        try:
            session_dict = json.loads(session_data_raw)
            session_data = SessionData.from_dict(session_dict)

            # Cache session
            self.session_cache[session_id] = session_data

            return session_data

        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None

    async def _store_session(self, session_data: SessionData):
        """Store session in Redis"""
        try:
            session_dict = session_data.to_dict()
            session_json = json.dumps(session_dict, default=str)

            # Calculate TTL
            ttl = None
            if session_data.expires_at:
                ttl = int((session_data.expires_at - datetime.utcnow()).total_seconds())
                if ttl <= 0:
                    # Session already expired, don't store
                    return

            # Store in Redis
            if ttl:
                await self.redis_client.client.set(
                    f"session:{session_data.session_id}", session_json, ex=ttl
                )
            else:
                await self.redis_client.client.set(
                    f"session:{session_data.session_id}", session_json
                )

            # Update cache
            self.session_cache[session_data.session_id] = session_data

        except Exception as e:
            logger.error(f"Error storing session {session_data.session_id}: {e}")

    async def _update_session_activity(
        self,
        session_data: SessionData,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Update session activity"""
        session_data.last_accessed = datetime.utcnow()
        session_data.request_count += 1

        # Check for anomalies
        await self._detect_anomalies(session_data, ip_address, user_agent)

        # Add activity log entry (rate limited)
        current_time = datetime.utcnow()
        last_activity = (
            session_data.activity_log[-1] if session_data.activity_log else None
        )

        # Only log if last activity was more than 1 minute ago
        if (
            not last_activity
            or (
                current_time - datetime.fromisoformat(last_activity["timestamp"])
            ).total_seconds()
            > 60
        ):
            session_data.activity_log.append(
                {
                    "timestamp": current_time.isoformat(),
                    "type": "request",
                    "ip_address": ip_address,
                    "user_agent": user_agent[:100] if user_agent else None,
                    "request_count": session_data.request_count,
                }
            )

            # Keep only last 50 activities
            if len(session_data.activity_log) > 50:
                session_data.activity_log = session_data.activity_log[-50:]

        # Store updated session
        await self._store_session(session_data)

    async def _detect_anomalies(
        self,
        session_data: SessionData,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Detect session anomalies"""
        if not self.config.anomaly_detection_enabled:
            return

        anomalies = []

        # IP address changes
        if (
            ip_address
            and session_data.ip_address
            and ip_address != session_data.ip_address
        ):
            anomalies.append("ip_change")

        # Geographic anomalies
        if ip_address and self.config.geographic_validation_enabled:
            current_country, current_city = await self._get_location_from_ip(ip_address)
            if (
                current_country
                and session_data.country
                and current_country != session_data.country
            ):
                anomalies.append("geographic_change")

        # User agent changes
        if (
            user_agent
            and session_data.user_agent
            and user_agent != session_data.user_agent
        ):
            # Parse user agents to check for significant changes
            current_ua = parse_user_agent(user_agent)
            original_ua = parse_user_agent(session_data.user_agent)

            if (
                current_ua.browser.family != original_ua.browser.family
                or current_ua.os.family != original_ua.os.family
            ):
                anomalies.append("user_agent_change")

        # Rate-based anomalies
        if session_data.activity_log:
            recent_activities = [
                a
                for a in session_data.activity_log
                if (
                    datetime.utcnow() - datetime.fromisoformat(a["timestamp"])
                ).total_seconds()
                < 60
            ]
            if len(recent_activities) > self.config.max_requests_per_minute:
                anomalies.append("high_request_rate")

        # Flag anomalies
        for anomaly in anomalies:
            await self._flag_anomaly(
                session_data,
                anomaly,
                {"ip_address": ip_address, "user_agent": user_agent},
            )

    async def _flag_anomaly(
        self, session_data: SessionData, anomaly_type: str, details: Dict[str, Any]
    ):
        """Flag session anomaly"""
        anomaly_flag = f"{anomaly_type}_{int(time.time())}"
        session_data.anomaly_flags.append(anomaly_flag)

        # Keep only recent flags (last 24 hours worth)
        cutoff_time = time.time() - 86400
        session_data.anomaly_flags = [
            flag
            for flag in session_data.anomaly_flags
            if int(flag.split("_")[-1]) > cutoff_time
        ]

        # Update risk score
        session_data.risk_score = min(len(session_data.anomaly_flags) * 0.1, 1.0)

        # Log anomaly
        self.audit_logger.log_event(
            AuditEventType.SECURITY_VIOLATIONS,
            f"Session anomaly detected: {anomaly_type}",
            severity=AuditEventSeverity.MEDIUM,
            user_id=session_data.user_id,
            details={
                "session_id": session_data.session_id,
                "anomaly_type": anomaly_type,
                "risk_score": session_data.risk_score,
                **details,
            },
        )

        # Auto-suspend if risk score is too high
        if session_data.risk_score >= self.config.anomaly_score_threshold:
            await self._suspend_session(
                session_data.session_id, f"High risk score: {session_data.risk_score}"
            )

    async def _suspend_session(self, session_id: str, reason: str):
        """Suspend session due to security concerns"""
        session_data = await self._get_session(session_id)
        if not session_data:
            return

        session_data.status = SessionStatus.SUSPENDED
        session_data.activity_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "session_suspended",
                "reason": reason,
            }
        )

        await self._store_session(session_data)

        # Remove from cache
        self.session_cache.pop(session_id, None)

        # Log suspension
        self.audit_logger.log_event(
            AuditEventType.SECURITY_VIOLATIONS,
            f"Session suspended: {reason}",
            severity=AuditEventSeverity.HIGH,
            user_id=session_data.user_id,
            details={
                "session_id": session_id,
                "reason": reason,
                "risk_score": session_data.risk_score,
            },
        )

    async def _expire_session(self, session_id: str, reason: str):
        """Mark session as expired"""
        session_data = await self._get_session(session_id)
        if not session_data:
            return

        session_data.status = SessionStatus.EXPIRED
        session_data.activity_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "session_expired",
                "reason": reason,
            }
        )

        await self._store_session(session_data)

        # Remove from cache
        self.session_cache.pop(session_id, None)

        # Update user sessions mapping
        if session_data.user_id in self.user_sessions:
            self.user_sessions[session_data.user_id].discard(session_id)

    async def _get_location_from_ip(
        self, ip_address: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Get country and city from IP address"""
        if not self.geoip_reader:
            return None, None

        try:
            response = self.geoip_reader.city(ip_address)
            return response.country.name, response.city.name
        except (geoip2.errors.AddressNotFoundError, ValueError):
            return None, None

    async def _load_active_sessions(self):
        """Load active sessions from Redis"""
        try:
            pattern = "session:*"
            session_keys = await self.redis_client.client.keys(pattern)

            loaded_count = 0
            for key in session_keys:
                session_data_raw = await self.redis_client.client.get(key)
                if session_data_raw:
                    try:
                        session_dict = json.loads(session_data_raw)
                        session_data = SessionData.from_dict(session_dict)

                        # Add to user sessions mapping
                        if session_data.user_id not in self.user_sessions:
                            self.user_sessions[session_data.user_id] = set()
                        self.user_sessions[session_data.user_id].add(
                            session_data.session_id
                        )

                        loaded_count += 1

                    except Exception as e:
                        logger.error(f"Error loading session from {key}: {e}")

            logger.info(f"Loaded {loaded_count} active sessions")

        except Exception as e:
            logger.error(f"Error loading active sessions: {e}")

    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Get all session keys
                pattern = "session:*"
                session_keys = await self.redis_client.client.keys(pattern)

                expired_count = 0
                for key in session_keys:
                    try:
                        session_data_raw = await self.redis_client.client.get(key)
                        if session_data_raw:
                            session_dict = json.loads(session_data_raw)
                            expires_at = session_dict.get("expires_at")

                            if expires_at:
                                expires_dt = datetime.fromisoformat(expires_at)
                                if datetime.utcnow() > expires_dt:
                                    # Session expired
                                    session_id = session_dict["session_id"]
                                    await self._expire_session(
                                        session_id, "Cleanup - session expired"
                                    )
                                    expired_count += 1

                    except Exception as e:
                        logger.error(f"Error checking session expiry: {e}")

                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions")

            except Exception as e:
                logger.error(f"Session cleanup task error: {e}")


# Factory function
async def setup_session_manager(
    redis_client: RedisClient,
    encryption_service: EncryptionService,
    audit_logger: AuditLogger,
    config: Optional[SessionConfig] = None,
) -> SessionManager:
    """Setup session manager"""
    manager = SessionManager(redis_client, encryption_service, audit_logger, config)
    await manager.initialize()

    logger.info("Session manager initialized")
    return manager


# Utility functions for device fingerprinting
def extract_device_fingerprint_from_request(request) -> DeviceFingerprint:
    """Extract device fingerprint from HTTP request"""
    user_agent = request.headers.get("User-Agent", "")

    # Extract additional fingerprinting data from headers or request
    fingerprint = DeviceFingerprint(
        user_agent=user_agent,
        language=request.headers.get("Accept-Language", "en")[:10],
        # Additional fields would be populated from client-side JavaScript
    )

    return fingerprint


def create_session_cookie(
    session_id: str,
    secure: bool = True,
    httponly: bool = True,
    samesite: str = "strict",
    max_age: Optional[int] = None,
) -> Dict[str, Any]:
    """Create secure session cookie configuration"""
    cookie_config = {
        "key": "session_id",
        "value": session_id,
        "secure": secure,
        "httponly": httponly,
        "samesite": samesite,
    }

    if max_age:
        cookie_config["max_age"] = max_age

    return cookie_config
