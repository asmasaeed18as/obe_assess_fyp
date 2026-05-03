#!/usr/bin/env bash
# build.sh — Render build script

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create admin user (idempotent — won't fail if user already exists)
python manage.py create_admin \
  --email aima@gmail.com \
  --password aima@123 \
  --first-name Admin \
  --last-name User
