FROM python:3.11 as common
COPY /nifty/worker/requirements.txt /app/requirements.txt
WORKDIR /app
RUN python -m pip install -r requirements.txt
COPY /config/config.ini /app/config/config.ini
COPY /nifty/common/ /app/nifty/common
COPY /nifty/worker/__init__.py /app/nifty/worker/__init__.py
COPY /nifty/worker/common/ /app/nifty/worker/common

FROM common AS worker-trend
ENV APP_CONTEXT_CFG=trend
COPY /nifty/worker/trend.py /app/nifty/worker/trend.py
COPY /nifty/worker/toplist/ /app/nifty/worker/toplist
COPY /config/trend_config.ini /app/config/trend_config.ini
WORKDIR /app
CMD ["python", "-m", "nifty.worker.trend"]

FROM common AS worker-trend-link
ENV APP_CONTEXT_CFG=trend_link
COPY /nifty/worker/trend_link.py /app/nifty/worker/trend_link.py
COPY /config/trend_link_config.ini /app/config/trend_link_config.ini
WORKDIR /app
CMD ["python", "-m", "nifty.worker.trend_link"]
