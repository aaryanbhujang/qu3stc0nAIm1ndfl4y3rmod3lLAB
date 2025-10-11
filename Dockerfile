FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libhdf5-dev \
    libjpeg-dev \
    curl \
    zlib1g-dev \
    e2fsprogs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user
RUN useradd -m -u 1000 ctfuser

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make flag file read-only and immutable, owned by root
RUN chown root:root flag.txt && \
    chmod 444 flag.txt && \
    chattr +i flag.txt 2>/dev/null || true

# Switch to non-root user
USER ctfuser

EXPOSE $PORT
ENV FLASK_ENV=production
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --worker-class sync app:app
