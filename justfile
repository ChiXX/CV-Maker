# CV-Maker Project Commands

# Default recipe (run when you just type 'just')
default:
    @just --list

# Database commands
db-start:
    docker-compose up -d

db-stop:
    docker-compose down

db-init:
    source .venv/bin/activate && python init_db.py

db-logs:
    docker-compose logs -f postgres

# Virtual environment commands
venv-activate:
    source .venv/bin/activate

# Application commands
run:
    source .venv/bin/activate && python main.py

run-cv url:
    source .venv/bin/activate && echo "{{url}}" | python main.py

# Development commands
install:
    pip install -r requirements.txt

freeze:
    pip freeze > requirements.txt

clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    rm -rf Applications/

# Setup commands
setup: db-start db-init
    @echo "Setup complete! Run 'just run' to start the application."

# Full development setup
dev-setup: install db-start db-init
    @echo "Development environment ready! Run 'just run' to start the application."

# Show status
status:
    @echo "=== Database Status ==="
    @docker ps | grep cv_maker_db || echo "Database not running"
    @echo ""
    @echo "=== Environment ==="
    @ls -la .env || echo ".env file not found"
    @echo ""
    @echo "=== Recent Applications ==="
    @ls -la Applications/ 2>/dev/null || echo "No applications directory"
