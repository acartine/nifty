FROM python:3.10

COPY /nifty/service/requirements.txt /app/requirements.txt

WORKDIR /app
RUN python -m pip install -r requirements.txt

ENV APP_CONTEXT_CFG=nifty
COPY /config/config.ini /app/config/config.ini
COPY /config/nifty_config.ini /app/config/nifty_config.ini
COPY /nifty/common/ /app/nifty/common
COPY /nifty/service /app/nifty/service


ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:5000", "nifty.service.app:app"]
