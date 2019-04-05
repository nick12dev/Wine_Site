import json

import pytest


class GraphQLClient:

    def __init__(self, client, api_url, authorization):
        self.client = client
        self.api_url = api_url
        self.authorization = authorization

    def post(self, query, variables=None):
        result = self.client.post(
            self.api_url,
            headers={
                'Authorization': self.authorization,
                'Content-Type': 'application/json',
            },
            json={
                'query': query,
                'variables': variables
            }
        )

        return json.loads(result.data.decode('utf8'))


@pytest.fixture
def graphql_client(client, api_url, valid_jwt):  # corresponds to fixture: user
    return GraphQLClient(client, api_url, 'JWT ' + valid_jwt)


@pytest.fixture
def graphql_client_admin(client, api_url, valid_jwt_admin):  # corresponds to fixture: user2
    return GraphQLClient(client, api_url, 'JWT ' + valid_jwt_admin)


@pytest.fixture
def graphql_client3(client, api_url, valid_jwt3):  # corresponds to fixture: user_no_stripe
    return GraphQLClient(client, api_url, 'JWT ' + valid_jwt3)


@pytest.fixture
def graphql_client_system(client, api_url, valid_system_secret):
    return GraphQLClient(client, api_url, 'SECRET ' + valid_system_secret)


@pytest.fixture
def graphql_client_anonymous(client, api_url, valid_secret):
    return GraphQLClient(client, api_url, 'SECRET ' + valid_secret)
