# ================================
# Builder Stage - For compilation
# ================================
FROM python:3.12-slim as builder

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install minimal build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies to virtual environment
RUN uv sync --frozen --no-install-project --no-dev

# ================================
# Runtime Stage - Minimal final image
# ================================
FROM python:3.12-slim as runtime

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Install minimal runtime dependencies
# Remove TeX Live - use lightweight PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install runtime Python packages (only what's needed)
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    sqlalchemy \
    psycopg2-binary \
    python-multipart \
    pydantic \
    openai \
    python-dotenv \
    beautifulsoup4 \
    requests \
    httpx \
    fpdf

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code (exclude heavy files)
COPY app.py cl_generator.py cv_generator.py jd_generator.py database.py models.py prompts.py ./
COPY latex_cl/ ./latex_cl/
COPY latex_cv/ ./latex_cv/

# Create non-root user
RUN groupadd -g 1001 app \
    && useradd -u 1001 -g app -m -s /bin/bash app \
    && chown -R app:app /app

USER app

EXPOSE 8000

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Run with optimized settings for low memory
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--loop", "asyncio"]
