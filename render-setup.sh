#!/bin/bash
# Render Deployment Helper Script
# Run this before pushing to generate required credentials

set -e

echo "================================================"
echo "OBE Assessment Platform - Render Setup Helper"
echo "================================================"
echo ""

# Check if django secret key is provided
if [ -z "$1" ]; then
    echo "✅ Step 1: Generate Django SECRET_KEY"
    echo "Run this command to generate a strong secret key:"
    echo ""
    echo "python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    echo ""
else
    SECRET_KEY=$1
    echo "✅ SECRET_KEY provided: ${SECRET_KEY:0:20}..."
fi

echo ""
echo "================================================"
echo "Deployment Checklist"
echo "================================================"
echo ""

# Checklist items
checklist=(
    "[ ] Groq API key obtained from https://console.groq.com"
    "[ ] GitHub repository is public or Render has access"
    "[ ] render.yaml file is present in repository root"
    "[ ] .env.production file is ready with all secrets"
    "[ ] PostgreSQL database is provisioned on Render"
    "[ ] All three services (backend, llm, frontend) exist on Render"
    "[ ] Environment variables set on each Render service"
    "[ ] SSH key added to Render account (optional but recommended)"
)

for item in "${checklist[@]}"; do
    echo "$item"
done

echo ""
echo "================================================"
echo "Service URLs Pattern"
echo "================================================"
echo ""
echo "Backend:    https://<PROJECT_NAME>-backend.onrender.com"
echo "LLM:        https://<PROJECT_NAME>-llm.onrender.com"
echo "Frontend:   https://<PROJECT_NAME>-frontend.onrender.com"
echo ""

echo "================================================"
echo "Quick Links"
echo "================================================"
echo ""
echo "Render Dashboard:     https://dashboard.render.com"
echo "Groq Console:         https://console.groq.com"
echo "Deployment Guide:     See RENDER_DEPLOYMENT.md"
echo ""

echo "✅ Setup helper complete. Ready for deployment!"
