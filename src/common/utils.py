"""Common utility functions."""

import os
import json
import hashlib
import secrets
import tempfile
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .logging import get_logger

logger = get_logger("utils")


def generate_id(length: int = 8) -> str:
    """Generate a random alphanumeric ID."""
    return secrets.token_urlsafe(length)[:length]


def generate_hash(data: str, algorithm: str = "sha256") -> str:
    """Generate a hash of the given data."""
    hash_func = getattr(hashlib, algorithm)()
    hash_func.update(data.encode('utf-8'))
    return hash_func.hexdigest()


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string, returning default on error."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "null") -> str:
    """Safely serialize object to JSON, returning default on error."""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return default


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """Unflatten a dictionary with dot-separated keys."""
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    return result


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List[Any], key_func: callable = None) -> List[Any]:
    """Remove duplicates from a list, optionally using a key function."""
    if key_func is None:
        return list(dict.fromkeys(lst))
    
    seen = set()
    result = []
    
    for item in lst:
        key = key_func(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


def format_bytes(bytes_value: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds as human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length with optional suffix."""
    if len(text) <= max_length:
        return text
    
    truncated_length = max_length - len(suffix)
    return text[:truncated_length] + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing/replacing invalid characters."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        max_name_length = 255 - len(ext)
        filename = name[:max_name_length] + ext
    
    return filename or "untitled"


def ensure_directory(path: str) -> Path:
    """Ensure directory exists, creating it if necessary."""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def create_temp_file(suffix: str = "", prefix: str = "tmp", content: str = None) -> str:
    """Create a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix=suffix, 
        prefix=prefix, 
        delete=False
    ) as tmp_file:
        if content:
            tmp_file.write(content)
        return tmp_file.name


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except (OSError, FileNotFoundError):
        return 0


def get_file_modification_time(file_path: str) -> Optional[datetime]:
    """Get file modification time."""
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp)
    except (OSError, FileNotFoundError):
        return None


def is_file_older_than(file_path: str, hours: int) -> bool:
    """Check if file is older than specified hours."""
    mod_time = get_file_modification_time(file_path)
    if mod_time is None:
        return True
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    return mod_time < cutoff_time


def retry_operation(func: callable, max_attempts: int = 3, delay_seconds: float = 1.0) -> Any:
    """Retry an operation with exponential backoff."""
    import time
    
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_attempts - 1:
                wait_time = delay_seconds * (2 ** attempt)
                logger.warning(f"Operation failed (attempt {attempt + 1}/{max_attempts}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"Operation failed after {max_attempts} attempts: {e}")
    
    raise last_exception


def batch_process(items: List[Any], batch_size: int, process_func: callable) -> List[Any]:
    """Process items in batches."""
    results = []
    
    for batch in chunk_list(items, batch_size):
        try:
            batch_results = process_func(batch)
            if isinstance(batch_results, list):
                results.extend(batch_results)
            else:
                results.append(batch_results)
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Continue with next batch
            continue
    
    return results


def normalize_path(path: str) -> str:
    """Normalize file path for consistent handling."""
    return os.path.normpath(os.path.expanduser(path))


def get_relative_path(path: str, base_path: str) -> str:
    """Get relative path from base path."""
    return os.path.relpath(normalize_path(path), normalize_path(base_path))


def is_subpath(path: str, parent: str) -> bool:
    """Check if path is a subpath of parent."""
    try:
        path_obj = Path(path).resolve()
        parent_obj = Path(parent).resolve()
        return parent_obj in path_obj.parents or path_obj == parent_obj
    except (OSError, ValueError):
        return False


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries."""
    result = {}
    for config in configs:
        if config:
            result = deep_merge_dicts(result, config)
    return result


def get_env_bool(env_var: str, default: bool = False) -> bool:
    """Get boolean value from environment variable."""
    value = os.getenv(env_var, "").lower()
    return value in ("true", "1", "yes", "on") if value else default


def get_env_int(env_var: str, default: int = 0) -> int:
    """Get integer value from environment variable."""
    try:
        return int(os.getenv(env_var, str(default)))
    except (ValueError, TypeError):
        return default


def get_env_float(env_var: str, default: float = 0.0) -> float:
    """Get float value from environment variable."""
    try:
        return float(os.getenv(env_var, str(default)))
    except (ValueError, TypeError):
        return default


def get_env_list(env_var: str, separator: str = ",", default: List[str] = None) -> List[str]:
    """Get list value from environment variable."""
    value = os.getenv(env_var)
    if not value:
        return default or []
    
    return [item.strip() for item in value.split(separator) if item.strip()]


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = self.elapsed_seconds
        logger.info(f"{self.description} completed in {format_duration(duration)}")
    
    @property
    def elapsed_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class RateLimiter:
    """Simple rate limiter."""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Check if a call is allowed under the rate limit."""
        now = datetime.now()
        
        # Remove old calls outside the time window
        cutoff_time = now - timedelta(seconds=self.time_window)
        self.calls = [call_time for call_time in self.calls if call_time > cutoff_time]
        
        # Check if we can make another call
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_time(self) -> float:
        """Get the time to wait before the next call is allowed."""
        if not self.calls:
            return 0.0
        
        oldest_call = min(self.calls)
        next_available = oldest_call + timedelta(seconds=self.time_window)
        wait_seconds = (next_available - datetime.now()).total_seconds()
        
        return max(0.0, wait_seconds)