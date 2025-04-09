web: gunicorn kursk_backend.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A kursk_backend worker --loglevel=info --pool=solo
beat: celery -A kursk_backend beat --loglevel=info