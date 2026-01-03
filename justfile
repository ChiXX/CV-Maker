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

# Frontend commands
ui-up:
    docker-compose -f docker-compose.dev.yml up frontend

ui-down:
    docker-compose -f docker-compose.dev.yml down frontend

ui-logs:
    docker-compose -f docker-compose.dev.yml logs -f frontend

ui-restart:
    docker-compose -f docker-compose.dev.yml restart frontend

# Start both API and UI
api-and-ui:
    docker-compose -f docker-compose.dev.yml up api frontend

# Docker development commands (with hot reload)
dev-up:
    docker-compose -f docker-compose.dev.yml up

dev-down:
    docker-compose -f docker-compose.dev.yml down

dev-logs:
    docker-compose -f docker-compose.dev.yml logs -f api

dev-restart:
    docker-compose -f docker-compose.dev.yml restart api

# Production mode
prod-up:
    docker-compose up -d

prod-down:
    docker-compose down

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
    @echo "=== Development Status ==="
    @docker ps | grep cv_maker_api_dev || echo "Development API not running"
    @echo ""
    @echo "=== Environment ==="
    @ls -la .env 2>/dev/null || echo ".env file not found"
    @echo ""
    @echo "=== Recent Applications ==="
    @ls -la Applications/ 2>/dev/null || echo "No applications directory"

# Development workflow
dev-test:
    @echo "Testing development API..."
    @curl -s http://localhost:8000/ | head -c 50 || echo "API not responding"
