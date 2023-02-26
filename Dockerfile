FROM python:3.10

COPY config.ini /app/config.ini
COPY /src/requirements.txt /app/requirements.txt
COPY /src/nifty_common/ /app/nifty_common
COPY /src/nifty/ /app/nifty
COPY /src/static/ /app/static
COPY /src/app.py /app/app.py
WORKDIR /app

RUN python -m pip install -r requirements.txt

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
