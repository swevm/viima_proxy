# This file can by run from venv with python3 run.py
from app import create_app

app = create_app()
app.run(host='0.0.0.0', port=8001, debug=True)