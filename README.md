# viima_proxy
Small Flask app that aggregate Viima items and allow easy create of new ideas

How to run:
- git clone into working dir
- Create python virtual env in working folder
- Activate venv
- pip3 install -r requirements.txt

Two ways to run:
- For simple testing "python3 run.py" start app on port 4000 (with Flask in debug mode)
- For a more scalable deployment do "gunicorn --bind 0.0.0.0:4000 wsgi:app"
