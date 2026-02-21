To understand how  module fits into the existing ecosystem, I have integrated  setup instructions with the contribution rules. This creates a single "Source of Truth" document for  repository.


---

# 🎓 OBE Assessment System (FYP)

A comprehensive Outcome-Based Education (OBE) assessment system that allows Instructors to manage courses, upload outlines, automatically extract CLOs, and generate AI-powered assessments mapped to Bloom's Taxonomy.

---

## 🛠 Project Contribution Rules (READ FIRST)

To avoid merge conflicts and structure errors, all team members **must** follow these rules:

1. **Do Not Rename Folders:** Never rename the root directories (`obe_assess`, `frontend`, etc.).
2. **The "Apps" Rule:** All backend features (like Assessment Marking) must be created as **Django Apps** inside the `obe_assess/` folder. Do **not** create separate root folders for your work.
3. **Branching:** Never push directly to `main`. Create a branch first:
* `git checkout -b feature/assessment-marking`


4. **Syncing:** Always run `git pull origin main` before starting work to ensure your local structure matches the server.

---

## 📋 Prerequisites

* **Python 3.10+**
* **Node.js & npm**
* **PostgreSQL**
* **Ollama** (for local LLM execution)

---

## 🚀 1. Setup Backend (Django & PostgreSQL)

Navigate to the project root:

**Create and Activate Virtual Environment:**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

```

**Install Dependencies:**

```bash
pip install -r requirements.txt
pip install psycopg2-binary

```

**Configure PostgreSQL:**
Create a database named `obe_assess_db` and a user `obe_user` in pgAdmin/psql. Then run:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

```

---

## 🎨 2. Setup Frontend (React)

```bash
cd frontend
npm install
npm start

```

---

## 🧠 3. Setup AI Microservice (LLM)

1. **Ollama:** `ollama pull gemma3:1b`
2. **Run Service:**

```bash
cd llm_service
pip install fastapi uvicorn requests
uvicorn main:app --reload --port 8001

```

---

## 🧪 Development Workflow

To run the full system, you need **3 terminals** active:

* **Terminal 1:** Django (`python manage.py runserver`)
* **Terminal 2:** React (`npm start`)
* **Terminal 3:** AI Service (`uvicorn main:app --reload --port 8001`)

### Adding a New Module (e.g., Assessment Marking)

If you are assigned a new feature, follow these steps to keep the structure clean:

1. `cd obe_assess`
2. `python manage.py startapp assessment_marking`
3. Add `'assessment_marking',` to `INSTALLED_APPS` in `obe_assess/settings.py`.

---

**to create supersuser to access the backend admin panel and database**
You need a superuser to access the Django Admin panel. Run this in your terminal:

PowerShell
python manage.py createsuperuser
