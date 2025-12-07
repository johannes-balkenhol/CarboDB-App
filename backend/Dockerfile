# syntax=docker/dockerfile:1
FROM mambaorg/micromamba:1.5.8
USER root
WORKDIR /srv/app

# Install conda requirements first (cache-friendly)
COPY backend/requirements.txt /tmp/conda-requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Channels per your README
RUN micromamba config append channels defaults && \
    micromamba config append channels conda-forge && \
    micromamba config append channels bioconda && \
    micromamba config append channels anaconda && \
    micromamba install -y -n base -f /tmp/conda-requirements.txt && \
    micromamba clean --all --yes

# Gunicorn for production serving (pip if not in conda reqs)
RUN micromamba run -n base python -m pip install --no-cache-dir gunicorn

# Copy the WHOLE repo so /srv/app/backend is a proper package
COPY . /srv/app

# Ensure Python sees the repo root
ENV PYTHONPATH=/srv/app

# Tiny smart launcher: prefer create_app(), else app, else flask run
RUN cat > /usr/local/bin/start-backend.sh <<'SH' && chmod +x /usr/local/bin/start-backend.sh
#!/usr/bin/env bash
set -e

# 1) create_app() factory?
if micromamba run -n base python - <<'PY'
import importlib, inspect, sys
m = importlib.import_module("backend.app")
sys.exit(0 if hasattr(m, "create_app") and inspect.isfunction(m.create_app) else 1)
PY
then
  exec micromamba run -n base gunicorn -w 2 -b 0.0.0.0:8000 "backend.app:create_app()"
fi

# 2) global app?
if micromamba run -n base python - <<'PY'
import importlib, sys
m = importlib.import_module("backend.app")
sys.exit(0 if getattr(m, "app", None) is not None else 1)
PY
then
  exec micromamba run -n base gunicorn -w 2 -b 0.0.0.0:8000 backend.app:app
fi

# 3) fallback dev server
export FLASK_APP=backend.app
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=8000
exec micromamba run -n base python -m flask run
SH

EXPOSE 8000
CMD ["/usr/local/bin/start-backend.sh"]
