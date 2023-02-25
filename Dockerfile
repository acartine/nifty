FROM python:3.10

# Install pipenv
RUN pip install pipenv

# Compute the hash of your source files
ARG SOURCE_HASH=$(find /src/requirements.txt /src/app.py /src/nifty/ /config.ini /src/nifty_common/ -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)

# Store the hash in an environment variable
ENV SOURCE_HASH=$SOURCE_HASH

# Only copy the sources if the hash has changed
COPY /src/app.py /app/app.py
COPY /src/nifty/ /app/nifty
COPY /src/nifty_common/ /app/nifty_common
COPY config.ini /app/config.ini
COPY /src/requirements.txt /app/requirements.txt

ONBUILD RUN set -e; \
    NEW_HASH=$(find /src/requirements.txt /src/app.py /src/nifty/ /config.ini /src/nifty_common/ -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1); \
    if [ "$SOURCE_HASH" != "$NEW_HASH" ]; then \
        # Perform the COPY step for your sources
        rm -rf /app; \
        COPY /src/app.py /app/app.py; \
        COPY /src/nifty/ /app/nifty; \
        COPY /src/nifty_common/ /app/nifty_common; \
        COPY config.ini /app/config.ini; \
        COPY /src/requirements.txt /app/requirements.txt; \
    fi

# Set the working directory to the app directory
WORKDIR /app

RUN python -m pip install -r requirements.txt

# Run the app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
