FROM python:3.10

# Install pipenv
RUN pip install pipenv

# Copy the application code and Pipfile.lock file
COPY /src/ /app/
COPY Pipfile.lock /app/Pipfile.lock
COPY Pipfile /app/Pipfile

# Set the working directory to the app directory
WORKDIR /app

# Install the dependencies from the Pipfile.lock file
RUN pipenv install --system --deploy

# Run the app using Gunicorn
CMD ["/usr/local/bin/gunicorn", "-b", "0.0.0.0:5000", "app:app"]
