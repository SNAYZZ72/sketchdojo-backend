# =============================================================================
# scripts/init_db.py
# =============================================================================
#!/usr/bin/env python3

"""
Database initialization script for SketchDojo
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import init_db, engine
from app.core.config import settings


async def main():
    """Initialize the database."""
    try:
        print("🗄️ Initializing SketchDojo database...")
        print(f"Database URL: {settings.database_url}")
        
        await init_db()
        
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        sys.exit(1)
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

