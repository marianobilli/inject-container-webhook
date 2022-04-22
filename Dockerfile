FROM python:3.9-slim-bullseye

# port for webhook api
EXPOSE 8443/tcp

# setup app directory with code/user
WORKDIR /app
RUN adduser -u 1001 webapp -q && chown webapp:webapp /app
COPY --chown=webapp:webapp src/* /app

# get required dependencies
COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt && chown webapp:webapp `which uvicorn`

# run as non-root user
USER webapp

# uvicorn will run the fastapi app using mounted tls files
ENTRYPOINT [ "uvicorn", "--host", "0.0.0.0", "--port", "8443", "--ssl-keyfile", "/app/ssl/tls.key", "--ssl-certfile", "/app/ssl/tls.crt", "main:app" ]
