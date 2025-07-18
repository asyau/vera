import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_connection_pooler():
    """Test connection using connection pooler (port 6543)"""
    try:
        conn = psycopg2.connect(
            host="aws-0-eu-central-1.pooler.supabase.com",
            port="6543",  # Connection pooler port
            database="postgres",
            user="postgres.aphnekdbxvzcofzzxghu",
            password="Virastartupsok"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"✅ Connection Pooler (port 6543) - Connected to: {db_version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection Pooler (port 6543) - Failed: {e}")
        return False

def test_direct_connection():
    """Test direct connection (port 5432)"""
    try:
        conn = psycopg2.connect(
            host="aws-0-eu-central-1.pooler.supabase.com", 
            port="5432",  # Direct connection port
            database="postgres", 
            user="postgres.aphnekdbxvzcofzzxghu", 
            password="Virastartupsok"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"✅ Direct Connection (port 5432) - Connected to: {db_version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Direct Connection (port 5432) - Failed: {e}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection using the current DATABASE_URL"""
    try:
        from sqlalchemy import create_engine, text
        
        # Test with connection pooler URL
        pooler_url = "postgresql://postgres.aphnekdbxvzcofzzxghu:Virastartupsok@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
        engine = create_engine(pooler_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ SQLAlchemy Connection Pooler - Connected to: {version}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy Connection Pooler - Failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing database connections...\n")
    
    # Test both connection methods
    pooler_success = test_connection_pooler()
    direct_success = test_direct_connection()
    sqlalchemy_success = test_sqlalchemy_connection()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Connection Pooler (6543): {'✅ SUCCESS' if pooler_success else '❌ FAILED'}")
    print(f"Direct Connection (5432): {'✅ SUCCESS' if direct_success else '❌ FAILED'}")
    print(f"SQLAlchemy Pooler: {'✅ SUCCESS' if sqlalchemy_success else '❌ FAILED'}")
    
    if pooler_success or direct_success:
        print("\n🎉 Database connection is working!")
        if pooler_success:
            print("💡 Recommendation: Use connection pooler (port 6543) for better performance")
        else:
            print("💡 Recommendation: Use direct connection (port 5432)")
    else:
        print("\n❌ All connection attempts failed. Please check your credentials and network.") 