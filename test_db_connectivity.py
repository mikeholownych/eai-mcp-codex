#!/usr/bin/env python3
"""Database connectivity test script."""

<<<<<<< HEAD
=======
import sys
import os
>>>>>>> main
import psycopg2
from psycopg2 import sql

def test_database_connection():
    """Test connection to all databases."""
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'mcp_user',
        'password': 'mcp_secure_password'  # Default from docker-compose
    }
    
    databases = [
        'mcp_database',
        'auth_db',
        'staff_db',
        'plan_management_db',
        'git_worktree_db',
        'workflow_orchestrator_db',
        'verification_feedback_db'
    ]
    
    print("Testing database connections...")
    print("=" * 50)
    
    for db_name in databases:
        try:
            # Connect to database
            conn = psycopg2.connect(database=db_name, **db_config)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # List tables
            cursor.execute(sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"))
            tables = cursor.fetchall()
            
            print(f"✓ {db_name}: Connected successfully")
            print(f"  Version: {version.split(',')[0]}")
            print(f"  Tables: {[table[0] for table in tables]}")
            
            # Test table creation if no tables exist
            if not tables:
<<<<<<< HEAD
                print("  No tables found - creating test table...")
                cursor.execute("CREATE TABLE test_connection (id SERIAL PRIMARY KEY, test_text VARCHAR(100));")
                cursor.execute("INSERT INTO test_connection (test_text) VALUES ('Database connection test successful');")
                conn.commit()
                print("  ✓ Test table created and populated")
=======
                print(f"  No tables found - creating test table...")
                cursor.execute("CREATE TABLE test_connection (id SERIAL PRIMARY KEY, test_text VARCHAR(100));")
                cursor.execute("INSERT INTO test_connection (test_text) VALUES ('Database connection test successful');")
                conn.commit()
                print(f"  ✓ Test table created and populated")
>>>>>>> main
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"✗ {db_name}: Connection failed - {str(e)}")
        
        print("-" * 50)
    
    print("Database connectivity test completed!")

if __name__ == "__main__":
    test_database_connection()