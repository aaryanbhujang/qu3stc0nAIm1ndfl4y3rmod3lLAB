FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libhdf5-dev \
    libjpeg-dev \
    curl \
    zlib1g-dev \
    e2fsprogs \
    && rm -rf /var/lib/apt/lists/*

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

EXPOSE 8000
ENV PORT=8000 FLASK_ENV=production
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "app:app"]
