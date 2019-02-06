#Run this file with "gunicorn --bind 0.0.0.0:4000 wsgi:app"
from app import create_app

app = create_app()
