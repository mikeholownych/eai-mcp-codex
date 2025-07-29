"""
End-to-End Encryption System

Provides comprehensive encryption services for sensitive data including:
- Field-level encryption for database storage
- Transport layer encryption for API communications
- Key management and rotation
- Performance-optimized encryption/decryption
- Support for multiple encryption algorithms
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, Union, List, Tuple, Protocol
from datetime import datetime, timedelta
from enum import Enum
import secrets
import hashlib
import base64
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.exceptions import InvalidSignature
import nacl.secret
import nacl.public
import nacl.utils
from nacl.exceptions import InvalidMessage

from pydantic import BaseModel, Field, SecretStr, validator
from ..common.redis_client import RedisClient

logger = logging.getLogger(__name__)


class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms"""
    FERNET = "fernet"  # Symmetric, built-in key rotation
    AES_GCM = "aes_gcm"  # Symmetric, authenticated encryption
    CHACHA20_POLY1305 = "chacha20_poly1305"  # Symmetric, fast and secure
    RSA_OAEP = "rsa_oaep"  # Asymmetric, for key exchange
    NACL_SECRETBOX = "nacl_secretbox"  # High-level symmetric encryption
    NACL_BOX = "nacl_box"  # High-level asymmetric encryption


class KeyType(str, Enum):
    """Types of encryption keys"""
    MASTER = "master"
    DATA = "data"
    TRANSPORT = "transport"
    FIELD = "field"
    SESSION = "session"


@dataclass
class EncryptionKey:
    """Encryption key metadata and material"""
    key_id: str
    key_type: KeyType
    algorithm: EncryptionAlgorithm
    key_material: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    rotation_count: int = 0
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if key is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def needs_rotation(self, rotation_days: int = 90) -> bool:
        """Check if key needs rotation"""
        if self.expires_at:
            return self.is_expired()
        
        age = datetime.utcnow() - self.created_at
        return age.days >= rotation_days


class EncryptionConfig(BaseModel):
    """Encryption system configuration"""
    default_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET
    key_rotation_days: int = 90
    key_backup_enabled: bool = True
    performance_cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    
    # Algorithm-specific settings
    fernet_key_generations: int = 3  # For key rotation
    aes_key_size: int = 256  # 128, 192, or 256 bits
    rsa_key_size: int = 2048  # 2048, 3072, or 4096 bits
    
    # Security settings
    secure_delete_enabled: bool = True
    key_derivation_iterations: int = 100000
    memory_protection_enabled: bool = True
    
    class Config:
        use_enum_values = True


class EncryptionProvider(Protocol):
    """Protocol for encryption providers"""
    async def encrypt(self, data: bytes, key: EncryptionKey, context: Optional[Dict[str, Any]] = None) -> bytes:
        ...
    
    async def decrypt(self, encrypted_data: bytes, key: EncryptionKey, context: Optional[Dict[str, Any]] = None) -> bytes:
        ...
    
    async def generate_key(self, key_type: KeyType) -> EncryptionKey:
        ...


