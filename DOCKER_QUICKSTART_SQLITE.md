# Docker Quick Start (SQLite Edition)

## Start Development (2 Commands)

```bash
# 1. Build and start everything
docker-compose up -d --build

# 2. Open browser
# http://localhost:8000
# Admin: http://localhost:8000/admin (admin/admin)
```

## What's Included

✅ **Django** - Your application (SQLite database)
✅ **Redis** - For caching and channels
✅ **Live Editing** - Edit code, see changes instantly

## Common Tasks

```bash
# View logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python manage.py migrate

# Run tests
docker-compose exec web python manage.py test mls_core

# Access Django shell
docker-compose exec web python manage.py shell

# Stop everything
docker-compose down
```

## Live Editing

Just edit your files - changes auto-reload! ✨

Your entire project is mounted, so any code changes are immediately visible.

## Database

The SQLite database (`db.sqlite3`) is stored in the mounted volume, so:
- ✅ Changes persist when you restart containers
- ✅ You can access it from your host machine
- ✅ You can commit it to git if needed
- ✅ No separate database container needed

## Troubleshooting

```bash
# Restart if something breaks
docker-compose restart web

# View logs if errors occur
docker-compose logs -f web

# Complete reset
docker-compose down
rm db.sqlite3  # Delete database if needed
docker-compose up -d --build
```

## Key Commands

```bash
# Start
docker-compose up -d --build

# Stop
docker-compose down

# Logs
docker-compose logs -f web

# Shell
docker-compose exec web python manage.py shell

# Bash
docker-compose exec web bash

# Test
docker-compose exec web python manage.py test

# Migrate
docker-compose exec web python manage.py migrate
```

## Services & Ports

- **Django**: http://localhost:8000
- **Redis**: localhost:6379

## URLs

- **Application**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **Credentials**: admin / admin

## Advantages of SQLite Setup

✅ **Simpler** - No PostgreSQL container needed
✅ **Faster startup** - One less service to wait for
✅ **Portable** - Database file can be easily copied
✅ **Less memory** - Only 2 containers instead of 3
✅ **Good for development** - Perfect for local testing

## When to Use PostgreSQL Instead

Use PostgreSQL if:
- You need production-like environment
- Testing PostgreSQL-specific features
- Working with large datasets (>100MB)
- Need concurrent write access
- Preparing for production deployment

For most development work, SQLite is perfect! 🚀

## Next Steps

```bash
# 1. Start containers
docker-compose up -d --build

# 2. Open browser
# http://localhost:8000

# 3. Start coding
# Files auto-sync!

# 4. View logs
docker-compose logs -f web
```

That's it! Simple and lightweight. 🎉
