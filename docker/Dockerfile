FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
COPY requirements/ /app/requirements/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary folders
RUN mkdir -p storage/webtoons storage/panels storage/temp logs

# Ensure the docker-settings.py module is importable
RUN ln -sf /app/docker/docker-settings.py /app/docker_settings.py

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
