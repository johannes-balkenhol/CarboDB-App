#!/bin/bash
set -u
BACKEND_DIR="$HOME/Projects_shared/CarboDB_v3"
FRONTEND_DIR="$HOME/Projects_shared/CarboDB-App-v2/frontend"

case "${1:-restart}" in
  stop|restart)
    pkill -f "uvicorn webapp.app.main" 2>/dev/null && echo "killed uvicorn"
    pkill -f "vite" 2>/dev/null && echo "killed vite"
    sleep 2
    [ "$1" = "stop" ] && exit 0 ;;
esac

cd "$BACKEND_DIR"
mkdir -p webapp/logs
DB_PATH=data/primary/carbodb.sqlite \
PFAM_HMM=data/dbs/pfam/Pfam-A.hmm \
MODELS_DIR=webapp/models \
JOBS_DIR=webapp/jobs \
ESM2_DEVICE=cpu \
PYTHONPATH=. \
  nohup uvicorn webapp.app.main:app --host 0.0.0.0 --port 8090 \
  > webapp/logs/webapp.log 2>&1 &
echo "started uvicorn (pid $!)"
sleep 5

cd "$FRONTEND_DIR"
nohup npm run dev > /tmp/vite.log 2>&1 &
echo "started vite (pid $!)"
sleep 8

echo ""
echo "=== Status ==="
pgrep -fa "uvicorn webapp.app.main" || echo "uvicorn NOT running"
pgrep -fa "vite" | grep -v grep || echo "vite NOT running"
echo ""
echo "Backend: http://132.187.22.206:8090"
echo "Frontend: http://132.187.22.206:5173/analysis"
