@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
cd obe_assess
python manage.py migrate --settings=obe_assess.settings_local
python manage.py runserver --settings=obe_assess.settings_local
