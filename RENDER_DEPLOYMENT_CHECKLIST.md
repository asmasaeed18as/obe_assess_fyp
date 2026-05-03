# Render Deployment Tracking Checklist

## Pre-Deployment Preparation

### Credentials & Setup
- [ ] Generated Django SECRET_KEY
  ```
  Key saved: ________________________________
  ```
- [ ] Obtained Groq API Key
  ```
  Key saved: ________________________________
  ```
- [ ] GitHub repository connected to Render account
- [ ] All code pushed to main branch
- [ ] render.yaml verified in repository root

---

## Service Deployment Checklist

### 1. PostgreSQL Database
**Timeline: ~5-10 minutes**

- [ ] Navigated to Render dashboard
- [ ] Created new PostgreSQL service
  - [ ] Name: `obe-assess-postgres`
  - [ ] Version: 15
  - [ ] Region: ______________ (same as services)
- [ ] Database created successfully (green checkmark)
- [ ] Internal Database URL copied:
  ```
  URL: postgresql://______________________
  ```

### 2. Backend Web Service
**Timeline: ~10-15 minutes**

- [ ] Created new Web Service
  - [ ] Name: `obe-assess-backend`
  - [ ] Runtime: Python 3
  - [ ] Region: ______________ (same as database)
  - [ ] Build Command: `pip install -r requirements.txt && cd obe_assess && python manage.py migrate`
  - [ ] Start Command: `gunicorn obe_assess.wsgi:application --chdir obe_assess --bind 0.0.0.0:$PORT`

- [ ] Added Environment Variables:
  - [ ] `SECRET_KEY` = ________________________
  - [ ] `DEBUG` = False
  - [ ] `DATABASE_URL` = ________________________
  - [ ] `LLM_SERVICE_URL` = (will update later)
  - [ ] `GROQ_API_KEY` = ________________________
  - [ ] `GROQ_BASE_URL` = https://api.groq.com/openai/v1
  - [ ] `GROQ_MODEL` = llama-3.1-70b-versatile

- [ ] Clicked "Save All" for environment variables
- [ ] Service deployed successfully (green checkmark)
- [ ] Verified migrations completed in logs
- [ ] Backend service URL noted:
  ```
  URL: https://obe-assess-backend.onrender.com
  ```

### 3. LLM Microservice
**Timeline: ~5-10 minutes**

- [ ] Created new Web Service
  - [ ] Name: `obe-assess-llm`
  - [ ] Runtime: Python 3
  - [ ] Region: ______________ (same as others)
  - [ ] Build Command: `cd llm_service && pip install -r requirements.txt`
  - [ ] Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

- [ ] Added Environment Variables:
  - [ ] `GROQ_API_KEY` = ________________________
  - [ ] `GROQ_BASE_URL` = https://api.groq.com/openai/v1
  - [ ] `GROQ_MODEL` = llama-3.1-70b-versatile

- [ ] Clicked "Save All"
- [ ] Service deployed successfully (green checkmark)
- [ ] LLM service URL noted:
  ```
  URL: https://obe-assess-llm.onrender.com
  ```

- [ ] **Updated Backend Service:**
  - [ ] Went back to backend service
  - [ ] Updated `LLM_SERVICE_URL` variable with LLM service URL
  - [ ] Clicked "Save All"
  - [ ] Backend service redeployed

### 4. Frontend Static Site
**Timeline: ~5-10 minutes**

- [ ] Created new Static Site
  - [ ] Name: `obe-assess-frontend`
  - [ ] Region: ______________ (same as others)
  - [ ] Build Command: `cd frontend && npm install && npm run build`
  - [ ] Publish Directory: `frontend/dist`

- [ ] Added Environment Variables:
  - [ ] `VITE_API_BASE_URL` = https://obe-assess-backend.onrender.com/api

- [ ] Clicked "Save All"
- [ ] Site deployed successfully (green checkmark)
- [ ] Frontend URL noted:
  ```
  URL: https://obe-assess-frontend.onrender.com
  ```

