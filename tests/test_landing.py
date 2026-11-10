def test_landing_page_is_served(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Sua experi\xc3\xaancia pode" in response.content
