FROM python:3.11-alpine as python-base

ENV \
    PYTHONPATH=/app/src/ \
    PATH=/app/src/:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 

ENV \
    POETRY_VERSION=1.3.2 \
    # Это же сработает вмето последующего "poetry config virtualenvs.create false" ?
    POETRY_VIRTUALENVS_IN_PROJECT=false \ 
    POETRY_NO_INTERACTION=1 


### poetry
FROM python-base as poetry
WORKDIR /tmp

# RUN curl -sSL https://install.python-poetry.org | python3 -
RUN pip install "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml ./
RUN poetry export --dev --without-hashes -o /tmp/requirements.txt


FROM python-base as runtime
WORKDIR /app

COPY --from=poetry /tmp/requirements.txt ./
RUN pip3 install -r requirements.txt
COPY . /app
