long_url_fixture = "https://askubuntu.com/questions/986525/syntax-error-near-unexpected-token-newline-error-while" \
                   "-installing-deb-package?noredirect=1&lq=1 "


def test_not_found(client):
    res = client.get('/foo')
    assert res.status_code == 404


def test_happy_path(client):
    # create new url
    res = client.post('/shorten', json={
        "long_url": f"{long_url_fixture}",
    })
    assert res.status_code == 201
    assert res.json.get('short_url')
    short_url = res.json['short_url']

    # try to create it again
    res = client.post('/shorten', json={
        "long_url": f"{long_url_fixture}",
    })
    # already exists, so 200 instead of 201
    assert res.status_code == 200
    assert res.json.get('short_url')
    # same as one we created before
    assert res.json['short_url'] == short_url
