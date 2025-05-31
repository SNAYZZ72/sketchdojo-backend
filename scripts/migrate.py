# =============================================================================
# scripts/migrate.py
# =============================================================================
#!/usr/bin/env python3

"""
Run database migrations
"""

import subprocess
import sys
import os


def main():
    """Run database migrations."""
    # Ensure we're in the project root
    project_root = os.path.dirname(os.path.dirname(__file__))
    os.chdir(project_root)
    
    command = "upgrade"
    target = "head"
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
    
    if len(sys.argv) > 2:
        target = sys.argv[2]
    
    try:
        if command == "upgrade":
            print(f"🔄 Running database migrations to {target}...")
            result = subprocess.run([
                "alembic", "upgrade", target
            ], capture_output=True, text=True)
        
        elif command == "downgrade":
            print(f"🔄 Downgrading database to {target}...")
            result = subprocess.run([
                "alembic", "downgrade", target
            ], capture_output=True, text=True)
        
        elif command == "current":
            print("📋 Checking current migration status...")
            result = subprocess.run([
                "alembic", "current"
            ], capture_output=True, text=True)
        
        elif command == "history":
            print("📜 Migration history:")
            result = subprocess.run([
                "alembic", "history", "--verbose"
            ], capture_output=True, text=True)
        
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: upgrade, downgrade, current, history")
            sys.exit(1)
        
        if result.returncode == 0:
            print("✅ Migration command completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ Migration command failed:")
            print(result.stderr)
            sys.exit(1)
    
    except FileNotFoundError:
        print("❌ Alembic not found. Make sure it's installed: pip install alembic")
        sys.exit(1)


if __name__ == "__main__":
    main()