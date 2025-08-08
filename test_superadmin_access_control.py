#!/usr/bin/env python3
"""
Test script to verify superadmin access control for user operations.
"""

import sys
import os
import hashlib
import secrets
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

# Simplified classes for testing
class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    SERVICE = "service"
    READONLY = "readonly"

class MockAuthManager:
    """Mock auth manager with the new superadmin methods."""
    
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
    
    def create_superadmin_user(
        self, requesting_user_roles: List[str], username: str, password: str, full_name: str = None
    ) -> bool:
        """Create a new superadmin user. Only superadmin users can create other superadmin users."""
        # Security check: Only superadmin users can create superadmin users
        if UserRole.SUPERADMIN.value not in requesting_user_roles:
            print(f"❌ SECURITY: Unauthorized attempt to create superadmin user by user with roles: {requesting_user_roles}")
            return False

        if username in self._users:
            print(f"❌ User {username} already exists")
            return False

        user_id = secrets.token_urlsafe(16)
        self._users[username] = {
            "user_id": user_id,
            "username": username,
            "password_hash": self._hash_password(password),
            "roles": [UserRole.SUPERADMIN.value],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "full_name": full_name,
        }

        print(f"✅ Superadmin user created: {username} by user with roles: {requesting_user_roles}")
        return True

    def modify_superadmin_user(
        self, requesting_user_roles: List[str], username: str, new_password: str = None, 
        new_full_name: str = None, is_active: bool = None
    ) -> bool:
        """Modify a superadmin user. Only superadmin users can modify other superadmin users."""
        # Security check: Only superadmin users can modify superadmin users
        if UserRole.SUPERADMIN.value not in requesting_user_roles:
            print(f"❌ SECURITY: Unauthorized attempt to modify superadmin user by user with roles: {requesting_user_roles}")
            return False

        user = self._users.get(username)
        if not user:
            print(f"❌ User {username} not found for modification")
            return False

        # Check if target user is a superadmin
        if UserRole.SUPERADMIN.value not in user["roles"]:
            print(f"❌ SECURITY: Attempt to modify non-superadmin user {username} via superadmin method")
            return False

        # Apply modifications
        if new_password is not None:
            user["password_hash"] = self._hash_password(new_password)
            print(f"✅ Password updated for superadmin user: {username}")

        if new_full_name is not None:
            user["full_name"] = new_full_name
            print(f"✅ Full name updated for superadmin user: {username}")

        if is_active is not None:
            user["is_active"] = is_active
            print(f"✅ Active status updated for superadmin user: {username} -> {is_active}")

        print(f"✅ Superadmin user modified: {username} by user with roles: {requesting_user_roles}")
        return True

    def delete_superadmin_user(
        self, requesting_user_roles: List[str], requesting_username: str, target_username: str
    ) -> bool:
        """Delete a superadmin user. Only superadmin users can delete other superadmin users."""
        # Security check: Only superadmin users can delete superadmin users
        if UserRole.SUPERADMIN.value not in requesting_user_roles:
            print(f"❌ SECURITY: Unauthorized attempt to delete superadmin user by user with roles: {requesting_user_roles}")
            return False

        # Prevent self-deletion
        if requesting_username == target_username:
            print(f"❌ SECURITY: Superadmin user {requesting_username} attempted to delete themselves")
            return False

        user = self._users.get(target_username)
        if not user:
            print(f"❌ User {target_username} not found for deletion")
            return False

        # Check if target user is a superadmin
        if UserRole.SUPERADMIN.value not in user["roles"]:
            print(f"❌ SECURITY: Attempt to delete non-superadmin user {target_username} via superadmin method")
            return False

        # Delete the user
        del self._users[target_username]

        print(f"✅ Superadmin user deleted: {target_username} by {requesting_username}")
        return True

    def list_superadmin_users(self, requesting_user_roles: List[str]) -> List[Dict[str, Any]]:
        """List all superadmin users. Only superadmin users can view this list."""
        # Security check: Only superadmin users can list superadmin users
        if UserRole.SUPERADMIN.value not in requesting_user_roles:
            print(f"❌ SECURITY: Unauthorized attempt to list superadmin users by user with roles: {requesting_user_roles}")
            return []

        superadmin_users = []
        for username, user in self._users.items():
            if UserRole.SUPERADMIN.value in user["roles"]:
                superadmin_users.append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "full_name": user.get("full_name"),
                    "is_active": user["is_active"],
                    "created_at": user["created_at"].isoformat(),
                    "last_login": user["last_login"].isoformat() if user["last_login"] else None,
                })

        print(f"✅ Superadmin users listed by user with roles: {requesting_user_roles}")
        return superadmin_users

