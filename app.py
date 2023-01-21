import os
from flask import Flask, send_from_directory, redirect, request, jsonify
import random
import string
import logging
import sys
from store import Store

long_to_short = Store("l2s")
short_to_long = Store("s2l")


# TODO set up blueprints

# TODO move this to config
log_level = os.environ.get('LOG_LEVEL', 'WARN')
log_level_val = getattr(logging, log_level.upper())
print(f"Log level set to {log_level} {log_level_val}")
root = logging.getLogger()
root.setLevel(log_level_val)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(log_level_val)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route('/')
def index():
    # Serve the index.html file from the static directory
    return send_from_directory('static', 'index.html')


# since these are stored in route we will route them directly to avoid 404s
@app.route("/manifest.json")
def manifest():
    return send_from_directory('static', 'manifest.json')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')


# for local development, in prod it would come from nginx
@app.route('/<path:subpath>')
def static_files(subpath):
    # Serve any other files from the static directory
    logger.debug(f"sending {subpath} from 'static'")
    return send_from_directory('static', subpath)


@app.route('/shorten', methods=['POST'])
def shorten():
    # Get the long URL from the request
    long_url = request.json['long_url']

    # Check if the long URL has already been shortened
    short_url = long_to_short.get(long_url)
    if short_url:
        logger.debug(f"found {short_url}")
        # Return the existing short URL if it has been shortened before
        return jsonify({'short_url': short_url})

    # Generate a new short URL
    short_url = generate_short_url()
    logger.debug(f"generated {short_url}")

    # Save the long URL and short URL in the database
    long_to_short.set(long_url, short_url)
    short_to_long.set(short_url, long_url)

    return jsonify({'short_url': short_url})


@app.route('/<short_url>', methods=['GET'])
def lookup(short_url):
    # Look up the long URL for the given short URL
    long_url = short_to_long.get(short_url)

    # Redirect to the long URL if it exists
    if long_url:
        return redirect(long_url)
    else:
        return 'Short URL not found', 404


def generate_short_url():
    # Generate a new short URL
    # This function can use any method for generating short URLs, such as using a
    # counter or hash function
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
