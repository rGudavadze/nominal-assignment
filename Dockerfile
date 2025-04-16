FROM python:3.12

ENV PYTHONUNBUFFERED 1

RUN mkdir -p /opt/app
WORKDIR /opt/app

COPY requirements.txt /opt/app/

RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

COPY ./app /opt/app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
