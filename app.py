import os
from flask import Flask, send_from_directory, redirect, request, jsonify
import redis
import random
import string
import logging
import sys

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

app = Flask(__name__)

# for local usage, add 'localhost' to your .env
redis_host = os.environ.get('REDIS_HOST', 'redis')
logging.info(f"Using '{redis_host}'")

r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

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
    logging.debug(f"sending {subpath} from 'static'")
    return send_from_directory('static', subpath)

@app.route('/shorten', methods=['POST'])
def shorten():
    # Get the long URL from the request
    long_url = request.json['long_url']

    # Check if the long URL has already been shortened
    short_url = r.get(long_url)
    if short_url:
        logging.debug(f"found {short_url}")
        # Return the existing short URL if it has been shortened before
        return jsonify({'short_url': short_url})

    # Generate a new short URL
    short_url = generate_short_url()
    logging.debug(f"generated {short_url}")

    # Save the long URL and short URL in the database
    r.set(long_url, short_url)
    r.set(short_url, long_url)

    return jsonify({'short_url': short_url})

@app.route('/<short_url>', methods=['GET'])
def lookup(short_url):
    # Look up the long URL for the given short URL
    long_url = r.get(short_url)

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
