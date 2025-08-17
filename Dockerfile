FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p data logs browser_data && \
    chmod +x app.py

# Expose port (if needed for health checks)
EXPOSE 8080

# Command to run the application
CMD ["python", "app.py", "continuous"]
