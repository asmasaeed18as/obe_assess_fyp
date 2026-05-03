# Render Deployment Guide

This guide walks you through deploying the OBE Assessment Platform to Render with two services: Backend and Frontend.

## Prerequisites

- Render account ([render.com](https://render.com))
- GitHub repository with this code
- Groq API key ([console.groq.com](https://console.groq.com))
- PostgreSQL database (Render PostgreSQL or external)

## Architecture Overview

```
┌─────────────┐
│   Frontend  │  (Static Site - React/Vite)
│ React/Vite  │
└──────┬──────┘
       │ VITE_API_BASE_URL
       ▼
┌─────────────────────────────────┐
│  Django Backend + LLM Integration│  (Web Service - Python)
│  Port: 8000                     │
│  Endpoints: /api, /api/llm      │
└──────┬──────────────────────────┘
       │ 
       ▼
┌──────────────┐
│ PostgreSQL   │
│  Database    │
└──────────────┘
       │
       │ GROQ_API_KEY
       ▼
   Groq API
```

## Step 1: Create PostgreSQL Database

### Option A: Render PostgreSQL Database (Recommended)

1. Go to Render Dashboard → **New +** → **PostgreSQL**
2. Fill in:
   - **Name**: `obe-assess-db`
   - **Region**: Same as your services
   - **PostgreSQL Version**: 15
   - **Data Dog Monitoring**: No (unless needed)
3. Click **Create Database**
4. Copy the Internal Database URL (starts with `postgresql://`)
5. Save this for later use

### Option B: External PostgreSQL

If using an external provider, ensure you have a valid PostgreSQL connection string.

## Step 2: Deploy Django Backend

1. Go to Render Dashboard → **New +** → **Web Service**
2. Connect GitHub repository
3. Configure:
   - **Name**: `obe-assess-backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt && cd obe_assess && python manage.py migrate`
   - **Start Command**: `gunicorn obe_assess.wsgi:application --chdir obe_assess --bind 0.0.0.0:$PORT`
   - **Plan**: Starter (or appropriate)

4. **Add Environment Variables** (Settings → Environment):
   ```
   SECRET_KEY=your-django-secret-key-here
   DEBUG=False
   DATABASE_URL=postgresql://user:password@db-host:5432/db_name
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_BASE_URL=https://api.groq.com/openai/v1
   GROQ_MODEL=llama-3.1-70b-versatile
   ```

5. Click **Create Web Service**
6. Wait for deployment
7. Copy the backend service URL (e.g., `https://obe-assess-backend.onrender.com`)

## Step 3: Deploy Frontend

1. Go to Render Dashboard → **New +** → **Static Site**
2. Connect GitHub repository
3. Configure:
   - **Name**: `obe-assess-frontend`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`

4. **Add Environment Variables** (Settings → Environment):
   ```
   VITE_API_BASE_URL=https://obe-assess-backend.onrender.com/api
   ```

5. Click **Create Static Site**
6. Wait for deployment to complete
7. Your frontend URL will be provided (e.g., `https://obe-assess-frontend.onrender.com`)

## Step 4: Generate Django SECRET_KEY

The backend won't work with a placeholder secret key. Generate a secure one:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

1. Run this command in your local terminal
2. Copy the generated key
3. Update the `SECRET_KEY` environment variable in the Django backend service on Render
4. Trigger a redeploy

## Step 5: Verify Deployment

### Test Backend API
```bash
curl https://obe-assess-backend.onrender.com/api/
```

### Test Frontend
Visit `https://obe-assess-frontend.onrender.com` in your browser

## Environment Variables Reference

### Backend (.env for Django with LLM Integration)
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | Yes | Django secret key (min 50 chars) | `django-insecure-abc123...` |
| `DEBUG` | No | Debug mode (False in production) | `False` |
| `DATABASE_URL` | Yes | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `GROQ_API_KEY` | Yes | Groq API authentication key | (from Groq Console) |
| `GROQ_BASE_URL` | No | Groq API endpoint | `https://api.groq.com/openai/v1` |
| `GROQ_MODEL` | No | LLM model to use | `llama-3.1-70b-versatile` |

### Frontend
| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_BASE_URL` | Yes | Backend API base URL | `https://obe-assess-backend.onrender.com/api` |

## Troubleshooting

### Backend Service Won't Start
- Check build logs: Look for Python dependency issues
- Verify `DATABASE_URL` is correct
- Ensure `SECRET_KEY` is set and valid

### Frontend Shows Blank Page
- Check browser console for CORS errors
- Verify `VITE_API_BASE_URL` matches actual backend URL
- Ensure frontend build completed successfully

### Database Connection Fails
- Verify PostgreSQL service is running
- Check connection string format
- Ensure IP whitelisting allows Render services

## Monitoring & Logs

1. Go to Render Dashboard
2. Click on each service
3. View **Logs** tab for:
   - Build logs
   - Deployment events
   - Runtime errors

## Auto-Deploy from GitHub

To enable automatic deployments on push:

1. In Render service settings, ensure GitHub is connected
2. Each push to the specified branch (default: main) will trigger a new deployment
3. View deployment progress in the **Events** tab

## Performance Tips

- Use Starter plan for development
- Upgrade to Standard/Pro for production load
- Monitor database connection pool usage
- Consider caching for frequently accessed API endpoints

## Security Checklist

- [ ] `SECRET_KEY` is random and kept secret
- [ ] `DEBUG=False` in production
- [ ] Database password is strong and rotated
- [ ] `GROQ_API_KEY` is not exposed in logs
- [ ] CORS is properly configured (only allow frontend origin in production)
- [ ] SSL/TLS certificates are auto-renewed (Render handles this)

## Additional Resources

- Render Docs: https://render.com/docs
- Django Deployment: https://docs.djangoproject.com/en/5.2/howto/deployment/
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- Groq API: https://console.groq.com/docs
