FROM python:3.11-slim

# chronyc client binary — talks to the host (or remote) Chrony daemon.
# No sudo is needed: the app uses plain `chronyc`, and read-only commands
# are permitted over the local unix socket.
RUN apt-get update && apt-get install -y --no-install-recommends \
        chrony \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application code + static assets.
COPY chronoguard.py ./
COPY templates/ ./templates/
COPY static/ ./static/

EXPOSE 5000

# docker-compose mounts the host control socket so chronyc can query the
# real daemon; set CHRONY_HOST / CHRONY_PORT to target a remote one instead.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "chronoguard:app"]
