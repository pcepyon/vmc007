# Use official Python runtime as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    file \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY backend/requirements.txt /app/backend/requirements.txt
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy application code
COPY . /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Collect static files
RUN cd backend && python manage.py collectstatic --noinput

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Run migrations and start server
CMD cd backend && python manage.py migrate --noinput && \
    gunicorn data_ingestion.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
