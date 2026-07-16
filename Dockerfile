# Use official Python runtime as a parent image
FROM python:3.11-slim

# Install dependencies for Chromium/Chrome
RUN apt-get update && apt-get install -y \
    chromium-browser \
    chromium-chromedriver \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV K_SERVICE=lamudi-scraper

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-u", "main.py"]
