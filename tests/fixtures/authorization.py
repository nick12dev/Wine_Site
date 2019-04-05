# pylint: disable=redefined-outer-name
#         (pytest fixtures would not work otherwise)
import json
import uuid
import time

import pytest
import jwt

from core.cognito import transform_jwks


@pytest.fixture
def sample_jwt_header(test_data_folder):
    with open(test_data_folder / 'authorization/sample_jwt_header.json') as file_p:
        return json.load(file_p)


@pytest.fixture
def sample_jwt_payload(test_data_folder):
    with open(test_data_folder / 'authorization/sample_jwt_payload.json') as file_p:
        payload = json.load(file_p)
        payload['sub'] = str(uuid.uuid4())
        return payload


@pytest.fixture
def sample_jwt_payload_hardcoded_sub(test_data_folder):
    with open(test_data_folder / 'authorization/sample_jwt_payload.json') as file_p:
        payload = json.load(file_p)
        return payload


@pytest.fixture
def sample_jwt_payload2(test_data_folder):
    with open(test_data_folder / 'authorization/sample_jwt_payload.json') as file_p:
        payload = json.load(file_p)
        payload['sub'] = str(uuid.uuid4())
        return payload


@pytest.fixture
def sample_jwt_payload3(test_data_folder):
    with open(test_data_folder / 'authorization/sample_jwt_payload.json') as file_p:
        payload = json.load(file_p)
        payload['sub'] = str(uuid.uuid4())
        return payload


@pytest.fixture
def sample_jwt_payload4(test_data_folder):
    with open(test_data_folder / 'authorization/sample_jwt_payload.json') as file_p:
        payload = json.load(file_p)
        payload['sub'] = str(uuid.uuid4())
        return payload


@pytest.fixture
def sample_jwks(test_data_folder):
    with open(test_data_folder / 'authorization/sample_jwks.json') as file_p:
        return json.load(file_p)


@pytest.fixture
def sample_kid():
    return 'nZrIUsBJ+wVi6rf3vyUrUKgMVGKHQlTEhi9iH/wglkg='


@pytest.fixture
def sample_jwk(sample_jwks, sample_kid):
    return transform_jwks(sample_jwks)[sample_kid]


@pytest.fixture
def foreign_jwk_same_kid(test_data_folder):
    with open(test_data_folder / 'authorization/foreign_jwk_same_kid.json') as file_p:
        return json.load(file_p)


@pytest.fixture
def valid_secret():
    return 'wTAo0v3kFQ2Oe2TI8UauRlofkz916WkJe3urkKX1BTf4ROImlqdt0uyw2N7orf5o'


@pytest.fixture
def valid_system_secret():
    return 'Ra99SV36btkzzSLEXxM2MGedeQb24WseHzSwdHG5saZjQ6xQrzA3CR48edfKLMTK'


@pytest.fixture
def valid_jwt(app, sample_jwt_header, sample_jwt_payload, sample_jwk):
    sample_jwt_payload['exp'] = int(time.time()) + 60
    return _create_jwt(app, sample_jwt_header, sample_jwt_payload, sample_jwk)


@pytest.fixture
def valid_jwt_admin(app, sample_jwt_header, sample_jwt_payload2, sample_jwk):
    sample_jwt_payload2['exp'] = int(time.time()) + 60
    sample_jwt_payload2['cognito:groups'] = ['admin']
    return _create_jwt(app, sample_jwt_header, sample_jwt_payload2, sample_jwk)


@pytest.fixture
def valid_jwt3(app, sample_jwt_header, sample_jwt_payload3, sample_jwk):
    sample_jwt_payload3['exp'] = int(time.time()) + 60
    return _create_jwt(app, sample_jwt_header, sample_jwt_payload3, sample_jwk)


@pytest.fixture
def no_signature_jwt(valid_jwt):
    return valid_jwt.rsplit('.', 1)[0]


@pytest.fixture
def almost_empty_jwt(app, sample_jwk, sample_kid):
    jwt_header = {'kid': sample_kid}
    jwt_payload = {'exp': int(time.time()) + 60}
    return _create_jwt(app, jwt_header, jwt_payload, sample_jwk)


@pytest.fixture
def invalid_issuer_jwt(app, sample_jwt_header, sample_jwt_payload, sample_jwk):
    sample_jwt_payload['exp'] = int(time.time()) + 60
    sample_jwt_payload['iss'] = 'https://cognito-idp.eu-central-1.amazonaws.com' \
                                '/eu-central-wRONGpooL'
    return _create_jwt(app, sample_jwt_header, sample_jwt_payload, sample_jwk)


@pytest.fixture
def invalid_token_use_jwt(app, sample_jwt_header, sample_jwt_payload, sample_jwk):
    sample_jwt_payload['exp'] = int(time.time()) + 60
    sample_jwt_payload['token_use'] = 'refresh'
    return _create_jwt(app, sample_jwt_header, sample_jwt_payload, sample_jwk)


@pytest.fixture
def invalid_signature_jwt(app, sample_jwt_header, sample_jwt_payload, foreign_jwk_same_kid):
    sample_jwt_payload['exp'] = int(time.time()) + 60
    return _create_jwt(app, sample_jwt_header, sample_jwt_payload, foreign_jwk_same_kid)


@pytest.fixture
def expired_jwt(app, sample_jwt_header, sample_jwt_payload, sample_jwk):
    sample_jwt_payload['exp'] = int(time.time()) - 60
    return _create_jwt(app, sample_jwt_header, sample_jwt_payload, sample_jwk)


def _create_jwt(app, jwt_header, jwt_payload, jwk):
    private_key = app.config['PYJWT_SIGN_ALG_CLASS'].from_jwk(json.dumps(jwk))
    return jwt.encode(
        jwt_payload,
        private_key,
        algorithm=app.config['JWT_SIGN_ALG_NAME'],
        headers=jwt_header
    ).decode('utf8')
