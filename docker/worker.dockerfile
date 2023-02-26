FROM python:3.10 as common
COPY /src/nifty_worker/requirements.txt /app/requirements.txt
WORKDIR /app
RUN python -m pip install -r requirements.txt
COPY config.ini /app/config.ini
COPY /src/nifty_common/ /app/nifty_common
COPY /src/nifty_worker/__init__.py /app/nifty_worker/__init__.py
COPY /src/nifty_worker/common/ /app/nifty_worker/common

FROM common AS worker-trend
COPY /src/nifty_worker/trend_worker/ /app/nifty_worker/trend_worker
WORKDIR /app
CMD ["python", "-m", "nifty_worker.trend_worker"]

FROM common AS worker-trend-link
COPY /src/nifty_worker/trend_link_worker/ /app/nifty_worker/trend_link_worker
WORKDIR /app
CMD ["python", "-m", "nifty_worker.trend_link_worker"]
