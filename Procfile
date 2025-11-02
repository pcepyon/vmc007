release: cd backend && python manage.py migrate --noinput
web: cd backend && gunicorn data_ingestion.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
