# 🚀 Render Deployment - Quick Start Checklist

## Pre-Deployment Checklist (Do This First)

### Generate Required Credentials

- [ ] **Django SECRET_KEY**
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
  Save the output (50+ character string)

- [ ] **Groq API Key**
  - Visit: https://console.groq.com/keys
  - Create new API key
  - Save the key

### Prepare Repository

- [ ] Push all code to GitHub (main branch)
- [ ] Ensure `render.yaml` is in repository root
- [ ] Verify `.gitignore` excludes `.env` files
- [ ] No secrets hardcoded in code

---

## Step-by-Step Deployment (30 minutes)

### Phase 1: Set Up Database (5 min)

1. Go to https://dashboard.render.com
2. Click **New +** → **PostgreSQL**
3. Fill in:
   - Name: `obe-assess-db`
   - PostgreSQL Version: 15
4. Click **Create Database**
5. **Copy the Internal Database URL** (looks like: `postgresql://user:pass@...`)
6. Save for later use in backend configuration

### Phase 2: Deploy Backend Service (10 min)

1. Click **New +** → **Web Service**
2. Connect GitHub repository
3. Configure:
   - Name: `obe-assess-backend`
   - Environment: Python 3
   - Region: Same as database
   - Build Command: `pip install -r requirements.txt && cd obe_assess && python manage.py migrate`
   - Start Command: `gunicorn obe_assess.wsgi:application --chdir obe_assess --bind 0.0.0.0:$PORT`
4. Click **Advanced** and add environment variables:
   ```
   SECRET_KEY=<your-generated-secret-key>
   DEBUG=False
   DATABASE_URL=<from-PostgreSQL-service>
   GROQ_API_KEY=<your-groq-api-key>
   GROQ_BASE_URL=https://api.groq.com/openai/v1
   GROQ_MODEL=llama-3.1-70b-versatile
   ```
5. Click **Create Web Service**
6. Wait for deployment (green checkmark)
7. **Copy the service URL** (e.g., `https://obe-assess-backend.onrender.com`)

### Phase 3: Deploy Frontend Service (5 min)

1. Click **New +** → **Static Site**
2. Connect GitHub repository
3. Configure:
   - Name: `obe-assess-frontend`
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/dist`
4. Click **Advanced** and add environment variables:
   ```
   VITE_API_BASE_URL=<your-backend-url>/api
   ```
   Example: `https://obe-assess-backend.onrender.com/api`
5. Click **Create Static Site**
6. Wait for deployment (green checkmark)
7. Your frontend URL will be provided

---

## Post-Deployment Verification (5 min)

### Test Each Service

- [ ] **Backend API**
  ```bash
  curl https://obe-assess-backend.onrender.com/api/
  ```
  Expected: JSON response or 404 (not 500)

- [ ] **Frontend**
  - Visit: `https://obe-assess-frontend.onrender.com`
  - Expected: Application loads without errors
  - Check browser console (F12) for no error messages

### Check Logs

- [ ] Backend logs: No errors about database or LLM connection
- [ ] Frontend logs: No CORS or 404 errors

---

## Configuration Reference

### Backend Environment Variables
```
SECRET_KEY=<50+ character random string>
DEBUG=False
DATABASE_URL=postgresql://user:password@host:5432/db
GROQ_API_KEY=<your-groq-key>
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.1-70b-versatile
```

### Frontend Environment Variables
```
VITE_API_BASE_URL=https://obe-assess-backend.onrender.com/api
```

---

## Troubleshooting

### Backend won't start
- [ ] Check Python dependencies are correct
- [ ] Verify SECRET_KEY is set
- [ ] Confirm DATABASE_URL format: `postgresql://user:pass@host:port/db`
- [ ] Ensure database is running

### Frontend blank or errors
- [ ] Open browser Developer Tools (F12)
- [ ] Check Console tab for errors
- [ ] Verify VITE_API_BASE_URL includes `/api` suffix
- [ ] Confirm backend URL is accessible

### Database connection failed
- [ ] Check DATABASE_URL in backend environment
- [ ] Verify PostgreSQL service is running
- [ ] Confirm credentials are correct

---

## File Reference

| File | Purpose |
|------|---------|
| `.env.production` | Production environment variables template |
| `.env.local.example` | Local development environment template |
| `.env.example` | Generic environment variables reference |
| `RENDER_DEPLOYMENT.md` | Comprehensive step-by-step guide |
| `ENV_VARIABLES.md` | Detailed documentation of all variables |
| `DEPLOYMENT_SUMMARY.md` | Overview and quick reference |
| `render.yaml` | Render service configuration |
| `render-setup.sh` | Helper script for deployment |

---

## Success Criteria ✅

Your deployment is successful when:

- [ ] All services show green checkmarks (deployed)
- [ ] Backend API responds with data (no 500 errors)
- [ ] Frontend loads and connects to backend
- [ ] Database migrations completed successfully
- [ ] No CORS errors in browser console
- [ ] Navigation and basic features work

---

## Next Steps

1. **Test Core Features**
   - Create a test user account
   - Create a test assessment
   - Test assessment generation (LLM integration)

2. **Set Up Monitoring**
   - Enable Render logs
   - Set up alerts for errors
   - Monitor API usage

3. **Document URLs**
   - Save all service URLs
   - Share frontend URL with team
   - Document API endpoint URLs

4. **Optional: Auto-Deploy**
   - Enable auto-deploy from GitHub
   - Any push to main will auto-redeploy

---

## Support & Resources

| Resource | Link |
|----------|------|
| Render Docs | https://render.com/docs |
| Groq Console | https://console.groq.com |
| Django Docs | https://docs.djangoproject.com/ |
| FastAPI Docs | https://fastapi.tiangolo.com/ |
| This Project Docs | See RENDER_DEPLOYMENT.md |

---

## Common Issues & Solutions

### Issue: "GROQ_API_KEY is not set"
**Solution**: Add GROQ_API_KEY to backend service environment variables

### Issue: Database migrations fail
**Solution**: Check DATABASE_URL format and verify credentials

### Issue: Frontend shows API errors
**Solution**: Verify VITE_API_BASE_URL matches backend URL with /api suffix

### Issue: Services in "build failed" state
**Solution**: Check build logs for specific error messages

---

## Final Checklist

- [ ] All credentials generated and saved securely
- [ ] All services deployed and green
- [ ] All environment variables set correctly
- [ ] Database migrations completed
- [ ] All endpoints responding without errors
- [ ] Frontend loads and connects to backend
- [ ] CORS errors resolved
- [ ] Groq API integration working
- [ ] Ready for user testing

**Congratulations! Your Render deployment is complete! 🎉**
