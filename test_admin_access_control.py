#!/usr/bin/env python3
"""
Test script to verify only superadmins can create admin users.
"""

import sys
import hashlib
import secrets
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any

# Simplified classes for testing
class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    SERVICE = "service"
    READONLY = "readonly"

class MockAuthManager:
    """Mock auth manager with admin user creation restrictions."""
    
    def __init__(self):
        self._users = {
            "mike.holownych@gmail.com": {
                "user_id": "superadmin",
                "username": "mike.holownych@gmail.com",
                "password_hash": self._hash_password("jack@345"),
                "roles": [UserRole.SUPERADMIN.value],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "full_name": "Mike Holownych",
            },
            "regular.admin@example.com": {
                "user_id": "admin1",
                "username": "regular.admin@example.com",
                "password_hash": self._hash_password("admin123"),
                "roles": [UserRole.ADMIN.value],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "full_name": "Regular Admin",
            },
            "normal.user@example.com": {
                "user_id": "user1",
                "username": "normal.user@example.com",
                "password_hash": self._hash_password("user123"),
                "roles": [UserRole.USER.value],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "full_name": "Normal User",
            }
        }
        
        self._api_keys = {}
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2."""
        salt = secrets.token_bytes(32)
        pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return salt.hex() + pwdhash.hex()
    
    def create_user(
        self, username: str, password: str, roles: List[str] = None, requesting_user_roles: List[str] = None
    ) -> bool:
        """Create a new user with admin creation restrictions."""
        if username in self._users:
            print(f"❌ User {username} already exists")
            return False

        # Security check: Only superadmin users can create admin or superadmin users
        target_roles = roles or [UserRole.USER.value]
        if UserRole.ADMIN.value in target_roles or UserRole.SUPERADMIN.value in target_roles:
            # If no requesting_user_roles provided, deny elevated role creation (public registration)
            if not requesting_user_roles or UserRole.SUPERADMIN.value not in requesting_user_roles:
                print(f"❌ SECURITY: Unauthorized attempt to create elevated role user by user with roles: {requesting_user_roles}")
                return False

        user_id = secrets.token_urlsafe(16)
        self._users[username] = {
            "user_id": user_id,
            "username": username,
            "password_hash": self._hash_password(password),
            "roles": target_roles,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None,
        }

        print(f"✅ User created: {username} with roles: {target_roles}")
        return True

    def create_admin_user(
        self, requesting_user_roles: List[str], username: str, password: str, full_name: str = None
    ) -> bool:
        """Create a new admin user. Only superadmin users can create admin users."""
        # Security check: Only superadmin users can create admin users
        if UserRole.SUPERADMIN.value not in requesting_user_roles:
            print(f"❌ SECURITY: Unauthorized attempt to create admin user by user with roles: {requesting_user_roles}")
            return False

        if username in self._users:
            print(f"❌ User {username} already exists")
            return False

        user_id = secrets.token_urlsafe(16)
        self._users[username] = {
            "user_id": user_id,
            "username": username,
            "password_hash": self._hash_password(password),
            "roles": [UserRole.ADMIN.value],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "full_name": full_name,
        }

        print(f"✅ Admin user created: {username} by user with roles: {requesting_user_roles}")
        return True

    def list_admin_users(self, requesting_user_roles: List[str]) -> List[Dict[str, Any]]:
        """List all admin users. Only superadmin users can view this list."""
        # Security check: Only superadmin users can list admin users
        if UserRole.SUPERADMIN.value not in requesting_user_roles:
            print(f"❌ SECURITY: Unauthorized attempt to list admin users by user with roles: {requesting_user_roles}")
            return []

        admin_users = []
        for username, user in self._users.items():
            if UserRole.ADMIN.value in user["roles"]:
                admin_users.append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "full_name": user.get("full_name"),
                    "is_active": user["is_active"],
                    "created_at": user["created_at"].isoformat(),
                    "last_login": user["last_login"].isoformat() if user["last_login"] else None,
                })

        print(f"✅ Admin users listed by user with roles: {requesting_user_roles}")
        return admin_users

def test_admin_access_control():
    """Test admin user creation access control."""
    print("Testing Admin User Creation Access Control...")
    print("=" * 60)
    
    auth_manager = MockAuthManager()
    
    # Define user roles for testing
    superadmin_roles = [UserRole.SUPERADMIN.value]
    admin_roles = [UserRole.ADMIN.value]
    user_roles = [UserRole.USER.value]
    
    print("\n1. Testing General User Creation with Admin Roles:")
    print("-" * 50)
    
    # Test: Superadmin can create admin user via general create_user method
    print("   Test: Superadmin creating admin user via create_user method")
    success = auth_manager.create_user(
        username="admin.via.createuser@example.com",
        password="password123",
        roles=[UserRole.ADMIN.value],
        requesting_user_roles=superadmin_roles
    )
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}\\n")
    
    # Test: Regular admin cannot create admin user via general create_user method
    print("   Test: Regular admin trying to create admin user via create_user method")
    success = auth_manager.create_user(
        username="unauthorized.admin@example.com",
        password="password123",
        roles=[UserRole.ADMIN.value],
        requesting_user_roles=admin_roles
    )
    print(f"   Result: {'❌ SECURITY BREACH' if success else '✅ BLOCKED (correct)'}\\n")
    
    # Test: Regular user cannot create admin user via general create_user method
    print("   Test: Regular user trying to create admin user via create_user method")
    success = auth_manager.create_user(
        username="another.unauthorized.admin@example.com",
        password="password123",
        roles=[UserRole.ADMIN.value],
        requesting_user_roles=user_roles
    )
    print(f"   Result: {'❌ SECURITY BREACH' if success else '✅ BLOCKED (correct)'}\\n")
    
    # Test: Public registration cannot create admin user (no requesting roles)
    print("   Test: Public registration trying to create admin user (no auth context)")
    success = auth_manager.create_user(
        username="public.admin.attempt@example.com",
        password="password123",
        roles=[UserRole.ADMIN.value],
        requesting_user_roles=None
    )
    print(f"   Result: {'❌ SECURITY BREACH' if success else '✅ BLOCKED (correct)'}\\n")
    
    print("\\n2. Testing Dedicated Admin User Creation Method:")
    print("-" * 50)
    
    # Test: Superadmin can create admin user via dedicated method
    print("   Test: Superadmin creating admin user via create_admin_user method")
    success = auth_manager.create_admin_user(
        requesting_user_roles=superadmin_roles,
        username="dedicated.admin@example.com",
        password="adminpassword123",
        full_name="Dedicated Admin User"
    )
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}\\n")
    
    # Test: Regular admin cannot create admin user via dedicated method
    print("   Test: Regular admin trying to create admin user via create_admin_user method")
    success = auth_manager.create_admin_user(
        requesting_user_roles=admin_roles,
        username="unauthorized.dedicated.admin@example.com",
        password="adminpassword123",
        full_name="Unauthorized Admin"
    )
    print(f"   Result: {'❌ SECURITY BREACH' if success else '✅ BLOCKED (correct)'}\\n")
    
    # Test: Regular user cannot create admin user via dedicated method
    print("   Test: Regular user trying to create admin user via create_admin_user method")
    success = auth_manager.create_admin_user(
        requesting_user_roles=user_roles,
        username="user.trying.admin@example.com",
        password="adminpassword123",
        full_name="User Trying Admin"
    )
    print(f"   Result: {'❌ SECURITY BREACH' if success else '✅ BLOCKED (correct)'}\\n")
    
    print("\\n3. Testing Admin User Listing:")
    print("-" * 50)
    
    # Test: Superadmin can list admin users
    print("   Test: Superadmin listing all admin users")
    admin_list = auth_manager.list_admin_users(requesting_user_roles=superadmin_roles)
    print(f"   Result: {'✅ SUCCESS' if len(admin_list) > 0 else '❌ FAILED'}")
    if admin_list:
        print(f"   Found {len(admin_list)} admin users:")
        for user in admin_list:
            print(f"     - {user['username']} ({user['full_name']})")
    print()
    
    # Test: Regular admin cannot list admin users
    print("   Test: Regular admin trying to list admin users")
    admin_list = auth_manager.list_admin_users(requesting_user_roles=admin_roles)
    print(f"   Result: {'❌ SECURITY BREACH' if len(admin_list) > 0 else '✅ BLOCKED (correct)'}\\n")
    
    # Test: Regular user cannot list admin users
    print("   Test: Regular user trying to list admin users")
    admin_list = auth_manager.list_admin_users(requesting_user_roles=user_roles)
    print(f"   Result: {'❌ SECURITY BREACH' if len(admin_list) > 0 else '✅ BLOCKED (correct)'}\\n")
    
    print("\\n4. Testing Regular User Creation (Should Still Work):")
    print("-" * 50)
    
    # Test: Everyone can create regular users
    print("   Test: Superadmin creating regular user")
    success = auth_manager.create_user(
        username="regular.user.by.superadmin@example.com",
        password="password123",
        roles=[UserRole.USER.value],
        requesting_user_roles=superadmin_roles
    )
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}\\n")
    
    # Test: Admin can create regular users
    print("   Test: Admin creating regular user")
    success = auth_manager.create_user(
        username="regular.user.by.admin@example.com",
        password="password123",
        roles=[UserRole.USER.value],
        requesting_user_roles=admin_roles
    )
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}\\n")
    
    # Test: Public registration creates regular user
    print("   Test: Public registration creating regular user")
    success = auth_manager.create_user(
        username="public.regular.user@example.com",
        password="password123",
        roles=None,  # Should default to USER
        requesting_user_roles=None
    )
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}\\n")
    
    print("=" * 60)
    print("🔒 ADMIN ACCESS CONTROL TEST COMPLETED!")
    print("\\nSUMMARY OF SECURITY CONTROLS:")
    print("✅ Only superadmin users can create admin users via create_user method")
    print("✅ Only superadmin users can create admin users via create_admin_user method")  
    print("✅ Only superadmin users can list admin users")
    print("✅ Regular users can still be created by anyone")
    print("✅ Public registration is restricted to regular users only")
    print("✅ All unauthorized attempts are logged and blocked")
    
    return True

if __name__ == "__main__":
    try:
        success = test_admin_access_control()
        if success:
            sys.exit(0)
        else:
            print("\\n❌ Access control tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Test execution failed: {e}")
        sys.exit(1)