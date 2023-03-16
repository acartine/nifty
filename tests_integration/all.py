long_url_fixture = (
    "https://askubuntu.com/questions/986525/syntax-error-near-unexpected-token-newline-error-while"
    "-installing-deb-package?noredirect=1&lq=1 "
)


def test_not_found(client):
    res = client.get("/foo")
    assert res.status_code == 404


def test_create_and_lookup(client):
    res = client.post(
        "/shorten",
        json={
            "long_url": "https://www.google.com",
        },
    )
    assert res.json.get("short_url")
    short_url = res.json["short_url"]

    res = client.get(f"/{short_url}")
    assert res.status_code == 302
    assert res.headers.get("Location")
    assert res.headers["Location"] == "https://www.google.com"


def test_reject_invalid_url(client):
    res = client.post(
        "/shorten",
        json={
            "long_url": "foo",
        },
    )
    assert res.status_code == 400
    assert res.json.get("validation_error").get("body_params")
    assert len(res.json["validation_error"]["body_params"]) == 1
    assert (
        res.json["validation_error"]["body_params"][0].get("msg")
        == "invalid or missing URL scheme"
    )


def test_happy_path(client):
    # create new url
    res = client.post(
        "/shorten",
        json={
            "long_url": f"{long_url_fixture}",
        },
    )
    assert res.status_code == 201
    assert res.json.get("short_url")
    short_url = res.json["short_url"]

    # try to create it again
    res = client.post(
        "/shorten",
        json={
            "long_url": f"{long_url_fixture}",
        },
    )
    # already exists, so 200 instead of 201
    assert res.status_code == 200
    assert res.json.get("short_url")
    # same as one we created before
    assert res.json["short_url"] == short_url
