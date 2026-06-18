#!/bin/bash
set -u

# === Paths ===
APP_DIR="/storage/users/projects/CarboDB-App-v2"
BACKEND_REPO_DIR="/storage/users/job37yv/Projects/CarboDB_v3"
FRONTEND_DIR="${APP_DIR}/frontend"
LOG_DIR="${APP_DIR}/logs"

# === Ports / Redis ===
BACKEND_HOST="0.0.0.0"
BACKEND_PORT="8091"
FRONTEND_PORT="5174"
REDIS_HOST="127.0.0.1"
REDIS_PORT="6379"
REDIS_DB="0"
REDIS_URL="redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}"
PREDICT_QUEUE_NAME="predict"

# === Backend env ===
export DB_PATH="${BACKEND_REPO_DIR}/data/primary/carbodb.sqlite"
export PFAM_HMM="${BACKEND_REPO_DIR}/data/dbs/pfam/Pfam-A.hmm"
export MODELS_DIR="${APP_DIR}/models"
export JOBS_DIR="${APP_DIR}/jobs"
export ESM2_DEVICE="cpu"
export PYTHONPATH="${APP_DIR}:${BACKEND_REPO_DIR}"
export REDIS_URL="${REDIS_URL}"
export PREDICT_QUEUE_NAME="${PREDICT_QUEUE_NAME}"
export PREDICT_JOB_TIMEOUT="300"
export PREDICT_RESULT_TTL="3600"
export PREDICT_FAILURE_TTL="86400"

export BATCH_QUEUE_NAME="batch"
export BATCH_JOB_TIMEOUT="3600"
export BATCH_RESULT_TTL="86400"
export BATCH_FAILURE_TTL="86400"

# === Frontend env used by vite.config.js ===
export BACKEND_PORT="${BACKEND_PORT}"
export FRONTEND_PORT="${FRONTEND_PORT}"
export VITE_BACKEND_PORT="${BACKEND_PORT}"
export VITE_FRONTEND_PORT="${FRONTEND_PORT}"

mkdir -p "${LOG_DIR}" "${JOBS_DIR}"

start_redis() {
  if ! command -v redis-server >/dev/null 2>&1; then
    echo "ERROR: redis-server not found."
    echo "Install it first, for example:"
    echo "  conda install -c conda-forge redis-server"
    exit 1
  fi

  if command -v redis-cli >/dev/null 2>&1 && redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping >/dev/null 2>&1; then
    echo "Redis already running on ${REDIS_HOST}:${REDIS_PORT}"
    return
  fi

  echo "Starting Redis on ${REDIS_HOST}:${REDIS_PORT}..."
  nohup redis-server \
    --bind "${REDIS_HOST}" \
    --port "${REDIS_PORT}" \
    --daemonize no \
    > "${LOG_DIR}/redis.log" 2>&1 &

  echo $! > "${LOG_DIR}/redis.pid"
  sleep 2

  if command -v redis-cli >/dev/null 2>&1; then
    redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping >/dev/null 2>&1 \
      && echo "Redis started" \
      || echo "WARNING: Redis may not have started. Check ${LOG_DIR}/redis.log"
  else
    echo "Redis started; redis-cli not available, skipping ping check"
  fi
}

start_worker() {
  if ! command -v rq >/dev/null 2>&1; then
    echo "ERROR: rq command not found."
    echo "Install requirements first:"
    echo "  pip install -r requirements.txt"
    exit 1
  fi

  echo "Starting RQ worker for queues '${PREDICT_QUEUE_NAME}' and '${BATCH_QUEUE_NAME}'..."
  cd "${APP_DIR}" || exit 1

  nohup rq worker "${PREDICT_QUEUE_NAME}" "${BATCH_QUEUE_NAME}" --url "${REDIS_URL}" \
    > "${LOG_DIR}/rq_worker.log" 2>&1 &

  echo $! > "${LOG_DIR}/rq_worker.pid"
  echo "started RQ worker (pid $!)"
}

