FROM mambaorg/micromamba:1.5.1

USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER

RUN micromamba install -y -n base -c conda-forge \
    python=3.12 \
    numpy=2.1 \
    pandas=2.2 \
    scikit-learn=1.6 \
    scipy=1.14 \
    joblib=1.4 \
    flask=3.0 \
    flask-cors=4.0 \
    apscheduler=3.10 \
    gunicorn=21.2 \
    && micromamba clean --all --yes

WORKDIR /srv/app

COPY --chown=$MAMBA_USER:$MAMBA_USER backend/ ./backend/
COPY --chown=$MAMBA_USER:$MAMBA_USER backend/ml_models/ ./backend/ml_models/

USER root
RUN mkdir -p /app/database_files /tmp/uploads /tmp/prosite && chown -R $MAMBA_USER:$MAMBA_USER /app /tmp/uploads /tmp/prosite
USER $MAMBA_USER

ENV FLASK_APP=backend.main
ENV FLASK_ENV=development
ENV PYTHONPATH=/srv/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
CMD ["micromamba", "run", "-n", "base", "python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8000"]
