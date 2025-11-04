#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

echo "Creating superuser if it doesn't exist..."
python manage.py shell <<'PYEND'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created successfully: username=admin, password=admin')
else:
    print('Superuser already exists: username=admin')
PYEND

echo "============================================"
echo "Setup complete!"
echo "Admin login: username=admin, password=admin"
echo "============================================"

echo "Starting Django development server..."
exec "$@"
