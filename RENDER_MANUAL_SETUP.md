# Render Dashboard Setup - Step-by-Step Instructions

## Step 1: Create Unified Web Service on Render

### Access Render Dashboard
1. Go to https://dashboard.render.com
2. Log in to your account
3. Click **New +** button → Select **Web Service**

### Service Configuration

**Basic Settings:**
- **Name**: `obe-assess-backend`
- **GitHub Repository**: Select your repository
- **Branch**: `main`
- **Region**: Choose closest to your users (e.g., us-east-1)
- **Runtime**: Python 3
- **Build Command**: 
  ```
  pip install -r requirements.txt && cd obe_assess && python manage.py migrate
  ```
- **Start Command**: 
  ```
  gunicorn obe_assess.wsgi:application --chdir obe_assess --bind 0.0.0.0:$PORT
  ```
- **Instance Type**: Starter (or upgrade as needed)
- **Auto-Deploy**: Enabled (optional)

**Advanced Settings:**
- **Health Check Path**: `/api/`
- **Health Check Protocol**: HTTP
- **Timeout**: 30 seconds

---

## Step 2: Create PostgreSQL Database on Render

### Create Database Service
1. Click **New +** → **PostgreSQL**
2. Configure:
   - **Name**: `obe-assess-postgres`
   - **PostgreSQL Version**: 15 (latest)
   - **Region**: Same as web service
   - **Data Dog Monitoring**: No (unless needed)
   - **Instance Type**: Starter

3. Click **Create Database**
4. Wait for database to provision (green checkmark)
5. **COPY the Internal Database URL** from the service page
   - Format: `postgresql://username:password@host:port/database`
   - This is what you'll use for DATABASE_URL

---

## Step 3: Add Environment Variables in Render Dashboard

### Navigate to Backend Service Settings
1. Click on the `obe-assess-backend` service
2. Go to **Settings** tab → **Environment**
3. Click **Add Environment Variable** for each:

### Backend Environment Variables

#### Required Variables:

**1. SECRET_KEY**
```
Key: SECRET_KEY
Value: (paste your generated 50+ character key)
```

**2. DEBUG**
```
Key: DEBUG
Value: False
```

**3. DATABASE_URL**
```
Key: DATABASE_URL
Value: (paste the PostgreSQL Internal URL from database service)
```

**4. GROQ_API_KEY**
```
Key: GROQ_API_KEY
Value: (paste your Groq API key from console.groq.com)
```

**6. GROQ_BASE_URL**
```
Key: GROQ_BASE_URL
Value: https://api.groq.com/openai/v1
```

**7. GROQ_MODEL**
```
Key: GROQ_MODEL
Value: llama-3.1-70b-versatile
```

### Save All Variables
- Click **Save All** or individual **Add** buttons
- Service will automatically redeploy with new variables

---

## Step 4: Deploy Frontend Static Site

### Create Static Site Service
1. Click **New +** → **Static Site**
2. Configure:
   - **Name**: `obe-assess-frontend`
   - **GitHub Repository**: Same repository
   - **Branch**: `main`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`

### Add Frontend Environment Variables
1. Go to frontend service **Settings** → **Environment**
2. Add this variable:

```
VITE_API_BASE_URL=https://obe-assess-backend.onrender.com/api
```

(Replace domain with your actual backend URL once deployed)

---

## Step 5: Configure Database Connection (First Time Only)

### Initialize Database
1. Go to Backend service **Logs** tab
2. Wait for initial deployment and migration to complete
3. Look for messages like:
   - `Running migrations...`
   - `Applying migrations... OK`
   - `Django server running on 0.0.0.0:xxxx`

### If Migrations Fail
1. Check logs for error details
2. Common issues:
   - DATABASE_URL format incorrect
   - PostgreSQL not ready
   - Credentials wrong
3. Fix the issue and redeploy by clicking **Manual Deploy**

---

## Step 6: Verify All Services Deployed

### Check Service Status
In Render Dashboard, verify:

- [ ] `obe-assess-backend` - Green checkmark (Live)
- [ ] `obe-assess-frontend` - Green checkmark (Live)
- [ ] `obe-assess-postgres` - Green checkmark (Available)

### Get Service URLs
From each service card, note:
- **Backend URL**: `https://obe-assess-backend.onrender.com`
- **Frontend URL**: `https://obe-assess-frontend.onrender.com`

