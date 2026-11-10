def test_landing_page_is_served(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Sua experi\xc3\xaancia pode" in response.content
    assert b'/static/css/app.css?v=4.3.5' in response.content


def test_css_compilado_e_encontrado_pelo_staticfiles_finder():
    from django.contrib.staticfiles import finders

    css_path = finders.find("css/app.css")

    assert css_path is not None
