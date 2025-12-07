# syntax=docker/dockerfile:1
FROM mambaorg/micromamba:1.5.8
USER root
WORKDIR /srv/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential libcairo2-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/conda-requirements.txt

RUN micromamba config append channels defaults && \
    micromamba config append channels conda-forge && \
    micromamba config append channels bioconda && \
    micromamba config append channels anaconda && \
    micromamba config set channel_priority flexible && \
    micromamba config set download_timeout 1200

RUN micromamba install -y -n base python=3.12 pip setuptools wheel && \
    micromamba clean --all --yes

RUN micromamba install -y -n base flask=3.0.3 flask-cors=5.0.0 && \
    micromamba clean --all --yes

RUN micromamba install -y -n base biopython=1.78 && \
    micromamba clean --all --yes

RUN micromamba install -y -n base numpy pandas matplotlib && \
    micromamba clean --all --yes

RUN micromamba install -y -n base apscheduler requests pytest && \
    micromamba clean --all --yes

RUN micromamba install -y -n base py_fasta_validator -c bioconda && \
    micromamba clean --all --yes

RUN (micromamba install -y -n base pyhmmer -c bioconda || true) && \
    micromamba clean --all --yes

# Install plotly and other packages via pip
RUN micromamba run -n base pip install --no-cache-dir \
    reportlab werkzeug gunicorn plotly

COPY . /srv/app
ENV PYTHONPATH=/srv/app

RUN cat > /usr/local/bin/start-backend.sh <<'SH' && chmod +x /usr/local/bin/start-backend.sh
#!/usr/bin/env bash
set -e
if [ -f "/srv/app/backend/main.py" ]; then
  cd /srv/app/backend
  exec micromamba run -n base python main.py
fi
export FLASK_APP=backend.main
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=8000
cd /srv/app/backend
exec micromamba run -n base python -m flask run
SH

EXPOSE 8000
CMD ["/usr/local/bin/start-backend.sh"]
