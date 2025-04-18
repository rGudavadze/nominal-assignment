#!/bin/sh
set -e

echo "Check postgres service availability"
python ~/check_service.py --service-name "postgres" --ip "pgdb" --port "5432"

echo "Apply database migrations"
cd /opt && alembic upgrade head

echo "Running app"
cd /opt/app && uvicorn main:app --host 0.0.0.0 --port 8000

exec "$@"
