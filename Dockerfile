FROM python:3.6.0-onbuild
WORKDIR /app
ADD . /app
RUN pip install -r /app/requirements.txt --ignore-installed
ENV CONF local.py
ENV PORT 5000
EXPOSE $PORT
ENV FLASK_APP /app/run.py
ENV FLASK_ENV=production
CMD flask run  -h 0.0.0.0 -p $PORT
