# viima_proxy
Small Flask app that aggregate Viima items and allow easy create of new ideas

How to run:
- git clone into working dir
- Create python virtual env in working folder
- Activate venv
- pip3 install -r requirements.txt

Two ways to run (from shell):
- For simple testing "python3 run.py" start app on port 4000 (with Flask in debug mode)
- For a more scalable deployment do "gunicorn --bind 0.0.0.0:4000 wsgi:app"

Run with Docker
- Clone repo
- mkdir /cert
- Create openssl cert, named localhost.key and localhost.crt
- docker image -t viima-proxy .
- docker run -p 4000:4000 viima-proxy