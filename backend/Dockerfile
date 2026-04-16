# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
# Note: oracledb python-oracledb 2.0+ uses Thin mode by default (no Oracle Client needed)
# If you need Thick mode, install Oracle Instant Client separately
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set PYTHONPATH so app module is resolvable
ENV PYTHONPATH=/app

# Make startup script executable
RUN chmod +x /app/startup.sh

# Expose the application port
EXPOSE 8000

# Run the startup script (waits for DBs, initializes schema, then starts uvicorn)
CMD ["/bin/bash", "/app/startup.sh"]
