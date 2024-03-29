import logging
from pathlib import Path
from uuid import uuid1

from flask import (
    Flask,
    jsonify,
    redirect,
    send_from_directory,  # pyright: ignore [reportUnknownVariableType]
)
from flask_pydantic import validate
from pydantic import BaseModel, HttpUrl

from .base62 import base62_encode
from .store import store
from nifty.common.types import Link
from nifty.common.helpers import timestamp_ms
from nifty.common import log
from nifty.common.types import Action, ActionType, Channel

log.log_init()

logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder=None)


class ShortenRequest(BaseModel):
    long_url: HttpUrl


@app.route("/")
def index():
    # Serve the index.html file from the static directory
    return send_from_directory("static", "index.html")


# since these are stored in route we will route them directly to avoid 404s
@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.ico")


# for local development, in prod it would come from nginx
@app.route("/<path:subpath>")
def static_files(subpath: Path):
    # Serve any other files from the static directory
    logger.error(f"sending {subpath} from 'static'")
    return send_from_directory("static", subpath)


@app.route("/shorten", methods=["POST"])
@validate()
def shorten(body: ShortenRequest):
    # Get the long URL from the request
    long_url = body.long_url

    # Check if the long URL has already been shortened
    short_url = store.get_short_url(long_url)
    if short_url:
        logger.debug(f"found {short_url}")
        # Return the existing short URL if it has been shortened before
        return jsonify({"short_url": short_url})

    # Upsert the long url
    long_url_id = store.upsert_long_url(long_url)
    short_url = base62_encode(long_url_id)
    logger.debug(f"generated {short_url}")

    # Save the long URL and short URL in the database
    link = store.upsert_link(long_url_id, short_url)

    # TODO maybe do this async after returning the response
    # this is also kinda shady
    store.redis_client.publish(
        Channel.action,
        Action(
            uuid=str(uuid1()),
            type=ActionType.create,
            at=timestamp_ms(),
            link_id=link.id,
        ).json(),
    )

    return jsonify({"short_url": short_url}), 201


@app.route("/nifty/trending", methods={"GET"})
def trending():
    return jsonify(store.get_trending().dict()), 200


@app.route("/<short_url>", methods=["GET"])
def lookup(short_url: str):
    # Look up the long URL for the given short URL
    link: Link | None = store.get_long_url(short_url)

    # Redirect to the long URL if it exists
    if link:
        # TODO maybe move publish into store
        # then we don't have to expose redis client
        store.redis_client.publish(
            Channel.action,
            Action(
                uuid=str(uuid1()),
                type=ActionType.get,
                at=timestamp_ms(),
                link_id=link.id,
            ).json(),
        )
        return redirect(link.long_url)
    else:
        return "Short URL not found", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0")
