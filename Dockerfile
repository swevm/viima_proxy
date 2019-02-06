FROM python:3.7

WORKDIR /usr/src/app

# For some reason below git clone won´t work as expected - /bin/sh cat find boot.sh afterwards
# COPY . . form a dir that contain the clone work though - Strange?!?!?!?
#RUN git clone https://github.com/swevm/viima_proxy.git .
COPY . .
#######
RUN pip install -r requirements.txt


# Are there any benefits running withing a venv?
#RUN python -m venv venv
#RUN venv/bin/pip install -r requirements.txt
#RUN venv/bin/pip install gunicorn

RUN chmod +x boot.sh

RUN chown -R microblog:microblog ./

EXPOSE 4000
ENTRYPOINT ["./boot.sh"]
