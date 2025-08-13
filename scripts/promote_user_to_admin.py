#!/usr/bin/env python3
"""
Script to promote a user to admin role in the auth service.
This directly modifies the in-memory user store.
"""

import httpx
import sys
import asyncio

async def promote_user_to_admin(username: str, auth_service_url: str = "http://localhost:8007"):
    """
    Promote a user to admin role by directly accessing the auth service.
    Since the auth service uses in-memory storage, we need to access it directly.
    """
    
    # First, let's try to get the admin token to see if we can modify users
    admin_login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Login as admin
            login_response = await client.post(
                f"{auth_service_url}/api/auth/login",
                json=admin_login_data
            )
            
            if login_response.status_code != 200:
                print(f"Failed to login as admin: {login_response.text}")
                return False
            
            # Unfortunately, there's no API endpoint to modify user roles
            # The auth service would need to be modified to support this
            print("ERROR: The auth service doesn't have an API endpoint to modify user roles.")
            print(f"The user '{username}' has been created with 'user' role, but cannot be promoted to 'admin' role through the API.")
            print("")
            print("Solutions:")
            print("1. Delete the user and recreate with admin role in the auth manager code")
            print("2. Add a user role modification endpoint to the auth service")
            print("3. Use the existing admin user (username: 'admin', password: 'admin123')")
            
            return False
            
        except Exception as e:
            print(f"Error: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_user_to_admin.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    asyncio.run(promote_user_to_admin(username))