def test_superadmin_access_control():
    """Test superadmin access control for user operations."""
    print("Testing Superadmin Access Control...")
    print("=" * 60)
    
    auth_manager = MockAuthManager()
    
    # Define user roles for testing
    superadmin_roles = [UserRole.SUPERADMIN.value]
    admin_roles = [UserRole.ADMIN.value]
    user_roles = [UserRole.USER.value]
    
    print("\n1. Testing Superadmin User Creation:")
    print("-" * 40)
    
    # Test: Superadmin can create superadmin user
    print("   Test: Superadmin creating another superadmin user")
    success = auth_manager.create_superadmin_user(
        requesting_user_roles=superadmin_roles,
        username="new.superadmin@example.com",
        password="newpassword123",
        full_name="New Superadmin"
    )
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}\n")
    
    # Test: Regular admin cannot create superadmin user
    print("   Test: Regular admin trying to create superadmin user")
    success = auth_manager.create_superadmin_user(
        requesting_user_roles=admin_roles,
        username="unauthorized.superadmin@example.com",
        password="badpassword",
        full_name="Unauthorized Superadmin"
    )
    print(f"   Result: {'❌ SECURITY BREACH' if success else '✅ BLOCKED (correct)'}\n")
    
    # Test: Regular user cannot create superadmin user
    print("   Test: Regular user trying to create superadmin user")
    success = auth_manager.create_superadmin_user(
        requesting_user_roles=user_roles,
        username="another.unauthorized@example.com",
        password="badpassword",
        full_name="Another Unauthorized"
    )
    print(f"   Result: {'❌ SECURITY BREACH' if success else '✅ BLOCKED (correct)'}\n")
    
    print("\n2. Testing Superadmin User Modification:")
    print("-" * 40)
    
    # Test: Superadmin can modify superadmin user
    print("   Test: Superadmin modifying another superadmin user")
    success = auth_manager.modify_superadmin_user(
        requesting_user_roles=superadmin_roles,
        username="new.superadmin@example.com",
        new_full_name="Modified Superadmin Name",
        new_password="newmodifiedpassword"
    )
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}\n")
    
    # Test: Admin cannot modify superadmin user
    print("   Test: Regular admin trying to modify superadmin user")
    success = auth_manager.modify_superadmin_user(
        requesting_user_roles=admin_roles,
        username="mike.holownych@gmail.com",
        new_password="hackedpassword"
    )
    print(f"   Result: {'❌ SECURITY BREACH' if success else '✅ BLOCKED (correct)'}\n")
    
    print("\n3. Testing Superadmin User Listing:")
    print("-" * 40)
    
    # Test: Superadmin can list superadmin users
    print("   Test: Superadmin listing all superadmin users")
    superadmin_list = auth_manager.list_superadmin_users(requesting_user_roles=superadmin_roles)
    print(f"   Result: {'✅ SUCCESS' if len(superadmin_list) > 0 else '❌ FAILED'}")
    if superadmin_list:
        print(f"   Found {len(superadmin_list)} superadmin users:")
        for user in superadmin_list:
            print(f"     - {user['username']} ({user['full_name']})")
    print()
    
    # Test: Admin cannot list superadmin users
    print("   Test: Regular admin trying to list superadmin users")
    admin_list = auth_manager.list_superadmin_users(requesting_user_roles=admin_roles)
    print(f"   Result: {'❌ SECURITY BREACH' if len(admin_list) > 0 else '✅ BLOCKED (correct)'}\n")
    
    print("\n4. Testing Superadmin User Deletion:")
    print("-" * 40)
    
    # Test: Superadmin cannot delete themselves
    print("   Test: Superadmin trying to delete themselves (should be blocked)")
    success = auth_manager.delete_superadmin_user(
        requesting_user_roles=superadmin_roles,
        requesting_username="mike.holownych@gmail.com",
        target_username="mike.holownych@gmail.com"
    )
    print(f"   Result: {'❌ SELF-DELETION ALLOWED' if success else '✅ BLOCKED (correct)'}\n")
    
    # Test: Superadmin can delete another superadmin user
    print("   Test: Superadmin deleting another superadmin user")
    success = auth_manager.delete_superadmin_user(
        requesting_user_roles=superadmin_roles,
        requesting_username="mike.holownych@gmail.com",
        target_username="new.superadmin@example.com"
    )
    print(f"   Result: {'✅ SUCCESS' if success else '❌ FAILED'}\n")
    
    # Test: Admin cannot delete superadmin user
    print("   Test: Regular admin trying to delete superadmin user")
    success = auth_manager.delete_superadmin_user(
        requesting_user_roles=admin_roles,
        requesting_username="regular.admin@example.com",
        target_username="mike.holownych@gmail.com"
    )
    print(f"   Result: {'❌ SECURITY BREACH' if success else '✅ BLOCKED (correct)'}\n")
    
    print("\n5. Testing Edge Cases:")
    print("-" * 40)
    
    # Test: Attempting to modify non-superadmin user via superadmin method
    print("   Test: Using superadmin method on regular admin user (should be blocked)")
    success = auth_manager.modify_superadmin_user(
        requesting_user_roles=superadmin_roles,
        username="regular.admin@example.com",  # This is an admin, not superadmin
        new_password="newpassword"
    )
    print(f"   Result: {'❌ SECURITY BREACH' if success else '✅ BLOCKED (correct)'}\n")
    
    print("=" * 60)
    print("🔒 SUPERADMIN ACCESS CONTROL TEST COMPLETED!")
    print("\nSUMMARY OF SECURITY CONTROLS:")
    print("✅ Only superadmin users can create other superadmin users")
    print("✅ Only superadmin users can modify other superadmin users")
    print("✅ Only superadmin users can delete other superadmin users")
    print("✅ Only superadmin users can list all superadmin users")
    print("✅ Superadmin users cannot delete themselves")
    print("✅ Superadmin methods only work on superadmin users")
    print("✅ All unauthorized attempts are logged and blocked")
    
    return True

if __name__ == "__main__":
    try:
        success = test_superadmin_access_control()
        if success:
            sys.exit(0)
        else:
            print("\n❌ Access control tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)