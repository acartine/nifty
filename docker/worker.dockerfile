FROM python:3.10 as common
COPY /src/nifty_worker/requirements.txt /app/requirements.txt
WORKDIR /app
RUN python -m pip install -r requirements.txt
COPY /config/config.ini /app/config/config.ini
COPY /src/nifty_common/ /app/nifty_common
COPY /src/nifty_worker/__init__.py /app/nifty_worker/__init__.py
COPY /src/nifty_worker/common/ /app/nifty_worker/common

FROM common AS worker-trend
ENV APP_CONTEXT_CFG=trend
COPY /src/nifty_worker/trend/ /app/nifty_worker/trend
COPY /config/trend_config.ini /app/config/trend_config.ini
WORKDIR /app
CMD ["python", "-m", "nifty_worker.trend"]

FROM common AS worker-trend-link
ENV APP_CONTEXT_CFG=trend_link
COPY /src/nifty_worker/trend_link/ /app/nifty_worker/trend_link
COPY /config/trend_link_config.ini /app/config/trend_link_config.ini
WORKDIR /app
CMD ["python", "-m", "nifty_worker.trend_link"]
