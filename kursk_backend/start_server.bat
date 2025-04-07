@echo off
echo 🔁 Start Redis, Celery, Django and Beat...

:: 1. Запуск Redis
start cmd /k "cd /d C:\Redis && redis-server.exe"

:: 2. Пауза для запуска Redis
timeout /t 3 > nul

:: 3. Запуск Celery worker
start cmd /k "cd /d D:\cla$$$ic\API(VS)\API_android\kursk_backend && call ..\.venv\Scripts\activate && celery -A kursk_backend worker --loglevel=info --pool=solo"

:: 4. Запуск Django
start cmd /k "cd /d D:\cla$$$ic\API(VS)\API_android\kursk_backend && call ..\.venv\Scripts\activate && python manage.py runserver"

:: 5. Запуск Celery Beat
start cmd /k "cd /d D:\cla$$$ic\API(VS)\API_android\kursk_backend && call ..\.venv\Scripts\activate && celery -A kursk_backend beat --loglevel=info"
