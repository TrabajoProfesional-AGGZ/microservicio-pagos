FROM python:3.12 AS base

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --only-binary :all: --upgrade -r /code/requirements.txt

COPY ./app /code/app

RUN adduser --disabled-password --no-create-home appuser

COPY --chown=appuser:appuser ./app /code/app


FROM base AS production

USER appuser

CMD ["python3", "-m", "app.main"]


FROM base AS development

RUN pip install --no-cache-dir --only-binary :all: watchdog==6.0.0

USER appuser

CMD ["python3", "-m", "app.main"]