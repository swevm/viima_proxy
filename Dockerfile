FROM python:3.7

WORKDIR /usr/src/app

RUN git clone https://github.com/swevm/viima_proxy.git .

RUN pip install -r requirements.txt

# Are there any benefits running withing a venv?
#RUN python -m venv venv
#RUN venv/bin/pip install -r requirements.txt
#RUN venv/bin/pip install gunicorn

COPY cert/* ./

RUN chmod +x ./boot.sh

RUN chown -R root:root ./

EXPOSE 4000
ENTRYPOINT ["./boot.sh", "localhost.key", "localhost.crt"]
