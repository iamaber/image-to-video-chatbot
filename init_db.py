# Initialize database tables for Neon DB
import sys
from db import Base, engine, SessionLocal
from sqlalchemy import text

def init_db():
    # Test connection to Neon DB
    print("Testing Neon DB connection...")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()
            print(f"✅ Connected to PostgreSQL: {version[0]}")
        
        # Create all tables
        print("\nCreating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
        
        # List all tables
        print("\nVerifying tables...")
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = result.fetchall()
            
            if tables:
                print("✅ Tables found:")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("⚠️  No tables found")
        
        print("\n✅ Database initialization complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
