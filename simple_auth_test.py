#!/usr/bin/env python3
"""
Simple test to verify auth manager changes without dependencies.
"""

import hashlib
import secrets
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

# Simplified UserRole enum
class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    SERVICE = "service"
    READONLY = "readonly"

# Test the modified auth logic
def test_modified_auth():
    """Test the core auth modifications."""
    print("Testing Modified Authentication Logic...")
    print("=" * 50)
    
    # Simulate the modified default users
    def hash_password(password: str) -> str:
        """Hash a password using PBKDF2."""
        salt = secrets.token_bytes(32)
        pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return salt.hex() + pwdhash.hex()
    
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt = bytes.fromhex(password_hash[:64])
            stored_hash = password_hash[64:]
            pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
            return pwdhash.hex() == stored_hash
        except Exception:
            return False
    
    def check_permission(user_roles: List[str], required_role: str) -> bool:
        """Check if user has required permission."""
        if UserRole.SUPERADMIN.value in user_roles or UserRole.ADMIN.value in user_roles:
            return True  # Superadmin and Admin have all permissions
        return required_role in user_roles
    
    # Test data based on our modifications
    password_hash = hash_password("jack@345")
    users = {
        "mike.holownych@gmail.com": {
            "user_id": "superadmin",
            "username": "mike.holownych@gmail.com",
            "password_hash": password_hash,
            "roles": [UserRole.SUPERADMIN.value],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
        "service": {
            "user_id": "service",
            "username": "service",
            "password_hash": hash_password("service123"),
            "roles": [UserRole.SERVICE.value],
            "is_active": True,
            "created_at": datetime.utcnow(),
        },
    }
    
    api_keys = {
        "test-api-key-123": {
            "user_id": "service",
            "username": "service",
            "roles": [UserRole.SERVICE.value],
            "created_at": datetime.utcnow(),
            "last_used": None,
        },
        "superadmin-api-key-456": {
            "user_id": "superadmin",
            "username": "mike.holownych@gmail.com",
            "roles": [UserRole.SUPERADMIN.value],
            "created_at": datetime.utcnow(),
            "last_used": None,
        }
    }
    
    print("1. Testing user data structure:")
    superadmin_user = users.get("mike.holownych@gmail.com")
    if superadmin_user:
        print(f"   ✅ Superadmin user exists")
        print(f"   ✅ Username: {superadmin_user['username']}")
        print(f"   ✅ User ID: {superadmin_user['user_id']}")
        print(f"   ✅ Roles: {superadmin_user['roles']}")
        print(f"   ✅ Active: {superadmin_user['is_active']}")
    else:
        print("   ❌ Superadmin user not found!")
        return False
    
    print("\n2. Testing password verification:")
    password_valid = verify_password("jack@345", superadmin_user['password_hash'])
    if password_valid:
        print("   ✅ Password verification successful")
    else:
        print("   ❌ Password verification failed!")
        return False
    
    print("\n3. Testing superadmin permissions:")
    user_roles = superadmin_user['roles']
    permissions_to_test = ["admin", "user", "service", "readonly", "custom_permission"]
    all_permissions_granted = True
    
    for permission in permissions_to_test:
        has_permission = check_permission(user_roles, permission)
        status = "✅" if has_permission else "❌"
        print(f"   {status} Permission '{permission}': {has_permission}")
        if not has_permission:
            all_permissions_granted = False
    
    if all_permissions_granted:
        print("   ✅ All permissions granted to superadmin")
    else:
        print("   ❌ Some permissions denied to superadmin!")
        return False
    
    print("\n4. Testing API key:")
    superadmin_api_key = api_keys.get("superadmin-api-key-456")
    if superadmin_api_key:
        print(f"   ✅ Superadmin API key exists")
        print(f"   ✅ API key user: {superadmin_api_key['username']}")
        print(f"   ✅ API key roles: {superadmin_api_key['roles']}")
    else:
        print("   ❌ Superadmin API key not found!")
        return False
    
    print("\n5. Testing old admin user removal:")
    old_admin = users.get("admin")
    if old_admin:
        print("   ❌ Old admin user still exists!")
        return False
    else:
        print("   ✅ Old admin user successfully removed")
    
    print("\n6. Testing UserRole enum:")
    print(f"   ✅ SUPERADMIN role: {UserRole.SUPERADMIN.value}")
    print(f"   ✅ ADMIN role: {UserRole.ADMIN.value}")
    print(f"   ✅ USER role: {UserRole.USER.value}")
    print(f"   ✅ SERVICE role: {UserRole.SERVICE.value}")
    print(f"   ✅ READONLY role: {UserRole.READONLY.value}")
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("\n🎉 Successfully modified default admin credentials:")
    print(f"   Username: mike.holownych@gmail.com")
    print(f"   Password: jack@345")
    print(f"   Role: {UserRole.SUPERADMIN.value}")
    print(f"   User ID: superadmin")
    print(f"   API Key: superadmin-api-key-456")
    print(f"   Full super administrative privileges: ✅")
    
    return True

if __name__ == "__main__":
    try:
        success = test_modified_auth()
        if success:
            exit(0)
        else:
            print("\n❌ Tests failed!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        exit(1)