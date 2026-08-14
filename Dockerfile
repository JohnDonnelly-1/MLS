# Use official Python runtime as base image
FROM python:3.14-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY Pipfile ./

# Install Python dependencies directly with pip
# Extract package names from Pipfile and install with pip
RUN pip install --no-cache-dir \
    pytz \
    python-slugify \
    argon2-cffi \
    whitenoise \
    redis \
    hiredis \
    "uvicorn[standard]" \
    channels \
    django-environ \
    django-model-utils \
    django-allauth \
    django-crispy-forms \
    django-redis \
    django-crum \
    django-treebeard \
    django-debug-toolbar \
    django-extensions \
    gunicorn \
    Pillow \
    Twisted \
    "Django>=4.2" \
    djlint \
    bleach

# Copy project files
COPY . .

# Create directory for static files
RUN mkdir -p /app/staticfiles

# Copy and set permissions for entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
