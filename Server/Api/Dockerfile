FROM python:3.12-slim

WORKDIR /app

# Copy application files
COPY ./*.py /app/
COPY ./datadomain /app/datadomain
COPY ./db /app/db
COPY ./routers /app/routers

# Copy requirements and other necessary files

COPY ./requirements.txt /app/
COPY ./config.json /app

RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /var/lib/pj-mobius-server
RUN useradd appuser
RUN chown -R appuser:appuser /app
USER appuser

VOLUME /var/lib/pj-mobius-server

EXPOSE 8085

CMD ["uvicorn", "AppEndPoint:app", "--workers", "4", "--host", "0.0.0.0", "--port", "8085"]