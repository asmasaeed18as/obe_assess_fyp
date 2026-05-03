#!/usr/bin/env bash
# build.sh — Render build script

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create admin user from environment variables (idempotent — won't fail if user already exists)
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
  python manage.py create_admin \
    --email "$ADMIN_EMAIL" \
    --password "$ADMIN_PASSWORD" \
    --first-name "${ADMIN_FIRST_NAME:-Admin}" \
    --last-name "${ADMIN_LAST_NAME:-User}"
else
  echo "Skipping admin user creation. Set ADMIN_EMAIL and ADMIN_PASSWORD environment variables."
fi
