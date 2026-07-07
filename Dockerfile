FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for chrony client
RUN apt-get update && apt-get install -y --no-install-recommends \
    chrony \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY ticc-dash.py ./
COPY static/ ./static/

# Install Python dependencies
RUN pip install --no-cache-dir flask

# Expose dashboard port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

# Run the dashboard
CMD ["python3", "ticc-dash.py"]
