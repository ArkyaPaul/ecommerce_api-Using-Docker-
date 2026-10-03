#
FROM python:3.10

#
WORKDIR /code

#
COPY requirements.txt /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

#
COPY ./ecommerce_api /code/ecommerce_api
COPY celery_worker.py /code/celery_worker.py

COPY alembic.ini /code/alembic.ini
COPY ./alembic /code/alembic

#
CMD ["uvicorn", "ecommerce_api.main:app", "--host", "0.0.0.0", "--port", "8080"]