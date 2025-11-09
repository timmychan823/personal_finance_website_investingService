FROM pytorch/pytorch:latest
WORKDIR /backend
RUN addgroup --group flask && adduser --ingroup flask flask
COPY requirements.txt /backend
#TODO: see why cant use sudo and apt-get then install libpq-dev, didnt get build-base
RUN apt-get update && apt-get install -y libpq-dev build-essential curl cron wget && ls -ltr && python -m venv venv && chown -R flask:flask /backend && chmod -R 700 /backend && ls /backend/venv/bin/ -ltr && /backend/venv/bin/activate && pip install -r /backend/requirements.txt && wget http://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_142.0.7444.59-1_amd64.deb && dpkg -i google-chrome-stable_142.0.7444.59-1_amd64.deb && apt-get install -f && wget https://chromedriver.storage.googleapis.com/142.0.7444.59/chromedriver_linux64.zip && unzip chromedriver_linux64.zip && mv chromedriver /usr/bin/chromedriver && chown flask:flask /usr/bin/chromedriver && chmod +x /usr/bin/chromedriver && rm google-chrome-stable_142.0.7444.59-1_amd64.deb chromedriver_linux64.zip
COPY . /backend
RUN systemctl start cron && systemctl enable cron && crontab /backend/cronjobs.txt
RUN chown -R flask:flask /backend && chmod -R 700 /backend && ls -ltr 
USER flask
EXPOSE 5000
ENTRYPOINT ["/bin/sh", "-c" , ". /backend/venv/bin/activate && flask run --host=0.0.0.0 --port=5000"]