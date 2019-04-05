FROM python:3.6

ARG logdir="/var/log/m3"

COPY . /core
WORKDIR /core

RUN apt-get -y update \
  && apt-get -y install openssl build-essential python3-dev libffi-dev postgresql-client enchant vim \
  && pip3 install pipenv \
  && mkdir ${logdir}
RUN pipenv install --system --deploy

# Server
EXPOSE 3000
ENTRYPOINT ["gunicorn"]
CMD ["--bind", "0.0.0.0:3000", "--timeout", "10000", "-k", "gevent", "--workers", "4", "--preload", "wsgi:app"]
