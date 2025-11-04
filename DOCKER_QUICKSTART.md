# Docker Quick Start

## Start Development (3 Commands)

```bash
# 1. Build and start everything
docker-compose up -d --build

# 2. Watch logs (optional)
docker-compose logs -f web

# 3. Open browser
# http://localhost:8000
# Admin: http://localhost:8000/admin (admin/admin)
```

## Or Use Make (Even Easier)

```bash
# Start everything
make up-build

# View logs
make logs-web

# Open: http://localhost:8000
```

## Common Tasks

```bash
# Run migrations
make migrate
# OR
docker-compose exec web python manage.py migrate

# Run tests
make test-mls
# OR
docker-compose exec web python manage.py test mls_core

# Access Django shell
make shell
# OR
docker-compose exec web python manage.py shell

# Stop everything
make down
# OR
docker-compose down
```

## Live Editing

Just edit your files - changes auto-reload! ✨

The entire `/mls` directory is mounted, so any changes you make are immediately reflected in the container.

## Troubleshooting

```bash
# Restart if something breaks
make restart

# View logs if errors occur
make logs

# Complete reset (nuclear option)
make reset
```

## Key Features

✅ **Live code editing** - Edit files, see changes instantly
✅ **PostgreSQL database** - Production-like environment
✅ **Redis cache** - Full stack development
✅ **Auto migrations** - Runs on startup
✅ **Auto superuser** - admin/admin created automatically
✅ **Volume mounts** - Your code, live synced

## Ports

- Django: **8000**
- PostgreSQL: **5432**
- Redis: **6379**

## Make Commands Cheatsheet

```bash
make help           # Show all commands
make up-build       # Build and start
make down           # Stop everything
make restart        # Restart services
make logs           # View all logs
make logs-web       # View Django logs
make shell          # Django shell
make bash           # Container bash
make db-shell       # PostgreSQL shell
make test           # Run all tests
make test-mls       # Run MLS tests
make migrate        # Run migrations
make makemigrations # Create migrations
make superuser      # Create admin user
make clean          # Remove everything
make reset          # Complete reset
```

## Without Make

```bash
docker-compose up -d --build         # Start
docker-compose down                  # Stop
docker-compose logs -f web           # Logs
docker-compose exec web python manage.py shell    # Shell
docker-compose exec web python manage.py test     # Test
docker-compose exec web python manage.py migrate  # Migrate
docker-compose restart web           # Restart
```

## URLs

- **Application**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **Credentials**: admin / admin

## Next Steps

1. Start containers: `make up-build`
2. Edit code in your editor
3. See changes at http://localhost:8000
4. Run tests: `make test-mls`
5. Have fun! 🚀

See **DOCKER_README.md** for complete documentation.
