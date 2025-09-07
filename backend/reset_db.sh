#!/bin/bash

# ---------------------------
# CONFIGURATION
# ---------------------------
DB_NAME="nanopore"                                   # Your database name
DB_USER="maquiz"                                     # Your PostgreSQL user
PROJECT_DIR="/home/maquiz/Documents/FINAL_PROJECTS/dream/backend"  # Django project path
VENV_DIR="$PROJECT_DIR/venv-dream"                  # Virtualenv path

# ---------------------------
# TERMINATE EXISTING CONNECTIONS
# ---------------------------
echo "Terminating connections to $DB_NAME..."
psql -U $DB_USER -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$DB_NAME';"

# ---------------------------
# DROP AND CREATE DATABASE
# ---------------------------
echo "Dropping database $DB_NAME if exists..."
psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

echo "Creating new database $DB_NAME..."
psql -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"

# ---------------------------
# ACTIVATE VIRTUAL ENVIRONMENT
# ---------------------------
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# ---------------------------
# APPLY MIGRATIONS
# ---------------------------
cd $PROJECT_DIR
echo "Applying migrations..."
python manage.py migrate

# ---------------------------
# CREATE SUPERUSER
# ---------------------------
echo "Creating superuser..."
python manage.py createsuperuser

# ---------------------------
# FINISHED
# ---------------------------
echo "Database reset complete! You now have a fresh $DB_NAME database with all migrations applied."
