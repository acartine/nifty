def test_all(client):
    res = client.get('foo')
    assert res.status_code == 404
