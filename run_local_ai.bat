@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
cd llm_service
uvicorn main:app --reload --port 8001
