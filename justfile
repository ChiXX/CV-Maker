# CV-Maker Project Commands

# Default recipe (run when you just type 'just')
default:
    @just --list

# Development Environment
dev-build:
    docker-compose -f docker-compose.dev.yml build --no-cache

dev-up:
    docker-compose -f docker-compose.dev.yml up api postgres

dev-ui:
    docker-compose -f docker-compose.dev.yml up frontend

dev-down:
    docker-compose -f docker-compose.dev.yml down api postgres

dev-ui-down:
    docker-compose -f docker-compose.dev.yml down frontend

# Production Deployment
deploy-build:
    docker-compose -f docker-compose.lightweight.yml build --no-cache

deploy-up:
    docker-compose -f docker-compose.lightweight.yml up -d

deploy-down:
    docker-compose -f docker-compose.lightweight.yml down

# Cleanup commands
dev-clean:
    docker-compose -f docker-compose.dev.yml down -v
    docker system prune -f

deploy-clean:
    docker-compose -f docker-compose.lightweight.yml down -v
    docker system prune -f

clean-all:
    docker-compose -f docker-compose.dev.yml down -v
    docker-compose -f docker-compose.lightweight.yml down -v
    docker system prune -a -f


