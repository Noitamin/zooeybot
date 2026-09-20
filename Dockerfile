FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libopus0 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home bot \
    && mkdir /data \
    && chown bot:bot /data

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY zooey.py .
COPY cogs/ cogs/
COPY utils/ utils/
COPY assets/ assets/
COPY jsons/ jsons/

USER bot
WORKDIR /data
CMD ["python", "/app/zooey.py"]
