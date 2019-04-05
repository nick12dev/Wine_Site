# pylint: disable=attribute-defined-outside-init
import json
import pytest


class TestAuthorization:
    @pytest.fixture(autouse=True)
    def init_fixture(self, client, api_url, domain_cards_query, user_query, domain_category, user):
        self._client = client
        self._api_url = api_url
        self._domain_cards_query = domain_cards_query
        self._user_query = user_query

    def test_valid_secret(self, valid_secret):
        resp = self._request_domain_cards('SECRET ' + valid_secret)
        _assert_graphql_data_returned(resp, 'domainCards')

        resp = self._request_user('SECRET ' + valid_secret)
        _assert_graphql_data_denied(resp, 'user')

    def test_valid_jwt(self, valid_jwt):
        resp = self._request_domain_cards('JWT ' + valid_jwt)
        _assert_graphql_data_returned(resp, 'domainCards')

        resp = self._request_user('JWT ' + valid_jwt)
        _assert_graphql_data_returned(resp, 'user')

    def test_no_auth_header(self):
        resp = self._client.post(
            self._api_url,
            headers={
                'Content-Type': 'application/graphql',
            },
            data=self._domain_cards_query
        )
        assert resp.status_code == 401

        resp = self._client.post(
            self._api_url,
            headers={
                'Content-Type': 'application/graphql',
            },
            data=self._user_query
        )
        assert resp.status_code == 401

    def test_invalid_auth_header(self):
        resp = self._request_domain_cards('invalid-auth-header')
        assert resp.status_code == 401

        resp = self._request_user('invalid-auth-header')
        assert resp.status_code == 401

    def test_invalid_auth_header_type(self, valid_secret, valid_jwt):
        resp = self._request_domain_cards('WRONG-HEADER-TYPE ' + valid_secret)
        assert resp.status_code == 401

        resp = self._request_user('WRONG-HEADER-TYPE ' + valid_secret)
        assert resp.status_code == 401

        resp = self._request_domain_cards('WRONG-HEADER-TYPE ' + valid_jwt)
        assert resp.status_code == 401

        resp = self._request_user('WRONG-HEADER-TYPE ' + valid_jwt)
        assert resp.status_code == 401

    def test_invalid_secret(self):
        resp = self._request_domain_cards('SECRET wRONgKEY')
        assert resp.status_code == 401

        resp = self._request_user('SECRET wRONgKEY')
        assert resp.status_code == 401

    def test_malformed_jwt1(self):
        resp = self._request_domain_cards('JWT mAlFormeD.jw.T')
        assert resp.status_code == 401

        resp = self._request_user('JWT mAlFormeD.jw.T')
        assert resp.status_code == 401

    def test_malformed_jwt2(self):
        resp = self._request_domain_cards('JWT aGVhZGVy.Ym9keQ==.c2lnbmF0dXJl')
        assert resp.status_code == 401

        resp = self._request_user('JWT aGVhZGVy.Ym9keQ==.c2lnbmF0dXJl')
        assert resp.status_code == 401

    def test_malformed_jwt_valid_signature(self, almost_empty_jwt):
        resp = self._request_domain_cards('JWT ' + almost_empty_jwt)
        assert resp.status_code == 401

        resp = self._request_user('JWT ' + almost_empty_jwt)
        assert resp.status_code == 401

    def test_no_signature_jwt(self, no_signature_jwt):
        resp = self._request_domain_cards('JWT ' + no_signature_jwt)
        assert resp.status_code == 401

        resp = self._request_user('JWT ' + no_signature_jwt)
        assert resp.status_code == 401

    def test_invalid_issuer_jwt(self, invalid_issuer_jwt):
        resp = self._request_domain_cards('JWT ' + invalid_issuer_jwt)
        assert resp.status_code == 401

        resp = self._request_user('JWT ' + invalid_issuer_jwt)
        assert resp.status_code == 401

    def test_invalid_token_use_jwt(self, invalid_token_use_jwt):
        resp = self._request_domain_cards('JWT ' + invalid_token_use_jwt)
        assert resp.status_code == 401

        resp = self._request_user('JWT ' + invalid_token_use_jwt)
        assert resp.status_code == 401

    def test_invalid_signature_jwt(self, invalid_signature_jwt):
        resp = self._request_domain_cards('JWT ' + invalid_signature_jwt)
        assert resp.status_code == 401

        resp = self._request_user('JWT ' + invalid_signature_jwt)
        assert resp.status_code == 401

    def test_expired_jwt(self, expired_jwt):
        resp = self._request_domain_cards('JWT ' + expired_jwt)
        assert resp.status_code == 401

        resp = self._request_user('JWT ' + expired_jwt)
        assert resp.status_code == 401

    def _request_api(self, authorization, query):
        return self._client.post(
            self._api_url,
            headers={
                'Authorization': authorization,
                'Content-Type': 'application/graphql',
            },
            data=query
        )

    def _request_domain_cards(self, authorization):
        return self._request_api(authorization, self._domain_cards_query)

    def _request_user(self, authorization):
        return self._request_api(authorization, self._user_query)


def _assert_graphql_data_returned(resp, subkey):
    resp_dict = json.loads(resp.data.decode('utf8'))
    assert resp_dict['data'][subkey] is not None
    assert 'errors' not in resp_dict


def _assert_graphql_data_denied(resp, subkey):
    resp_dict = json.loads(resp.data.decode('utf8'))
    assert resp_dict['data'][subkey] is None
    assert len(resp_dict['errors']) == 1
    assert '401 Unauthorized' in resp_dict['errors'][0]['message']
