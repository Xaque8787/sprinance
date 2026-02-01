FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --user -r /tmp/requirements.txt

FROM python:3.11-slim AS production

RUN apt-get update && apt-get install -y \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 app

WORKDIR /app

COPY --from=builder /root/.local /home/app/.local

COPY app/ /app/app/
COPY migrations/ /app/migrations/
COPY run_migrations.py /app/
COPY docker-entrypoint.sh /app/
COPY .dockerversion /app/

RUN mkdir -p data/scheduler \
             data/backups \
             data/reports/daily_report \
             data/reports/tip_report \
             data/logs \
             migrations/old && \
    chown -R app:app /app && \
    chmod -R 755 data && \
    chmod +x docker-entrypoint.sh

USER app

ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///data/database.db
ENV TZ=America/Los_Angeles

EXPOSE 5710

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5710/ || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "1", "-b", "0.0.0.0:5710", "--access-logfile", "-", "--error-logfile", "-"]