class FernetProvider:
    """Fernet encryption provider with key rotation support"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self._fernet_cache: Dict[str, MultiFernet] = {}
    
    async def encrypt(self, data: bytes, key: EncryptionKey, context: Optional[Dict[str, Any]] = None) -> bytes:
        """Encrypt data using Fernet"""
        try:
            fernet = self._get_fernet(key)
            return fernet.encrypt(data)
        except Exception as e:
            logger.error(f"Fernet encryption failed: {e}")
            raise
    
    async def decrypt(self, encrypted_data: bytes, key: EncryptionKey, context: Optional[Dict[str, Any]] = None) -> bytes:
        """Decrypt data using Fernet"""
        try:
            fernet = self._get_fernet(key)
            return fernet.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Fernet decryption failed: {e}")
            raise
    
    async def generate_key(self, key_type: KeyType) -> EncryptionKey:
        """Generate new Fernet key"""
        key_material = Fernet.generate_key()
        key_id = self._generate_key_id()
        
        return EncryptionKey(
            key_id=key_id,
            key_type=key_type,
            algorithm=EncryptionAlgorithm.FERNET,
            key_material=key_material,
            created_at=datetime.utcnow()
        )
    
    def _get_fernet(self, key: EncryptionKey) -> MultiFernet:
        """Get or create MultiFernet instance with key rotation support"""
        if key.key_id in self._fernet_cache:
            return self._fernet_cache[key.key_id]
        
        # Support multiple key generations for rotation
        keys = [Fernet(key.key_material)]
        
        # Add older generations if available
        for i in range(1, self.config.fernet_key_generations):
            old_key_material = key.metadata.get(f"generation_{i}")
            if old_key_material:
                keys.append(Fernet(base64.b64decode(old_key_material)))
        
        fernet = MultiFernet(keys)
        self._fernet_cache[key.key_id] = fernet
        return fernet
    
    def _generate_key_id(self) -> str:
        """Generate unique key ID"""
        return f"fernet_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(8)}"


class AESGCMProvider:
    """AES-GCM encryption provider"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
    
    async def encrypt(self, data: bytes, key: EncryptionKey, context: Optional[Dict[str, Any]] = None) -> bytes:
        """Encrypt data using AES-GCM"""
        try:
            # Generate random nonce
            nonce = os.urandom(12)  # 96-bit nonce for GCM
            
            # Additional authenticated data (AAD)
            aad = self._build_aad(context) if context else b""
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key.key_material),
                modes.GCM(nonce)
            )
            encryptor = cipher.encryptor()
            
            if aad:
                encryptor.authenticate_additional_data(aad)
            
            # Encrypt
            ciphertext = encryptor.update(data) + encryptor.finalize()
            
            # Return nonce + tag + ciphertext
            return nonce + encryptor.tag + ciphertext
            
        except Exception as e:
            logger.error(f"AES-GCM encryption failed: {e}")
            raise
    
    async def decrypt(self, encrypted_data: bytes, key: EncryptionKey, context: Optional[Dict[str, Any]] = None) -> bytes:
        """Decrypt data using AES-GCM"""
        try:
            # Extract components
            nonce = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]
            
            # Additional authenticated data (AAD)
            aad = self._build_aad(context) if context else b""
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key.key_material),
                modes.GCM(nonce, tag)
            )
            decryptor = cipher.decryptor()
            
            if aad:
                decryptor.authenticate_additional_data(aad)
            
            # Decrypt
            return decryptor.update(ciphertext) + decryptor.finalize()
            
        except Exception as e:
            logger.error(f"AES-GCM decryption failed: {e}")
            raise
    
    async def generate_key(self, key_type: KeyType) -> EncryptionKey:
        """Generate new AES key"""
        key_size = self.config.aes_key_size // 8  # Convert bits to bytes
        key_material = os.urandom(key_size)
        key_id = self._generate_key_id()
        
        return EncryptionKey(
            key_id=key_id,
            key_type=key_type,
            algorithm=EncryptionAlgorithm.AES_GCM,
            key_material=key_material,
            created_at=datetime.utcnow()
        )
    
    def _build_aad(self, context: Dict[str, Any]) -> bytes:
        """Build Additional Authenticated Data from context"""
        # Sort context keys for consistency
        sorted_context = {k: context[k] for k in sorted(context.keys())}
        return json.dumps(sorted_context, sort_keys=True).encode()
    
    def _generate_key_id(self) -> str:
        """Generate unique key ID"""
        return f"aes_gcm_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(8)}"


class NaClProvider:
    """NaCl (libsodium) encryption provider"""
    
    def __init__(self, config: EncryptionConfig):
        self.config = config
    
    async def encrypt(self, data: bytes, key: EncryptionKey, context: Optional[Dict[str, Any]] = None) -> bytes:
        """Encrypt data using NaCl SecretBox"""
        try:
            box = nacl.secret.SecretBox(key.key_material)
            return box.encrypt(data)
        except Exception as e:
            logger.error(f"NaCl encryption failed: {e}")
            raise
    
    async def decrypt(self, encrypted_data: bytes, key: EncryptionKey, context: Optional[Dict[str, Any]] = None) -> bytes:
        """Decrypt data using NaCl SecretBox"""
        try:
            box = nacl.secret.SecretBox(key.key_material)
            return box.decrypt(encrypted_data)
        except InvalidMessage as e:
            logger.error(f"NaCl decryption failed: {e}")
            raise
    
    async def generate_key(self, key_type: KeyType) -> EncryptionKey:
        """Generate new NaCl key"""
        key_material = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
        key_id = self._generate_key_id()
        
        return EncryptionKey(
            key_id=key_id,
            key_type=key_type,
            algorithm=EncryptionAlgorithm.NACL_SECRETBOX,
            key_material=key_material,
            created_at=datetime.utcnow()
        )
    
    def _generate_key_id(self) -> str:
        """Generate unique key ID"""
        return f"nacl_{int(datetime.utcnow().timestamp())}_{secrets.token_hex(8)}"


