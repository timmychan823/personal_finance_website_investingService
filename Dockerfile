FROM pytorch/pytorch:latest
WORKDIR /backend
RUN addgroup --group flask && adduser --ingroup flask flask
COPY requirements.txt /backend
RUN apt-get update && apt-get install -y libpq-dev build-essential curl cron wget && ls -ltr && python -m venv venv && chown -R flask:flask /backend && chmod -R 700 /backend && ls /backend/venv/bin/ -ltr && /backend/venv/bin/activate && pip install -r /backend/requirements.txt
COPY . /backend
RUN chown -R flask:flask /backend && chmod -R 700 /backend && ls -ltr 
USER flask
EXPOSE 5000
ENTRYPOINT ["/bin/sh", "-c" , ". /backend/venv/bin/activate && flask run --host=0.0.0.0 --port=5000"]