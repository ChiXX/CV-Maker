import subprocess
import sys
import os

def run_migrations():
    """Run database migrations using Alembic."""
    print("Running database migrations...")
    try:
        # Check if we are in Docker or have a specific venv path
        alembic_path = "/app/.venv/bin/alembic"
        if not os.path.exists(alembic_path):
            alembic_path = "alembic"

        result = subprocess.run(
            [alembic_path, "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✅ Database migrations applied successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
