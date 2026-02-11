FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy application files
COPY requirements.txt ./
COPY main.py ./
COPY config.json ./
COPY certifications ./certifications

RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p logs

EXPOSE 8085