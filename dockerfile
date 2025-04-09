FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies (without Chrome and ChromeDriver)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn requests

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs backups info/maps info/profile

# Create a non-root user to run the application
RUN useradd -m travianuser
RUN chown -R travianuser:travianuser /app
USER travianuser

# Default command to run the web application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "web.app:create_app()"]