import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def test_connection_pooler():
    """Test connection using connection pooler (port 6543)"""
    try:
        # Test with connection pooler URL
        pooler_url = "postgresql://postgres:Virastartupsok@db.aphnekdbxvzcofzzxghu.supabase.co:6543/postgres"
        engine = create_engine(pooler_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connection Pooler (port 6543) - Connected to: {version}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection Pooler (port 6543) - Failed: {e}")
        return False

def test_direct_connection():
    """Test direct connection (port 5432)"""
    try:
        # Test with direct connection URL
        direct_url = "postgresql://postgres:Virastartupsok@db.aphnekdbxvzcofzzxghu.supabase.co:5432/postgres"
        engine = create_engine(direct_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Direct Connection (port 5432) - Connected to: {version}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct Connection (port 5432) - Failed: {e}")
        return False

def test_current_config():
    """Test the current DATABASE_URL from database.py"""
    try:
        # Import the current database configuration
        from app.database import engine
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Current Config - Connected to: {version}")
        
        return True
        
    except Exception as e:
        print(f"❌ Current Config - Failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing database connections with SQLAlchemy...\n")
    
    # Test both connection methods
    pooler_success = test_connection_pooler()
    direct_success = test_direct_connection()
    current_success = test_current_config()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Connection Pooler (6543): {'✅ SUCCESS' if pooler_success else '❌ FAILED'}")
    print(f"Direct Connection (5432): {'✅ SUCCESS' if direct_success else '❌ FAILED'}")
    print(f"Current Config: {'✅ SUCCESS' if current_success else '❌ FAILED'}")
    
    if pooler_success or direct_success:
        print("\n🎉 Database connection is working!")
        if pooler_success:
            print("💡 Recommendation: Use connection pooler (port 6543) for better performance")
        else:
            print("💡 Recommendation: Use direct connection (port 5432)")
    else:
        print("\n❌ All connection attempts failed. Please check your credentials and network.") 