class KeyManager:
    """Manages encryption keys with rotation and storage"""
    
    def __init__(self, config: EncryptionConfig, redis_client: Optional[RedisClient] = None):
        self.config = config
        self.redis_client = redis_client
        self.keys: Dict[str, EncryptionKey] = {}
        self.key_cache: Dict[str, EncryptionKey] = {}
        self._master_key: Optional[bytes] = None
        
        # Initialize providers
        self.providers = {
            EncryptionAlgorithm.FERNET: FernetProvider(config),
            EncryptionAlgorithm.AES_GCM: AESGCMProvider(config),
            EncryptionAlgorithm.NACL_SECRETBOX: NaClProvider(config)
        }
    
    async def initialize(self):
        """Initialize key manager"""
        try:
            # Load or generate master key
            await self._load_master_key()
            
            # Load existing keys
            await self._load_keys()
            
            # Start key rotation task
            asyncio.create_task(self._key_rotation_task())
            
            logger.info("Key manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize key manager: {e}")
            raise
    
    async def generate_key(self, key_type: KeyType, algorithm: Optional[EncryptionAlgorithm] = None) -> EncryptionKey:
        """Generate new encryption key"""
        if not algorithm:
            algorithm = self.config.default_algorithm
        
        provider = self.providers.get(algorithm)
        if not provider:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        key = await provider.generate_key(key_type)
        
        # Set expiration if configured
        if self.config.key_rotation_days > 0:
            key.expires_at = key.created_at + timedelta(days=self.config.key_rotation_days)
        
        # Store key
        await self._store_key(key)
        
        logger.info(f"Generated new {algorithm} key: {key.key_id}")
        return key
    
    async def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get encryption key by ID"""
        # Check cache first
        if key_id in self.key_cache:
            key = self.key_cache[key_id]
            if not key.is_expired():
                return key
            else:
                # Remove expired key from cache
                del self.key_cache[key_id]
        
        # Load from storage
        key = await self._load_key(key_id)
        if key and not key.is_expired():
            self.key_cache[key_id] = key
        
        return key
    
    async def rotate_key(self, key_id: str) -> EncryptionKey:
        """Rotate encryption key"""
        old_key = await self.get_key(key_id)
        if not old_key:
            raise ValueError(f"Key not found: {key_id}")
        
        # Generate new key material
        provider = self.providers[old_key.algorithm]
        new_key = await provider.generate_key(old_key.key_type)
        
        # Preserve metadata and increment rotation count
        new_key.key_id = old_key.key_id  # Keep same ID
        new_key.rotation_count = old_key.rotation_count + 1
        new_key.metadata = old_key.metadata.copy()
        
        # Store old key material for decryption of existing data
        new_key.metadata[f"generation_{old_key.rotation_count}"] = base64.b64encode(old_key.key_material).decode()
        
        # Store rotated key
        await self._store_key(new_key)
        
        logger.info(f"Rotated key {key_id} (generation {new_key.rotation_count})")
        return new_key
    
    async def list_keys(self, key_type: Optional[KeyType] = None, include_inactive: bool = False) -> List[EncryptionKey]:
        """List encryption keys"""
        keys = []
        
        if self.redis_client:
            # Load from Redis
            pattern = f"encryption_key:*"
            key_ids = await self.redis_client.client.keys(pattern)
            
            for key_id_bytes in key_ids:
                key_id = key_id_bytes.decode().replace("encryption_key:", "")
                key = await self.get_key(key_id)
                if key:
                    if key_type and key.key_type != key_type:
                        continue
                    if not include_inactive and not key.is_active:
                        continue
                    keys.append(key)
        else:
            # Use in-memory storage
            for key in self.keys.values():
                if key_type and key.key_type != key_type:
                    continue
                if not include_inactive and not key.is_active:
                    continue
                keys.append(key)
        
        return keys
    
    async def _load_master_key(self):
        """Load or generate master key"""
        master_key_env = os.getenv("ENCRYPTION_MASTER_KEY")
        if master_key_env:
            self._master_key = base64.b64decode(master_key_env)
        else:
            # Generate new master key
            self._master_key = os.urandom(32)
            logger.warning("Generated new master key. Store ENCRYPTION_MASTER_KEY environment variable.")
    
    async def _load_keys(self):
        """Load existing keys from storage"""
        if not self.redis_client:
            return
        
        try:
            pattern = "encryption_key:*"
            key_ids = await self.redis_client.client.keys(pattern)
            
            for key_id_bytes in key_ids:
                key_id = key_id_bytes.decode().replace("encryption_key:", "")
                await self._load_key(key_id)
            
            logger.info(f"Loaded {len(key_ids)} encryption keys")
            
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
    
    async def _load_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Load single key from storage"""
        try:
            if self.redis_client:
                key_data = await self.redis_client.client.get(f"encryption_key:{key_id}")
                if key_data:
                    # Decrypt key data with master key
                    decrypted_data = self._decrypt_with_master_key(key_data)
                    key_dict = json.loads(decrypted_data)
                    
                    return EncryptionKey(
                        key_id=key_dict["key_id"],
                        key_type=KeyType(key_dict["key_type"]),
                        algorithm=EncryptionAlgorithm(key_dict["algorithm"]),
                        key_material=base64.b64decode(key_dict["key_material"]),
                        created_at=datetime.fromisoformat(key_dict["created_at"]),
                        expires_at=datetime.fromisoformat(key_dict["expires_at"]) if key_dict.get("expires_at") else None,
                        rotation_count=key_dict.get("rotation_count", 0),
                        is_active=key_dict.get("is_active", True),
                        metadata=key_dict.get("metadata", {})
                    )
            else:
                return self.keys.get(key_id)
        
        except Exception as e:
            logger.error(f"Failed to load key {key_id}: {e}")
        
        return None
    
    async def _store_key(self, key: EncryptionKey):
        """Store key in storage"""
        try:
            # Prepare key data for storage
            key_dict = {
                "key_id": key.key_id,
                "key_type": key.key_type.value,
                "algorithm": key.algorithm.value,
                "key_material": base64.b64encode(key.key_material).decode(),
                "created_at": key.created_at.isoformat(),
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "rotation_count": key.rotation_count,
                "is_active": key.is_active,
                "metadata": key.metadata
            }
            
            if self.redis_client:
                # Encrypt key data with master key
                encrypted_data = self._encrypt_with_master_key(json.dumps(key_dict).encode())
                await self.redis_client.client.set(f"encryption_key:{key.key_id}", encrypted_data)
                
                if key.expires_at:
                    # Set TTL in Redis
                    ttl = int((key.expires_at - datetime.utcnow()).total_seconds())
                    await self.redis_client.client.expire(f"encryption_key:{key.key_id}", ttl)
            else:
                # Store in memory
                self.keys[key.key_id] = key
            
            # Update cache
            self.key_cache[key.key_id] = key
            
        except Exception as e:
            logger.error(f"Failed to store key {key.key_id}: {e}")
            raise
    
    def _encrypt_with_master_key(self, data: bytes) -> bytes:
        """Encrypt data with master key"""
        if not self._master_key:
            raise ValueError("Master key not available")
        
        fernet = Fernet(base64.urlsafe_b64encode(self._master_key))
        return fernet.encrypt(data)
    
    def _decrypt_with_master_key(self, encrypted_data: bytes) -> bytes:
        """Decrypt data with master key"""
        if not self._master_key:
            raise ValueError("Master key not available")
        
        fernet = Fernet(base64.urlsafe_b64encode(self._master_key))
        return fernet.decrypt(encrypted_data)
    
    async def _key_rotation_task(self):
        """Background task for automatic key rotation"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                keys = await self.list_keys(include_inactive=False)
                for key in keys:
                    if key.needs_rotation(self.config.key_rotation_days):
                        logger.info(f"Auto-rotating key {key.key_id}")
                        await self.rotate_key(key.key_id)
                
            except Exception as e:
                logger.error(f"Key rotation task error: {e}")


class EncryptionService:
    """Main encryption service providing high-level encryption operations"""
    
    def __init__(self, config: EncryptionConfig, key_manager: KeyManager):
        self.config = config
        self.key_manager = key_manager
        self.providers = key_manager.providers
        
        # Performance cache
        self._cache: Dict[str, Tuple[bytes, datetime]] = {}
    
    async def encrypt_field(self, data: Union[str, bytes], field_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Encrypt sensitive field data"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Get or create field-specific key
        key_id = f"field_{hashlib.sha256(field_name.encode()).hexdigest()[:16]}"
        key = await self.key_manager.get_key(key_id)
        
        if not key:
            key = await self.key_manager.generate_key(KeyType.FIELD)
            key.key_id = key_id
            await self.key_manager._store_key(key)
        
        # Encrypt data
        provider = self.providers[key.algorithm]
        encrypted_data = await provider.encrypt(data, key, context)
        
        # Return base64-encoded result with key ID prefix
        return f"{key.key_id}:{base64.b64encode(encrypted_data).decode()}"
    
    async def decrypt_field(self, encrypted_data: str, context: Optional[Dict[str, Any]] = None) -> bytes:
        """Decrypt sensitive field data"""
        # Parse key ID and encrypted data
        if ':' not in encrypted_data:
            raise ValueError("Invalid encrypted field format")
        
        key_id, encoded_data = encrypted_data.split(':', 1)
        data = base64.b64decode(encoded_data)
        
        # Get key
        key = await self.key_manager.get_key(key_id)
        if not key:
            raise ValueError(f"Encryption key not found: {key_id}")
        
        # Decrypt data
        provider = self.providers[key.algorithm]
        return await provider.decrypt(data, key, context)
    
    async def encrypt_payload(self, payload: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
        """Encrypt specific fields in a payload"""
        encrypted_payload = payload.copy()
        
        for field_path in sensitive_fields:
            # Support nested field paths like "user.email"
            parts = field_path.split('.')
            current = encrypted_payload
            
            # Navigate to parent
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    break
                current = current[part]
            else:
                # Encrypt final field
                field_name = parts[-1]
                if field_name in current:
                    original_value = current[field_name]
                    if original_value:  # Only encrypt non-empty values
                        encrypted_value = await self.encrypt_field(str(original_value), field_path)
                        current[field_name] = encrypted_value
        
        return encrypted_payload
    
    async def decrypt_payload(self, encrypted_payload: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
        """Decrypt specific fields in a payload"""
        decrypted_payload = encrypted_payload.copy()
        
        for field_path in sensitive_fields:
            parts = field_path.split('.')
            current = decrypted_payload
            
            # Navigate to parent
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    break
                current = current[part]
            else:
                # Decrypt final field
                field_name = parts[-1]
                if field_name in current:
                    encrypted_value = current[field_name]
                    if encrypted_value and isinstance(encrypted_value, str) and ':' in encrypted_value:
                        try:
                            decrypted_bytes = await self.decrypt_field(encrypted_value)
                            current[field_name] = decrypted_bytes.decode('utf-8')
                        except Exception as e:
                            logger.warning(f"Failed to decrypt field {field_path}: {e}")
        
        return decrypted_payload
    
    @asynccontextmanager
    async def encrypted_session(self, session_id: str):
        """Context manager for encrypted session data"""
        session_key = await self._get_session_key(session_id)
        
        class EncryptedSession:
            def __init__(self, encryption_service, key):
                self._service = encryption_service
                self._key = key
            
            async def encrypt(self, data: Union[str, bytes]) -> str:
                if isinstance(data, str):
                    data = data.encode('utf-8')
                provider = self._service.providers[self._key.algorithm]
                encrypted = await provider.encrypt(data, self._key)
                return base64.b64encode(encrypted).decode()
            
            async def decrypt(self, encrypted_data: str) -> bytes:
                data = base64.b64decode(encrypted_data)
                provider = self._service.providers[self._key.algorithm]
                return await provider.decrypt(data, self._key)
        
        try:
            yield EncryptedSession(self, session_key)
        finally:
            # Cleanup if needed
            pass
    
    async def _get_session_key(self, session_id: str) -> EncryptionKey:
        """Get or create session-specific encryption key"""
        key_id = f"session_{hashlib.sha256(session_id.encode()).hexdigest()[:16]}"
        key = await self.key_manager.get_key(key_id)
        
        if not key:
            key = await self.key_manager.generate_key(KeyType.SESSION)
            key.key_id = key_id
            # Session keys expire after 24 hours
            key.expires_at = datetime.utcnow() + timedelta(hours=24)
            await self.key_manager._store_key(key)
        
        return key


# Factory function for easy setup
async def setup_encryption_service(config: Optional[EncryptionConfig] = None,
                                 redis_client: Optional[RedisClient] = None) -> EncryptionService:
    """Set up encryption service with configuration"""
    if not config:
        config = EncryptionConfig()
    
    key_manager = KeyManager(config, redis_client)
    await key_manager.initialize()
    
    service = EncryptionService(config, key_manager)
    
    logger.info("Encryption service initialized")
    return service


# Utility decorators and functions
def encrypt_response_fields(*field_names):
    """Decorator to automatically encrypt specified response fields"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Get encryption service from app state or dependency injection
            # This would need to be implemented based on your FastAPI setup
            encryption_service = kwargs.get('encryption_service')
            if encryption_service and isinstance(result, dict):
                result = await encryption_service.encrypt_payload(result, list(field_names))
            
            return result
        return wrapper
    return decorator


def decrypt_request_fields(*field_names):
    """Decorator to automatically decrypt specified request fields"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Similar implementation for request decryption
            return await func(*args, **kwargs)
        return wrapper
    return decorator