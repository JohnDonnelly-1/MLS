# Docker Setup for MLS Django Application

This Docker setup allows you to run the MLS Django application in containers with live code editing.

## Quick Start

### 1. Start the Application

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

The application will be available at: http://localhost:8000

**Default admin credentials:**
- Username: `admin`
- Password: `admin`

### 2. Stop the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes database data)
docker-compose down -v
```

## What's Included

The Docker Compose setup includes:

- **web** - Django application (port 8000)
- **db** - PostgreSQL database (port 5432)
- **redis** - Redis cache (port 6379)

## Live Editing

The entire project directory is mounted as a volume, so you can edit code on your host machine and see changes immediately:

```yaml
volumes:
  - .:/app  # Live code sync
```

**Changes that auto-reload:**
- Python files (*.py)
- Templates (*.html)
- Static files (after collectstatic)

**Changes that require restart:**
- Dependencies (Pipfile)
- Settings changes (sometimes)
- Database migrations

To restart after changes:
```bash
docker-compose restart web
```

## Common Commands

### Django Management Commands

```bash
# Run any Django management command
docker-compose exec web python manage.py <command>

# Examples:
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py test
```

### Database Commands

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U mls_user -d mls_db

# Create database backup
docker-compose exec db pg_dump -U mls_user mls_db > backup.sql

# Restore database backup
docker-compose exec -T db psql -U mls_user -d mls_db < backup.sql

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d db
docker-compose exec web python manage.py migrate
```

### View Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs db
docker-compose logs redis

# Follow logs (live tail)
docker-compose logs -f web

# View last 100 lines
docker-compose logs --tail=100 web
```

### Access Container Shell

```bash
# Django container shell
docker-compose exec web bash

# PostgreSQL container shell
docker-compose exec db bash

# Redis container shell
docker-compose exec redis sh
```

## Testing

### Run Tests

```bash
# Run all tests
docker-compose exec web python manage.py test

# Run specific app tests
docker-compose exec web python manage.py test mls_core

# Run specific test class
docker-compose exec web python manage.py test mls_core.tests.BasicMLSAccessTestCase

# Run with verbosity
docker-compose exec web python manage.py test mls_core --verbosity=2
```

### Run Tests with Coverage

```bash
# Install coverage first (if not in Pipfile)
docker-compose exec web pip install coverage

# Run tests with coverage
docker-compose exec web coverage run --source='.' manage.py test mls_core
docker-compose exec web coverage report
docker-compose exec web coverage html
```

## Development Workflow

### 1. Start Development

```bash
# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f web
```

### 2. Make Code Changes

Edit files on your host machine - changes auto-reload in the container.

### 3. Run Migrations (if models changed)

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### 4. Test Your Changes

```bash
docker-compose exec web python manage.py test
```

### 5. Access Django Shell (for debugging)

```bash
docker-compose exec web python manage.py shell
```

```python
# In shell:
from abac.models import Label, Security
from mls_core import MLSObject

# Test your code
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs web

# Check if ports are in use
# On Linux/Mac:
sudo lsof -i :8000
# On Windows:
netstat -ano | findstr :8000

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Database Connection Issues

```bash
# Check if database is running
docker-compose ps

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db

# Wait for database to be ready
docker-compose exec web python manage.py migrate
```

### Code Changes Not Reflecting

```bash
# Restart web service
docker-compose restart web

# If still not working, rebuild
docker-compose up -d --build
```

### Permission Issues (Linux)

```bash
# If you get permission errors on Linux:
sudo chown -R $USER:$USER .

# Or run containers with your user ID:
# Add to docker-compose.yml under 'web':
user: "${UID}:${GID}"

# Then export your UID/GID:
export UID=$(id -u)
export GID=$(id -g)
docker-compose up
```

### "pg_isready: command not found"

Update the Dockerfile to ensure postgresql-client is installed:
```dockerfile
RUN apt-get update && apt-get install -y postgresql-client
```

## Environment Variables

Environment variables are configured in `docker-compose.yml`. To customize:

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your values

3. Update `docker-compose.yml` to use `.env`:
```yaml
web:
  env_file:
    - .env
```

## Production Deployment

This Docker setup is for **development only**. For production:

1. **Change the command**:
```yaml
command: gunicorn mls.wsgi:application --bind 0.0.0.0:8000
```

2. **Use environment variables**:
```yaml
environment:
  - DEBUG=False
  - SECRET_KEY=${SECRET_KEY}
```

3. **Add nginx**:
```yaml
nginx:
  image: nginx:latest
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
  ports:
    - "80:80"
  depends_on:
    - web
```

4. **Use production database**:
```yaml
db:
  image: postgres:15
  volumes:
    - postgres_data:/var/lib/postgresql/data
  environment:
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # From env file
```

## Useful Docker Commands

```bash
# View running containers
docker-compose ps

# View resource usage
docker stats

# Remove stopped containers
docker-compose rm

# View images
docker images

# Remove unused images
docker image prune

# Remove everything (CAREFUL!)
docker system prune -a --volumes

# Rebuild specific service
docker-compose build web

# Scale services (run multiple instances)
docker-compose up -d --scale web=3
```

## Directory Structure

```
mls/
├── Dockerfile              # Django container definition
├── docker-compose.yml      # Multi-container orchestration
├── docker-entrypoint.sh    # Startup script
├── .dockerignore          # Files to exclude from image
├── .env.example           # Environment variable template
├── manage.py
├── Pipfile
├── Pipfile.lock
├── mls/                   # Django project
├── abac/                  # ABAC app
├── mls_core/              # MLS Core app
└── ...
```

## Tips

1. **Use .dockerignore**: Keeps your images small by excluding unnecessary files

2. **Named volumes**: Data persists across container restarts
```bash
# View volumes
docker volume ls

# Inspect volume
docker volume inspect mls_postgres_data
```

3. **Layer caching**: Put frequently changing code last in Dockerfile

4. **Multi-stage builds**: For smaller production images
```dockerfile
# Stage 1: Builder
FROM python:3.11 as builder
# Install dependencies

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
```

5. **Health checks**: Ensure services are ready
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready"]
  interval: 5s
```

## Summary

**To start development:**
```bash
docker-compose up -d
docker-compose logs -f web
```

**Access the app:**
- Django: http://localhost:8000
- Admin: http://localhost:8000/admin (admin/admin)

**Run tests:**
```bash
docker-compose exec web python manage.py test mls_core
```

**Stop everything:**
```bash
docker-compose down
```

**Complete reset:**
```bash
docker-compose down -v
docker-compose up -d --build
```

Happy coding! 🐳🚀
