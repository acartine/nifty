FROM python:3.10

# Compute the hash of your source files
ARG SOURCE_HASH=$(find  /config.ini /src/nifty_common /src/nifty_worker -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)

# Store the hash in an environment variable
ENV SOURCE_HASH=$SOURCE_HASH

# Only copy the sources if the hash has changed
COPY config.ini /app/config.ini
COPY /src/nifty_common/ /app/nifty_common
COPY /src/nifty_worker/ /app/nifty_worker

ONBUILD RUN set -e; \
    NEW_HASH=$(find /config.ini /src/nifty_common /src/nifty_worker -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1); \
    if [ "$SOURCE_HASH" != "$NEW_HASH" ]; then \
        # Perform the COPY step for your sources
        rm -rf /app; \
        COPY config.ini /app/config.ini; \
        COPY /src/nifty_common/ /app/nifty_common; \
        COPY /src/nifty_worker/ /app/nifty_worker; \
    fi

# Set the working directory to the app directory
WORKDIR /app

RUN python -m pip install -r nifty_worker/requirements.txt

# Run the app using Gunicorn
CMD ["python", "-m", "nifty_worker.trend_worker"]