---

## Step 7: Test Deployed Endpoints

### Test Backend API
```bash
curl https://obe-assess-backend.onrender.com/api/
```
Expected response: Status 200 or 404 (not 500)

### Test Frontend
1. Visit: `https://obe-assess-frontend.onrender.com`
2. Check:
   - Page loads without errors
   - No red X icons
   - Console has no error messages (F12)

### Verify Database Connection
1. Go to Backend service logs
2. Should see successful database migration messages
3. No connection errors

---

## Step 8: Troubleshoot Common Issues

### Backend shows "500 Internal Server Error"
**Check:**
1. Environment variables all set correctly
2. SECRET_KEY has 50+ characters
3. DATABASE_URL format is correct
4. Migrations completed successfully

**Fix:**
- Update variable → Click **Save All** → Wait for redeploy
- Check logs for specific error

### Frontend blank or shows errors
**Check:**
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network tab for failed API calls

**Common fixes:**
- VITE_API_BASE_URL doesn't match backend URL
- Backend URL missing `/api` suffix
- CORS issues

---

## Step 9: Delete Old Services (If Any)

### Find Old Services
1. In Render Dashboard, look for old/duplicate services
2. Click on each old service
3. Go to **Settings** tab
4. Scroll to bottom → **Delete Service**

### Confirm Deletion
- Enter service name to confirm
- Click **Delete**
- Old service will be removed

---

## Checklist for Manual Render Setup

**Before Creating Services:**
- [ ] Have your SECRET_KEY ready (50+ chars)
- [ ] Have your GROQ_API_KEY ready
- [ ] GitHub repository is accessible from Render
- [ ] You're logged into Render dashboard

**Creating Backend Service:**
- [ ] Web service created with correct build/start commands
- [ ] Region selected (close to target users)
- [ ] PostgreSQL database created with Internal URL copied
- [ ] All 6 environment variables added to backend
- [ ] Database migrations completed (check logs)

**Creating Frontend Service:**
- [ ] Static site created with correct build command
- [ ] Publish directory set to `frontend/dist`
- [ ] VITE_API_BASE_URL set to backend URL with `/api`

**Verification:**
- [ ] All services show green checkmarks
- [ ] Backend API responds to curl requests
- [ ] Frontend loads in browser
- [ ] No 500 errors in logs

---

## Environment Variables Quick Reference

### Backend Environment Variables (added in Step 3)

```
SECRET_KEY=<your-50-char-key>
DEBUG=False
DATABASE_URL=<postgresql-internal-url-from-db-service>
GROQ_API_KEY=<your-groq-key>
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.1-70b-versatile
```

---

## Support & Debugging

### Check Service Logs
1. Click on service → **Logs** tab
2. Filter by date/time
3. Look for error messages
4. Common patterns:
   - `ERROR` in red
   - `Exception` or `Traceback`
   - `Connection refused`

### Redeploy Service
1. Go to service **Settings**
2. Scroll to bottom → **Manual Deploy**
3. Wait for redeploy to complete

### Environment Variables Not Updated?
1. Make sure to click **Save All**
2. Service should auto-redeploy
3. If not, click **Manual Deploy**

---

## Next After Successful Deployment

1. **Test User Features**
   - Create test user account
   - Create test assessment
   - Generate assessment questions (tests LLM integration)

2. **Monitor**
   - Set up email alerts for service failures
   - Monitor Groq API usage

3. **Document URLs**
   - Save all three service URLs
   - Share frontend URL with team

4. **Optional: Auto-Deploy**
   - Already enabled in Backend service
   - Any GitHub push to main will auto-deploy

---

## Estimated Timeline

| Step | Time |
|------|------|
| Create Backend service | 2 min |
| Create PostgreSQL | 5 min |
| Add environment variables | 3 min |
| Create Frontend | 2 min |
| Initial deployment & migrations | 5-10 min |
| **Total** | **~17-22 min** |

**Total time to deployment: 20-25 minutes**
