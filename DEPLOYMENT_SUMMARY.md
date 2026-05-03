# Render Deployment Configuration Summary

## Created Files

This deployment package includes the following configuration files:

### 1. `.env.production` (Production environment variables)
- Contains all environment variables needed for Render deployment
- Instructions on how to fill in each variable
- Security reminders for sensitive values

### 2. `.env.local.example` (Local development template)
- Example configuration for local development
- Uses localhost addresses and SQLite/local PostgreSQL
- Includes comments explaining each variable

### 3. `.env.example` (Updated generic template)
- Enhanced version of the original `.env.example`
- Better documentation for all environment variables
- Examples for both local and production use

### 4. `RENDER_DEPLOYMENT.md` (Comprehensive deployment guide)
- Step-by-step instructions for deploying all three services
- Database setup guidance
- Environment variable configuration
- Troubleshooting section
- Security checklist

### 5. `ENV_VARIABLES.md` (Detailed variable reference)
- Complete documentation of all environment variables
- Explains purpose, type, and usage of each variable
- Environment-specific examples
- Security best practices
- Validation checklist

### 6. `render-setup.sh` (Deployment helper script)
- Quick checklist generator
- Links to deployment resources
- Reminder for required credentials

### 7. `render.yaml` (Already configured)
- Defines services (backend, frontend)
- Build and start commands for each service
- Health check endpoints

## Quick Start for Deployment

### Step 1: Prepare Credentials (5 minutes)

```bash
# Generate Django SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Get Groq API key
# Visit: https://console.groq.com/keys
```

### Step 2: Create Services on Render (15 minutes)

1. **Create PostgreSQL Database**
   - Render → New → PostgreSQL
   - Copy the connection string

2. **Create Backend Service**
   - Render → New → Web Service
   - Branch: main
   - Build: `pip install -r requirements.txt && cd obe_assess && python manage.py migrate`
   - Start: `gunicorn obe_assess.wsgi:application --chdir obe_assess --bind 0.0.0.0:$PORT`
   - Add all backend env variables (see below)

3. **Create Frontend Service**
   - Render → New → Static Site
   - Branch: main
   - Build: `cd frontend && npm install && npm run build`
   - Publish: `frontend/dist`
   - Add VITE_API_BASE_URL

### Step 3: Set Environment Variables

**Backend Service:**
```
SECRET_KEY=<your-generated-key>
DEBUG=False
DATABASE_URL=<from-PostgreSQL-service>
GROQ_API_KEY=<your-groq-key>
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.1-70b-versatile
```

**Frontend Service:**
```
VITE_API_BASE_URL=<your-backend-service-url>/api
```

### Step 4: Verify Deployment (5 minutes)

```bash
# Test backend
curl https://obe-assess-backend.onrender.com/api/

# Visit frontend
# https://obe-assess-frontend.onrender.com
```

## Service URLs Template

Replace `<project-name>` with your actual project/service names:

```
Backend:  https://<project-name>-backend.onrender.com
Frontend: https://<project-name>-frontend.onrender.com
Database: Internal connection from services
```

## Environment Variables by Service

### Backend (Django with LLM Integration)
| Variable | Purpose | Development | Production |
|----------|---------|-------------|-----------|
| SECRET_KEY | Django security | `dev-unsafe-key` | Generated (50+ chars) |
| DEBUG | Debug mode | `True` | `False` |
| DATABASE_URL | PostgreSQL connection | Optional | Required |
| GROQ_API_KEY | Groq authentication | Development key | Production key |
| GROQ_BASE_URL | Groq API endpoint | `https://api.groq.com/openai/v1` | Same |
| GROQ_MODEL | Model to use | `llama-3.1-70b-versatile` | Same |

### Frontend
| Variable | Purpose | Value |
|----------|---------|-------|
| VITE_API_BASE_URL | Backend API URL | `https://<backend-url>/api` |

## Security Checklist

- [ ] `SECRET_KEY` is random and 50+ characters
- [ ] `DEBUG=False` in production
- [ ] No secrets committed to Git
- [ ] GROQ_API_KEY never exposed in logs
- [ ] PostgreSQL password is strong
- [ ] HTTPS enabled (Render auto-handles)
- [ ] All services have proper error handling
- [ ] CORS configured appropriately

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│     Render Platform                     │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  (Static Site)        │
│  │   Frontend   │  React/Vite           │
│  │   React App  │  (frontend/dist)      │
│  └──────┬───────┘                       │
│         │ API calls                     │
│         ▼                               │
│  ┌──────────────┐  (Web Service)        │
│  │   Backend    │  Django/DRF           │
│  │  API Server  │  (Port 8000)          │
│  │ + LLM Integ. │  LLM at /api/llm/*    │
│  └──────┬───────┘                       │
│         │                               │
│         ▼                               │
│  ┌──────────────┐  (Managed DB)         │
│  │ PostgreSQL   │                       │
│  │  Database    │                       │
│  └──────────────┘                       │
│                                         │
└────────────────┬────────────────────────┘
                 │ External API call
                 ▼
            ┌─────────────┐
            │  Groq API   │
            │  LLM Models │
            └─────────────┘
```

## Troubleshooting Quick Links

**Problem**: Backend service won't start
- Check: Python dependencies in build logs
- Verify: DATABASE_URL is correct format
- Ensure: SECRET_KEY is set

**Problem**: Frontend shows blank/errors
- Check: Browser console for API errors
- Verify: VITE_API_BASE_URL in frontend env
- Confirm: CORS allows frontend domain

**Problem**: Database connection failed
- Verify: PostgreSQL service is running
- Check: Connection string format
- Confirm: Credentials are correct

## Cost Estimation

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| Backend | Starter | $7 |
| Frontend | Free | $0 |
| PostgreSQL | Starter | $7 |
| **Total** | | **~$14/month** |

(Prices subject to change - check Render.com for current pricing)

## Next Steps

1. Copy environment variables from `.env.production` to Render
2. Deploy services using render.yaml
3. Run migrations on backend: `python manage.py migrate`
4. Test all endpoints
5. Monitor logs in Render dashboard
6. Set up auto-deploys from GitHub (optional)

## Useful Resources

- **Render Documentation**: https://render.com/docs
- **Django Deployment**: https://docs.djangoproject.com/en/5.2/howto/deployment/
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Groq API Docs**: https://console.groq.com/docs
- **This Project's Guide**: See RENDER_DEPLOYMENT.md

## Support

For issues or questions:
1. Check Render logs in the dashboard
2. Review RENDER_DEPLOYMENT.md troubleshooting section
3. Check ENV_VARIABLES.md for variable explanations
4. Visit Render support: https://support.render.com
