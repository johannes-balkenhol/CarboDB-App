# CarboxyPred Backend Dockerfile
FROM mambaorg/micromamba:1.5.1

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER

# Create environment with specific versions matching HPC
RUN micromamba install -y -n base -c conda-forge \
    python=3.11 \
    numpy=1.26.4 \
    pandas=2.2.3 \
    scikit-learn=1.5.2 \
    scipy=1.14.1 \
    joblib=1.4.2 \
    flask=3.0.0 \
    flask-cors=4.0.0 \
    apscheduler=3.10.4 \
    gunicorn=21.2.0 \
    && micromamba clean --all --yes

# Set working directory
WORKDIR /srv/app

# Copy backend code
COPY --chown=$MAMBA_USER:$MAMBA_USER backend/ ./backend/

# Copy models directory
COPY --chown=$MAMBA_USER:$MAMBA_USER models/ ./backend/ml_models/

# Create necessary directories
RUN mkdir -p /app/database_files /tmp/uploads /tmp/prosite

# Set environment
ENV FLASK_APP=backend.main
ENV FLASK_ENV=development
ENV PYTHONPATH=/srv/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with micromamba
ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
CMD ["micromamba", "run", "-n", "base", "python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8000"]
