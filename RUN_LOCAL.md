# Run Project Locally

Your normal `obe_assess/.env` currently points to the deployed database. For
local development, run Django with `obe_assess.settings_local` instead. That
settings file uses your installed local Postgres on `localhost:5432`.

## Database

Local settings expect:

```text
DB_NAME=obe_db
DB_USER=obe_user
DB_PASSWORD=obe_password
DB_HOST=localhost
DB_PORT=5432
```

## Terminal 1: Django Backend

```cmd
run_local_backend.bat
```

This runs:

```cmd
python manage.py migrate --settings=obe_assess.settings_local
python manage.py runserver --settings=obe_assess.settings_local
```

Backend URL:

```text
http://127.0.0.1:8000
```

## Terminal 2: AI Service

If the AI service needs Groq, set your key first:

```cmd
set GROQ_API_KEY=your_key_here
run_local_ai.bat
```

AI service URL:

```text
http://127.0.0.1:8001
```

## Terminal 3: React Frontend

```cmd
run_local_frontend.bat
```

Frontend URL:

```text
http://localhost:5173
```

The frontend local env is in `frontend/.env.local`:

```text
VITE_API_BASE_URL=http://localhost:8000/api
```

## Create Admin User

With the database running:

```cmd
cd /d D:\Fyp\obe_assess_fyp
.venv\Scripts\activate
cd obe_assess
python manage.py createsuperuser --settings=obe_assess.settings_local
```
