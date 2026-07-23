FROM python:3.12 AS base

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes -r /code/requirements.txt

COPY ./app /code/app

RUN adduser --disabled-password --no-create-home appuser

COPY --chown=appuser:appuser ./app /code/app


FROM base AS production

USER appuser

CMD ["python3", "-m", "app.main"]


FROM base AS development

COPY ./requirements-dev.txt /code/requirements-dev.txt
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes -r /code/requirements-dev.txt

USER appuser

CMD ["python3", "-m", "app.main"]