FROM python:3.10

COPY /src/requirements.txt /app/requirements.txt

WORKDIR /app
RUN python -m pip install -r requirements.txt

COPY /config/config.ini /app/config/config.ini
COPY /src/nifty_common/ /app/nifty_common
COPY /src/nifty/ /app/nifty
COPY /src/static/ /app/static
COPY /src/app.py /app/app.py

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
