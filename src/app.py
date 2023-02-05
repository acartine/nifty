import logging
import random
import string
import sys
import time

from flask import Flask, send_from_directory, redirect, jsonify
from flask_pydantic import validate
from pydantic import BaseModel, HttpUrl

from nifty.base62 import base62_encode
from nifty_common.config import cfg
from nifty.store import get_short_url, upsert_long_url, upsert_link, get_long_url, redis_client
from nifty_common.types import Action, Channel, ActionType

# TODO set up blueprints

log_level = cfg['logging'].get('level', 'WARN')
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


class ShortenRequest(BaseModel):
    long_url: HttpUrl


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
@validate()
def shorten(body: ShortenRequest):
    # Get the long URL from the request
    long_url = body.long_url

    # Check if the long URL has already been shortened
    short_url = get_short_url(long_url)
    if short_url:
        logger.debug(f"found {short_url}")
        # Return the existing short URL if it has been shortened before
        return jsonify({'short_url': short_url})

    # Upsert the long url
    long_url_id = upsert_long_url(long_url)
    short_url = base62_encode(long_url_id)
    logger.debug(f"generated {short_url}")

    # Save the long URL and short URL in the database
    upsert_link(long_url_id, short_url)

    return jsonify({'short_url': short_url}), 201


@app.route('/<short_url>', methods=['GET'])
def lookup(short_url):
    # Look up the long URL for the given short URL
    long_url = get_long_url(short_url)

    # Redirect to the long URL if it exists
    if long_url:
        redis_client.publish(Channel.action,
                             Action(type=ActionType.get,
                                    at=int(time.time()),
                                    url=short_url).json())
        return redirect(long_url)
    else:
        return 'Short URL not found', 404





if __name__ == '__main__':
    app.run(host='0.0.0.0')
