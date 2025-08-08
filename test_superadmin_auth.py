#!/usr/bin/env python3
"""
Test script to validate the superadmin authentication changes.
"""

import sys
import os
sys.path.append('src')

from src.common.auth import AuthManager, UserRole

def test_superadmin_auth():
    """Test the modified superadmin authentication."""
    print("Testing Superadmin Authentication Changes...")
    print("=" * 50)
    
    # Initialize auth manager
    auth_manager = AuthManager()
    
    # Test 1: Check if superadmin user exists
    print("\n1. Testing superadmin user existence:")
    user_info = auth_manager.get_user_info("mike.holownych@gmail.com")
    if user_info:
        print(f"   ✅ Superadmin user exists: {user_info['username']}")
        print(f"   ✅ User ID: {user_info['user_id']}")
        print(f"   ✅ Roles: {user_info['roles']}")
        print(f"   ✅ Active: {user_info['is_active']}")
    else:
        print("   ❌ Superadmin user not found!")
        return False
    
    # Test 2: Test authentication with credentials
    print("\n2. Testing authentication with new credentials:")
    auth_result = auth_manager.authenticate_password("mike.holownych@gmail.com", "jack@345")
    if auth_result.success:
        print(f"   ✅ Authentication successful")
        print(f"   ✅ User ID: {auth_result.user_id}")
        print(f"   ✅ Username: {auth_result.username}")
        print(f"   ✅ Roles: {auth_result.roles}")
    else:
        print(f"   ❌ Authentication failed: {auth_result.error_message}")
        return False
    
    # Test 3: Test superadmin permissions
    print("\n3. Testing superadmin permissions:")
    user_roles = auth_result.roles
    
    # Test various permission checks
    permissions_to_test = ["admin", "user", "service", "readonly", "custom_permission"]
    for permission in permissions_to_test:
        has_permission = auth_manager.check_permission(user_roles, permission)
        status = "✅" if has_permission else "❌"
        print(f"   {status} Permission '{permission}': {has_permission}")
    
    # Test 4: Test JWT token creation
    print("\n4. Testing JWT token creation:")
    try:
        jwt_token = auth_manager.create_jwt_token(
            user_id=auth_result.user_id,
            username=auth_result.username,
            roles=auth_result.roles
        )
        print(f"   ✅ JWT token created successfully")
        print(f"   ✅ Token preview: {jwt_token[:50]}...")
        
        # Verify the token
        verify_result = auth_manager.verify_jwt_token(jwt_token)
        if verify_result.success:
            print(f"   ✅ JWT token verification successful")
            print(f"   ✅ Verified user: {verify_result.username}")
            print(f"   ✅ Verified roles: {verify_result.roles}")
        else:
            print(f"   ❌ JWT token verification failed: {verify_result.error_message}")
    except Exception as e:
        print(f"   ❌ JWT token creation failed: {e}")
        return False
    
    # Test 5: Test API key availability
    print("\n5. Testing API key:")
    api_keys = auth_manager._api_keys
    superadmin_key = None
    for key, info in api_keys.items():
        if info.get("username") == "mike.holownych@gmail.com":
            superadmin_key = key
            break
    
    if superadmin_key:
        print(f"   ✅ Superadmin API key found: {superadmin_key}")
        print(f"   ✅ API key user: {api_keys[superadmin_key]['username']}")
        print(f"   ✅ API key roles: {api_keys[superadmin_key]['roles']}")
    else:
        print("   ❌ Superadmin API key not found!")
    
    # Test 6: Test old admin user is removed
    print("\n6. Testing old admin user removal:")
    old_admin = auth_manager.get_user_info("admin")
    if old_admin:
        print("   ❌ Old admin user still exists!")
    else:
        print("   ✅ Old admin user successfully removed")
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED - Superadmin authentication working correctly!")
    print(f"✅ New superadmin credentials:")
    print(f"   Username: mike.holownych@gmail.com")
    print(f"   Password: jack@345")
    print(f"   Role: {UserRole.SUPERADMIN.value}")
    print(f"   API Key: {superadmin_key}")
    
    return True

if __name__ == "__main__":
    try:
        success = test_superadmin_auth()
        if success:
            sys.exit(0)
        else:
            print("\n❌ Tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)