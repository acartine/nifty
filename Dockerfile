FROM python:3.10

# Install pipenv
RUN pip install pipenv

# Compute the hash of your source files
ARG SOURCE_HASH=$(find /src/ /config.ini -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1)

# Store the hash in an environment variable
ENV SOURCE_HASH=$SOURCE_HASH

# Only copy the sources if the hash has changed
COPY /src/ /app
COPY config.ini /app/config.ini
ONBUILD RUN set -e; \
    NEW_HASH=$(find /src/ /config.ini -type f -exec sha256sum {} \; | sha256sum | cut -d' ' -f1); \
    if [ "$SOURCE_HASH" != "$NEW_HASH" ]; then \
        # Perform the COPY step for your sources
        rm -rf /app/src /app/config.ini; \
        COPY /src/ /app; \
        COPY config.ini /app/config.ini; \
    fi

# Copy the Pipfile.lock file
COPY Pipfile.lock /app/Pipfile.lock
COPY Pipfile /app/Pipfile

# Set the working directory to the app directory
WORKDIR /app

# Install the dependencies from the Pipfile.lock file
RUN pipenv install --system --deploy

# Run the app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
