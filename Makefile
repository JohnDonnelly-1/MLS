.PHONY: help build up down restart logs shell test migrate makemigrations superuser clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services started! Django is running at http://localhost:8000"
	@echo "Admin interface: http://localhost:8000/admin (admin/admin)"

up-build: ## Build and start all services
	docker-compose up -d --build
	@echo "Services started! Django is running at http://localhost:8000"

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

restart-web: ## Restart web service only
	docker-compose restart web

logs: ## View logs from all services
	docker-compose logs -f

logs-web: ## View logs from web service
	docker-compose logs -f web

logs-db: ## View logs from database service
	docker-compose logs -f db

shell: ## Access Django shell
	docker-compose exec web python manage.py shell

bash: ## Access web container bash shell
	docker-compose exec web bash

db-shell: ## Access PostgreSQL shell
	docker-compose exec db psql -U mls_user -d mls_db

test: ## Run all tests
	docker-compose exec web python manage.py test

test-mls: ## Run MLS Core tests
	docker-compose exec web python manage.py test mls_core

test-verbose: ## Run tests with verbose output
	docker-compose exec web python manage.py test --verbosity=2

migrate: ## Run database migrations
	docker-compose exec web python manage.py migrate

makemigrations: ## Create new migrations
	docker-compose exec web python manage.py makemigrations

superuser: ## Create a superuser
	docker-compose exec web python manage.py createsuperuser

collectstatic: ## Collect static files
	docker-compose exec web python manage.py collectstatic --noinput

clean: ## Remove all containers, volumes, and images
	docker-compose down -v
	docker system prune -f

reset: ## Complete reset (delete everything and rebuild)
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d
	@echo "System reset complete!"

ps: ## Show running containers
	docker-compose ps

exec-web: ## Execute command in web container (usage: make exec-web CMD="python manage.py ...")
	docker-compose exec web $(CMD)
