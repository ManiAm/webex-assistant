FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV VIRTUAL_ENV=/opt/venv

RUN apt-get update && \
    apt-get install -y \
        libpq-dev \
        gcc \
        python3 \
        python3-pip \
        python3-venv \
        libpq-dev \
        curl \
        git \
        iputils-ping

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade pip && pip install \
    python-dotenv \
    webexpythonsdk \
    langchain \
    langchain-openai \
    langchain-community \
    backoff \
    coloredlogs \
    websockets \
    requests

WORKDIR /app

CMD ["python3", "start.py"]
