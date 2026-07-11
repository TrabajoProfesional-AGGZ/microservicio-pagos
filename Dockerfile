FROM python:3.12 AS base

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

FROM base AS production

CMD ["python3", "-m", "app.main"]

# Development Stage
FROM base AS development

RUN pip install --no-cache-dir watchdog 

# Command for development with auto-reload
CMD ["python3", "-m", "app.main"]