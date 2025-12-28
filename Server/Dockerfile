FROM python:3.12-slim

WORKDIR /app

COPY ./*.py /app/
COPY ./requirements.txt /app/
COPY ./config.mpl /app
COPY ./certifications /run/secrets/certifications

RUN pip install -r requirements.txt
RUN mkdir /var/lib/pj-mobius-server
RUN useradd appuser
RUN chown appuser:appuser /app
RUN chown appuser:appuser /run/secrets/certifications/pj-mobius-key.key
RUN chown appuser:appuser /var/lib/pj-mobius-server

USER appuser

VOLUME /var/lib/pj-mobius-server

EXPOSE 8000

CMD ["uvicorn", "AppEndPoint:app", "--workers", "4", "--host", "0.0.0.0", "--port", "8085", "--ssl-certfile", "/run/secrets/certifications/pj-mobius-cert.crt", "--ssl-keyfile", "/run/secrets/certifications/pj-mobius-key.key"]