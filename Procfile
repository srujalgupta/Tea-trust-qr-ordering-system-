web: flask --app run.py init-db && flask --app run.py seed-data && gunicorn --bind 0.0.0.0:$PORT --worker-class eventlet -w 1 wsgi:app
