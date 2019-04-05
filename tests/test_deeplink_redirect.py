from core.config import SUBSCRIPTIONS_DEEPLINK


def test_deeplink_to_star(client):
    response = client.get('/deeplink/subscriptions/')
    assert response.status_code == 302
    assert response.location == SUBSCRIPTIONS_DEEPLINK


def test_deeplink_to_order(client):
    response = client.get('/deeplink/subscriptions/?id=1')
    assert response.status_code == 302
    assert response.location == SUBSCRIPTIONS_DEEPLINK + '/1'
