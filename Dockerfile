FROM python:latest

WORKDIR /app

RUN pip3 install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

COPY . .

CMD ["poetry", "run", "pytest", "tests"]
