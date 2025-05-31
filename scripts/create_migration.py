# =============================================================================
# scripts/create_migration.py
# =============================================================================
#!/usr/bin/env python3

"""
Create a new database migration
"""

import subprocess
import sys
import os


def main():
    """Create a new migration."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/create_migration.py 'migration message'")
        sys.exit(1)
    
    message = sys.argv[1]
    
    # Ensure we're in the project root
    project_root = os.path.dirname(os.path.dirname(__file__))
    os.chdir(project_root)
    
    try:
        # Create migration
        result = subprocess.run([
            "alembic", "revision", "--autogenerate", "-m", message
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Migration created successfully:")
            print(result.stdout)
        else:
            print(f"❌ Failed to create migration:")
            print(result.stderr)
            sys.exit(1)
    
    except FileNotFoundError:
        print("❌ Alembic not found. Make sure it's installed: pip install alembic")
        sys.exit(1)


if __name__ == "__main__":
    main()
