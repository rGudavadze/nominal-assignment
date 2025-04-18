FROM python:3.12

ENV PYTHONUNBUFFERED 1

RUN mkdir -p /opt/app
WORKDIR /opt/app

COPY requirements.txt /opt/app/

RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

COPY ./app /opt/app/
COPY ./migrations /opt/migrations
COPY ./alembic.ini /opt/alembic.ini

RUN useradd -ms /bin/bash nominal
RUN chown -R nominal:nominal /opt/app

ADD scripts/entrypoint.sh /home/nominal/entrypoint.sh
ADD scripts/check_service.py /home/nominal/check_service.py

RUN chmod +x /home/nominal/entrypoint.sh
USER nominal

ENTRYPOINT ["/home/nominal/entrypoint.sh"]
