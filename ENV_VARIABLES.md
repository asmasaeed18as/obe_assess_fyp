# Environment Variables Configuration

This document describes all environment variables used in the OBE Assessment Platform across different services and deployment stages.

## Backend Service (Django + LLM Integration)

### Required Variables

#### `SECRET_KEY` (Required)
- **Purpose**: Django secret key for session management and CSRF protection
- **Type**: String (50+ characters recommended)
- **Generate**: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- **Security**: KEEP SECRET - never commit to version control
- **Example**: `django-insecure-abc123def456ghi789...`

#### `DEBUG` (Recommended)
- **Purpose**: Django debug mode
- **Type**: Boolean (True/False)
- **Development**: True
- **Production**: False
- **Default**: False
- **Note**: Set to False in production to disable traceback exposure

#### `DATABASE_URL` (Required for Render)
- **Purpose**: Database connection string (PostgreSQL preferred)
- **Type**: Connection URL
- **Format**: `postgresql://user:password@host:port/database`
- **Priority**: If set, overrides individual DB_* variables
- **Example**: `postgresql://postgres:mypass@db.xyz.internal:5432/obe_db`

#### Alternative DB Configuration (if not using DATABASE_URL)
- **`DB_ENGINE`**: `django.db.backends.postgresql` or `django.db.backends.sqlite3`
- **`DB_NAME`**: Database name (for SQLite: path to db file)
- **`DB_USER`**: Database username
- **`DB_PASSWORD`**: Database password
- **`DB_HOST`**: Database hostname or IP
- **`DB_PORT`**: Database port (default: 5432 for PostgreSQL)

### LLM Integration (Integrated into Backend)

#### `GROQ_API_KEY` (Required for LLM functionality)
- **Purpose**: API key for Groq LLM service
- **Type**: String
- **Get from**: https://console.groq.com/keys
- **Security**: KEEP SECRET - use environment variables
- **Example**: `gsk_abcd1234efgh5678ijkl9012mnop...`

#### `GROQ_BASE_URL` (Optional)
- **Purpose**: Groq API endpoint base URL
- **Type**: URL
- **Default**: `https://api.groq.com/openai/v1`
- **Use Case**: Override if using private Groq deployment
- **Example**: `https://api.groq.com/openai/v1`

#### `GROQ_MODEL` (Optional)
- **Purpose**: Groq model identifier
- **Type**: String
- **Default**: `llama-3.1-70b-versatile`
- **Available models**: Check https://console.groq.com/docs/models
- **Example**: `llama-3.1-70b-versatile`, `mixtral-8x7b-32768`

## Frontend Service (React/Vite)

### `VITE_API_BASE_URL` (Required)
- **Purpose**: Base URL for backend API calls
- **Type**: URL
- **Development**: `http://localhost:8000/api`
- **Production (Render)**: `https://obe-assess-backend.onrender.com/api`
- **Note**: Must include `/api` suffix
- **Example**: `https://obe-assess-backend.onrender.com/api`

## Environment-Specific Examples

### Local Development (.env)
```
SECRET_KEY=django-insecure-dev-key-only-for-local-dev
DEBUG=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=obe_db_dev
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
GROQ_API_KEY=your_groq_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.1-70b-versatile
VITE_API_BASE_URL=http://localhost:8000/api
```

### Docker Compose Development
```
SECRET_KEY=docker-dev-key
DEBUG=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=obe_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432
GROQ_API_KEY=${GROQ_API_KEY}
VITE_API_BASE_URL=http://localhost:8000/api
```

### Render Production (.env.production)
```
SECRET_KEY=<generated-secret-key-50+-chars>
DEBUG=False
DATABASE_URL=postgresql://<user>:<pass>@<render-host>:5432/<db-name>
GROQ_API_KEY=${GROQ_API_KEY}
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.1-70b-versatile
VITE_API_BASE_URL=https://obe-assess-backend.onrender.com/api
```

## Security Best Practices

1. **Never commit secrets to Git**
   - Use `.gitignore` to exclude `.env` files
   - Use Render's environment variable UI instead

2. **Use strong SECRET_KEY**
   - Generate with Django's utility (50+ characters)
   - Rotate periodically in production

3. **Restrict database access**
   - Use strong passwords
   - Enable SSL connections
   - Whitelist IP addresses if possible

4. **Rotate API keys**
   - Groq API keys: Regenerate periodically
   - Database credentials: Change after deployment

5. **Monitor API usage**
   - Check Groq API quotas and usage
   - Set up alerts for unusual activity

## Validation Checklist

Before deploying, verify:

- [ ] `SECRET_KEY` is set and has 50+ characters
- [ ] `DEBUG=False` in production
- [ ] `DATABASE_URL` uses correct PostgreSQL format
- [ ] `GROQ_API_KEY` is valid (test with `/api/llm/` endpoints)
- [ ] `VITE_API_BASE_URL` is correctly formatted with `/api` suffix
- [ ] All variables are set in Render dashboard
- [ ] No secrets are hardcoded in `.render.yaml` or application code
- [ ] HTTPS is enabled for all URLs (Render handles this)

## Troubleshooting

### "SECRET_KEY not set" Error
- Solution: Generate and set `SECRET_KEY` in Render environment

### Database Connection Failed
- Check: `DATABASE_URL` format is correct
- Verify: Database service is running
- Confirm: Credentials are accurate

### Frontend Shows Blank Page
- Check: Browser console for errors
- Verify: `VITE_API_BASE_URL` matches backend URL
- Confirm: CORS is properly configured

## References

- Django Settings: https://docs.djangoproject.com/en/5.2/ref/settings/
- Groq API: https://console.groq.com/docs
- Render Docs: https://render.com/docs/environment-variables
- Vite Env: https://vitejs.dev/guide/env-and-mode
