import asyncio
import asyncpg

async def test_connection():
    """Test database connection using asyncpg"""
    try:
        # Test connection pooler (port 6543)
        conn = await asyncpg.connect(
            host="db.aphnekdbxvzcofzzxghu.supabase.co",
            port=6543,
            database="postgres",
            user="postgres",
            password="Virastartupsok"
        )
        
        version = await conn.fetchval("SELECT version();")
        print(f"✅ Connection Pooler (port 6543) - Connected to: {version}")
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection Pooler (port 6543) - Failed: {e}")
        
        try:
            # Try direct connection (port 5432)
            conn = await asyncpg.connect(
                host="db.aphnekdbxvzcofzzxghu.supabase.co",
                port=5432,
                database="postgres",
                user="postgres",
                password="Virastartupsok"
            )
            
            version = await conn.fetchval("SELECT version();")
            print(f"✅ Direct Connection (port 5432) - Connected to: {version}")
            await conn.close()
            return True
            
        except Exception as e2:
            print(f"❌ Direct Connection (port 5432) - Failed: {e2}")
            return False

if __name__ == "__main__":
    print("Testing database connection with asyncpg...\n")
    
    success = asyncio.run(test_connection())
    
    if success:
        print("\n🎉 Database connection is working!")
    else:
        print("\n❌ All connection attempts failed. Please check your credentials and network.") 