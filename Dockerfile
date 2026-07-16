# Use official Python runtime as a parent image
FROM python:3.11-slim

# Install minimal dependencies
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download and install Google Chrome
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && \
    apt-get install -y /tmp/chrome.deb || true && \
    rm /tmp/chrome.deb && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download chromedriver to avoid timeout on startup
RUN python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()" || true

# Copy application code
COPY main.py .

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV K_SERVICE=lamudi-scraper
ENV PYTHONUNBUFFERED=1

# Run the application directly with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
