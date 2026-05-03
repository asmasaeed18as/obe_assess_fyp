# Render Deployment Setup

## Environment Variables Required

For your Render deployment, set these environment variables in your Render dashboard:

### Database
- `DATABASE_URL` - PostgreSQL connection string (Render provides this)

### Admin User Creation
- `ADMIN_EMAIL` - Email for admin user (e.g., `aima@gmail.com`)
- `ADMIN_PASSWORD` - Secure password (use a strong password, not `aima@123`)
- `ADMIN_FIRST_NAME` (optional) - Defaults to "Admin"
- `ADMIN_LAST_NAME` (optional) - Defaults to "User"

### Django Settings
- `SECRET_KEY` - Generate a strong secret key (don't use the default)
- `DEBUG` - Set to `False` for production
- `ALLOWED_HOSTS` - Set to your Render domain

### LLM Integration (if needed)
- `GROQ_API_KEY` - Your Groq API key

## Steps to Deploy on Render

1. **Create a new Web Service** on Render
2. **Connect your GitHub repository**
3. **Set Build Command:**
   ```
   bash obe_assess/build.sh
   ```

4. **Set Start Command:**
   ```
   python obe_assess/manage.py runserver 0.0.0.0:$PORT
   ```

5. **Add Environment Variables** in Render dashboard:
   - Add each variable listed above
   - **NEVER commit secrets to git**

6. **Database Setup:**
   - Add a PostgreSQL database in Render
   - Render automatically provides `DATABASE_URL`

## After Deployment

Once deployed, you can log in with:
- Email: Value of `ADMIN_EMAIL`
- Password: Value of `ADMIN_PASSWORD`

The `create_admin` command is **idempotent** — it won't create duplicate users if run multiple times.

## Security Best Practices

✅ Use environment variables for all secrets  
✅ Use strong, unique passwords (20+ characters)  
✅ Set `DEBUG = False` in production  
✅ Generate a new `SECRET_KEY`  
❌ Don't hardcode credentials in build.sh  
❌ Don't commit .env files to git  
