FROM python:3.13-alpine3.21
WORKDIR /backend
RUN addgroup -S flask && adduser -S flask -G flask
COPY requirements.txt /backend
#TODO: see why cant use sudo and apt-get then install libpq-dev
RUN apk add libpq-dev build-base curl && ls -ltr && python -m venv venv && chown -R flask:flask /backend && chmod -R 700 /backend && ls /backend/venv/bin/ -ltr && /backend/venv/bin/activate && pip install -r /backend/requirements.txt
COPY . /backend
RUN chown -R flask:flask /backend && chmod -R 700 /backend && ls -ltr 
USER flask
EXPOSE 5000
ENTRYPOINT ["/bin/sh", "-c" , "source /backend/venv/bin/activate && flask run --host=0.0.0.0 --port=5000"]