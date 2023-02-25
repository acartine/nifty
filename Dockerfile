FROM python:3.10

# Compute the hash of your source files
ARG SOURCE_HASH=$(find /config.ini /src/requirements.txt /src/nifty_common/ /src/nifty/ /src/app.py -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)

# Store the hash in an environment variable
ENV SOURCE_HASH=$SOURCE_HASH

# Only copy the sources if the hash has changed
COPY config.ini /app/config.ini
COPY /src/requirements.txt /app/requirements.txt
COPY /src/nifty_common/ /app/nifty_common
COPY /src/nifty/ /app/nifty
COPY /src/app.py /app/app.py

ONBUILD RUN set -e; \
    NEW_HASH=$(find /config.ini /src/requirements.txt /src/nifty_common/ /src/nifty/ /src/app.py -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1); \
    if [ "$SOURCE_HASH" != "$NEW_HASH" ]; then \
        # Perform the COPY step for your sources
        rm -rf /app; \
        COPY config.ini /app/config.ini; \
        COPY /src/requirements.txt /app/requirements.txt; \
        COPY /src/nifty_common/ /app/nifty_common; \
        COPY /src/nifty/ /app/nifty; \
        COPY /src/app.py /app/app.py; \
    fi

# Set the working directory to the app directory
WORKDIR /app

RUN python -m pip install -r requirements.txt

# Run the app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