---

## Verification & Testing

### Service Status Check
- [ ] Backend service: Green checkmark ✓
- [ ] LLM service: Green checkmark ✓
- [ ] Frontend site: Green checkmark ✓
- [ ] PostgreSQL database: Green checkmark ✓

### Manual Endpoint Testing
- [ ] Backend health: `curl https://obe-assess-backend.onrender.com/api/`
  - Response: ____________________________
- [ ] LLM health: `curl https://obe-assess-llm.onrender.com/`
  - Response: ____________________________
- [ ] Frontend loads: Visit https://obe-assess-frontend.onrender.com
  - Status: ____________________________

### Log Review
- [ ] Backend logs reviewed for errors
- [ ] LLM service logs reviewed
- [ ] Frontend build logs verified
- [ ] Database migration messages found

### Browser Testing
- [ ] Frontend loads without blank page
- [ ] Browser console (F12) shows no errors
- [ ] Network tab shows successful API calls
- [ ] No CORS errors visible

---

## Troubleshooting Log

### Issues Encountered

**Issue 1:**
- Symptom: ____________________________
- Cause: ____________________________
- Solution Applied: ____________________________
- ✓ Resolved

**Issue 2:**
- Symptom: ____________________________
- Cause: ____________________________
- Solution Applied: ____________________________
- ✓ Resolved

---

## Service URLs Recorded

```
Frontend:  https://obe-assess-frontend.onrender.com
Backend:   https://obe-assess-backend.onrender.com
LLM:       https://obe-assess-llm.onrender.com
Database:  (Internal - no public URL)
```

### Credentials & Secrets Stored Securely
- [ ] SECRET_KEY stored in password manager
- [ ] GROQ_API_KEY stored in password manager
- [ ] Database credentials stored in password manager
- [ ] .env files NOT committed to Git

---

## Old Services Cleanup

### Services to Delete (if any)
- [ ] Service 1: ____________________________
  - [ ] Confirmed no traffic
  - [ ] Deleted from Render

- [ ] Service 2: ____________________________
  - [ ] Confirmed no traffic
  - [ ] Deleted from Render

---

## Post-Deployment Tasks

### Feature Testing (Optional)
- [ ] Created test user account
- [ ] Logged in successfully
- [ ] Created test course
- [ ] Created test assessment
- [ ] Generated assessment questions (tests LLM)
- [ ] Marked assessment questions

### Monitoring Setup (Optional)
- [ ] Email alerts configured for service failures
- [ ] Groq API usage monitored
- [ ] Error logs reviewed

### Documentation (Optional)
- [ ] Service URLs documented
- [ ] Access credentials shared with team (securely)
- [ ] Deployment date recorded: ______________
- [ ] README updated with deployment info

---

## Deployment Completion

**Deployment Date:** ______________

**Completed by:** ______________

**Status:** 
- [ ] ✓ All services deployed and verified
- [ ] ⚠ Partial deployment (issues encountered)
- [ ] ✗ Deployment incomplete

**Final Verification:**
- [ ] All services responding
- [ ] Database connected
- [ ] Frontend loading
- [ ] LLM integration working

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## Next Steps

1. **Share with Team**
   - [ ] Frontend URL shared
   - [ ] API documentation shared
   - [ ] Access credentials shared securely

2. **Monitor**
   - [ ] Check dashboard weekly for issues
   - [ ] Monitor Groq API usage
   - [ ] Review logs for errors

3. **Iterate**
   - [ ] Collect user feedback
   - [ ] Fix bugs reported
   - [ ] Optimize performance if needed

4. **Scaling (Future)**
   - [ ] Upgrade to Standard plan if needed
   - [ ] Configure auto-scaling
   - [ ] Add caching layer
   - [ ] Set up CDN for frontend

---

**✓ Deployment Complete! 🎉**
