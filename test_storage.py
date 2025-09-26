#!/usr/bin/env python3
"""
Test script for the multi-storage backend
Run this to verify your storage configuration works
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Add backend to path
sys.path.append('backend')

# Set up environment for testing
os.environ.setdefault('ENVIRONMENT', 'development')

async def test_storage_backend():
    """Test the storage backend configuration"""
    print("🧪 Testing Storage Backend Configuration")
    print("=" * 50)
    
    # Test data
    test_submission = {
        "name": "Test User",
        "email": "test@example.com",
        "answer": "This is a test submission for storage verification",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Import the main app
        from backend.main import app, init_storage, insert_submission, count_submissions
        
        print("✅ Successfully imported backend modules")
        
        # Test storage initialization
        print("\n🔧 Testing storage initialization...")
        storage_backend = init_storage()
        print(f"✅ Storage backend initialized: {storage_backend}")
        
        # Test submission insertion
        print("\n📝 Testing submission insertion...")
        from backend.main import ContestSubmission
        submission = ContestSubmission(**test_submission)
        submission_id = await insert_submission(submission)
        print(f"✅ Submission inserted with ID: {submission_id}")
        
        # Test count
        print("\n📊 Testing submission count...")
        count = count_submissions()
        print(f"✅ Current submission count: {count}")
        
        print("\n🎉 All tests passed! Your storage backend is working correctly.")
        print(f"📋 Active storage method: {storage_backend}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you have installed the requirements:")
        print("   pip install -r backend/requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Check your environment variables and storage configuration")
        return False

def check_environment():
    """Check environment variables"""
    print("🔍 Checking Environment Variables")
    print("=" * 50)
    
    required_vars = {
        'STORAGE_BACKEND': 'Storage backend selection',
        'SUPABASE_URL': 'Supabase project URL (if using Supabase)',
        'SUPABASE_ANON_KEY': 'Supabase anonymous key (if using Supabase)',
        'GOOGLE_SHEETS_API_KEY': 'Google Sheets API key (if using Sheets)',
        'GOOGLE_SHEET_ID': 'Google Sheets ID (if using Sheets)',
        'DATABASE_URL': 'PostgreSQL connection string (if using PostgreSQL)'
    }
    
    missing_vars = []
    configured_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Don't show full values for security
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked_value}")
            configured_vars.append(var)
        else:
            print(f"❌ {var}: Not set ({description})")
            missing_vars.append(var)
    
    print(f"\n📊 Summary:")
    print(f"   Configured: {len(configured_vars)}/{len(required_vars)}")
    print(f"   Missing: {len(missing_vars)}")
    
    if missing_vars:
        print(f"\n💡 Missing variables: {', '.join(missing_vars)}")
        print("   Set these in your .env file or environment")
    
    return len(missing_vars) == 0

def show_setup_instructions():
    """Show setup instructions based on current configuration"""
    print("\n📋 Setup Instructions")
    print("=" * 50)
    
    storage_backend = os.getenv('STORAGE_BACKEND', 'memory').lower()
    
    if storage_backend == 'supabase':
        print("🎯 You're using Supabase (Recommended)")
        print("1. Create a Supabase project at https://supabase.com")
        print("2. Create a table called 'submissions' with columns:")
        print("   - id (TEXT PRIMARY KEY)")
        print("   - name (TEXT NOT NULL)")
        print("   - email (TEXT NOT NULL)")
        print("   - answer (TEXT NOT NULL)")
        print("   - timestamp (TIMESTAMPTZ DEFAULT NOW())")
        print("3. Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
        
    elif storage_backend == 'sheets':
        print("📊 You're using Google Sheets")
        print("1. Create a Google Sheet with headers: ID, Name, Email, Answer, Timestamp")
        print("2. Enable Google Sheets API in Google Cloud Console")
        print("3. Create an API key and restrict it to Sheets API")
        print("4. Set GOOGLE_SHEETS_API_KEY and GOOGLE_SHEET_ID environment variables")
        
    elif storage_backend == 'postgres':
        print("🐘 You're using PostgreSQL")
        print("1. Set up a PostgreSQL database (Render, Railway, or local)")
        print("2. Create the submissions table")
        print("3. Set DATABASE_URL environment variable")
        
    else:
        print("💾 You're using in-memory storage (data will be lost on restart)")
        print("💡 Consider setting up Supabase or Google Sheets for persistent storage")

async def main():
    """Main test function"""
    print("🚀 ANYTIME Contest Storage Backend Test")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    
    # Show setup instructions
    show_setup_instructions()
    
    if not env_ok:
        print("\n⚠️  Environment not fully configured. Some tests may fail.")
        response = input("\nContinue with tests anyway? (y/N): ")
        if response.lower() != 'y':
            print("👋 Exiting. Configure environment variables and try again.")
            return
    
    # Run storage tests
    print("\n" + "=" * 50)
    success = await test_storage_backend()
    
    if success:
        print("\n🎉 Setup complete! Your contest backend is ready to handle submissions.")
    else:
        print("\n❌ Setup incomplete. Please check the errors above and try again.")

if __name__ == "__main__":
    asyncio.run(main())
