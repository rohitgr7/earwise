FROM python:3.9.16-slim as base

COPY requirements/backend.txt /tmp/backend.txt
COPY ./backend /backend
COPY ./whisper_setup.sh /whisper_setup.sh

ENV MAX_WORKERS="1"
ENV WEB_CONCURRENCY="1"

RUN apt-get update && \
    apt-get install -y git make gcc g++ wget && \
    rm -rf /var/lib/apt/lists/* && \
    python -m pip install --upgrade pip && \
    python -m pip install torch==1.13.1 --extra-index-url https://download.pytorch.org/whl/cpu && \
    python -m pip install -r /tmp/backend.txt

EXPOSE 8005
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8005"]
