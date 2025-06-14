FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    FLASK_ENV=production

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
       python3-dev \
       git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script first and make it executable
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Copy application code
COPY . .

# Create a non-root user and switch to it
RUN groupadd -r weatherapp && \
    useradd -r -g weatherapp weatherapp && \
    chown -R weatherapp:weatherapp /app

USER weatherapp

# Expose the port the app runs on
EXPOSE ${PORT}

# Use the entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
