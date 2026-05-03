# Testing Setup

Use the dedicated Django test settings so tests run against an in-memory SQLite
database instead of the database configured in `obe_assess/.env`.

## Assessment Marking Tests With Pytest

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

These tests mock the LLM service and document preprocessing where needed, so they
do not call Groq/Ollama or require a running FastAPI service.

`pytest.ini` is configured to:

- Use `obe_assess.test_settings`.
- Run `obe_assess/assessment_marking/tests`.

## Coverage Report With Pytest

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m coverage run --rcfile=obe_assess/.coveragerc -m pytest
.\.venv\Scripts\python.exe -m coverage report --rcfile=obe_assess/.coveragerc
.\.venv\Scripts\python.exe -m coverage html --rcfile=obe_assess/.coveragerc -d obe_assess/htmlcov_assessment_marking
```

Open `obe_assess/htmlcov_assessment_marking/index.html` for the HTML report.

To run one file:

```powershell
.\.venv\Scripts\python.exe -m pytest obe_assess/assessment_marking/tests/test_views.py
```

## What Is Covered

- Graded submission model helpers and serializer validation.
- Single-file grading upload validation and success flow.
- ZIP bulk grading, including invalid ZIP and missing rubric cases.
- Graded submission detail and delete endpoints.
- Course-level submission deletion.
- CLO mapping and course remapping utilities.
- CLO analytics aggregation.
- LLM marking client payloads, score normalization, error fallback, CSV report
  generation, and summary totals.

## Test Media

The test settings write generated upload/report files into:

```text
obe_assess/.test_media/
```

That folder is ignored by git.