start_backend() {
  echo "Starting FastAPI backend on port ${BACKEND_PORT}..."
  cd "${APP_DIR}" || exit 1

  nohup uvicorn app.main:app \
    --host "${BACKEND_HOST}" \
    --port "${BACKEND_PORT}" \
    > "${LOG_DIR}/webapp.log" 2>&1 &

  echo $! > "${LOG_DIR}/backend.pid"
  echo "started uvicorn (pid $!)"
}

start_frontend() {
  echo "Starting Vite frontend on port ${FRONTEND_PORT}..."
  cd "${FRONTEND_DIR}" || exit 1

  nohup npm run dev \
    > "${LOG_DIR}/vite.log" 2>&1 &

  echo $! > "${LOG_DIR}/vite.pid"
  echo "started vite (pid $!)"
}

stop_all() {
  echo "Stopping CarboDB app processes..."

  pkill -f "uvicorn app.main:app" 2>/dev/null && echo "killed uvicorn" || true
  pkill -f "rq worker ${PREDICT_QUEUE_NAME} ${BATCH_QUEUE_NAME}" 2>/dev/null && echo "killed RQ worker" || true
  pkill -f "vite" 2>/dev/null && echo "killed vite" || true

  # Only stop Redis if this script started it and pid file exists
  if [ -f "${LOG_DIR}/redis.pid" ]; then
    REDIS_PID=$(cat "${LOG_DIR}/redis.pid")
    if kill -0 "${REDIS_PID}" 2>/dev/null; then
      kill "${REDIS_PID}" 2>/dev/null && echo "killed Redis started by script"
    fi
    rm -f "${LOG_DIR}/redis.pid"
  else
    echo "No script-managed Redis pid file found; leaving Redis alone"
  fi

  rm -f "${LOG_DIR}/backend.pid" "${LOG_DIR}/rq_worker.pid" "${LOG_DIR}/vite.pid"
}

status_all() {
  echo ""
  echo "=== Status ==="

  echo ""
  echo "[Redis]"
  if command -v redis-cli >/dev/null 2>&1 && redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping >/dev/null 2>&1; then
    echo "Redis running at ${REDIS_URL}"
  else
    echo "Redis NOT reachable at ${REDIS_URL}"
  fi

  echo ""
  echo "[RQ worker]"
  pgrep -fa "rq worker ${PREDICT_QUEUE_NAME}" || echo "RQ worker NOT running"

  echo ""
  echo "[Backend]"
  pgrep -fa "uvicorn app.main:app" || echo "uvicorn NOT running"

  echo ""
  echo "[Frontend]"
  pgrep -fa "vite" | grep -v grep || echo "vite NOT running"

  echo ""
  echo "Backend:  http://132.187.22.206:${BACKEND_PORT}"
  echo "Frontend: http://132.187.22.206:${FRONTEND_PORT}/analysis"
  echo ""
  echo "Logs:"
  echo "  Redis:   ${LOG_DIR}/redis.log"
  echo "  Worker:  ${LOG_DIR}/rq_worker.log"
  echo "  Backend: ${LOG_DIR}/webapp.log"
  echo "  Vite:    ${LOG_DIR}/vite.log"
}

case "${1:-restart}" in
  start)
    start_redis
    start_worker
    start_backend
    sleep 5
    start_frontend
    sleep 3
    status_all
    ;;

  stop)
    stop_all
    ;;

  restart)
    stop_all
    sleep 2
    start_redis
    start_worker
    start_backend
    sleep 5
    start_frontend
    sleep 3
    status_all
    ;;

  status)
    status_all
    ;;

  logs)
    echo "Backend log:"
    tail -n 80 "${LOG_DIR}/webapp.log"
    echo ""
    echo "RQ worker log:"
    tail -n 80 "${LOG_DIR}/rq_worker.log"
    echo ""
    echo "Redis log:"
    tail -n 40 "${LOG_DIR}/redis.log"
    echo ""
    echo "Vite log:"
    tail -n 40 "${LOG_DIR}/vite.log"
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status|logs}"
    exit 1
    ;;
esac