# pylint: disable=invalid-name
import logging
import json
from functools import wraps

from requests.auth import HTTPBasicAuth
import requests
from flask_principal import (
    RoleNeed,
    Permission,
    Identity,
    IdentityContext,
    AnonymousIdentity,
)
from flask import (
    current_app,
    request,
)
import jwt

from core.cognito_sync import CognitoUserSync
from core.db.models import db
from core.dbmethods.user import (
    populate_most_of_cognito_fields,
    populate_cognito_display_status,
    get_or_create_user,
)
from core.extensions import principal


class CognitoPermission(Permission):
    # pylint: disable=arguments-differ
    def require(self, http_exception=None, pass_identity=False):
        """
        If ``require(..., pass_identity=True)`` is used as a decorator then
        ``flask_principal.Identity`` object will be passed to the function being
        decorated as the last non-keyword argument.
        """
        return CognitoIdentityContext(self, http_exception=http_exception,
                                      pass_identity=pass_identity)


anonymous_user_role_need = RoleNeed('anonymous_user')
system_user_role_need = RoleNeed('system_user')
registered_user_role_need = RoleNeed('registered_user')
admin_user_role_need = RoleNeed('admin_user')

anonymous_user_permission = CognitoPermission(anonymous_user_role_need)
system_user_permission = Permission(system_user_role_need)
registered_user_permission = CognitoPermission(registered_user_role_need)
admin_user_permission = CognitoPermission(admin_user_role_need)


class CognitoIdentityContext(IdentityContext):
    def __init__(self, permission, http_exception=None, pass_identity=False):
        super().__init__(permission, http_exception=http_exception)
        self._pass_identity = pass_identity

    def __call__(self, f):
        if self._pass_identity:
            @wraps(f)
            def _decorated(*args, **kwargs):
                with self as identity:
                    return f(*args, identity, **kwargs)

            return _decorated
        return super().__call__(f)

    def __enter__(self):
        super().__enter__()
        return self.identity


class CognitoUser:
    def __init__(self, jwt_payload, encoded_token):
        self._jwt_payload = jwt_payload
        self._encoded_token = encoded_token

    @property
    def subject(self):
        return self._jwt_payload['sub']

    @property
    def groups(self):
        return self._jwt_payload.get('cognito:groups', ())

    @property
    def encoded_token(self):
        return self._encoded_token

    def __repr__(self):
        return repr(self._jwt_payload)


def _produce_cognito_identity(token):
    if token is None:
        return AnonymousIdentity()

    identity = Identity(
        id=CognitoUser(
            decode_verify_jwt(token, token_uses=('access',)),
            token
        ),
        auth_type='JWT',
    )
    if 'admin' in identity.id.groups:
        identity.provides.add(admin_user_role_need)
        identity.provides.add(system_user_role_need)
    identity.provides.add(registered_user_role_need)
    identity.provides.add(anonymous_user_role_need)
    return identity


@principal.identity_loader
def identity_loader():
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header is None:
            if current_app.debug:
                return _produce_cognito_identity(request.cookies.get('cognito_access_token'))
            raise ValueError('Authorization HTTP header is missing')

        current_app.logger.debug('HTTP Authorization: %s', auth_header)
        auth_header_type, auth_header_token = auth_header.split(maxsplit=1)

        if auth_header_type == 'JWT':
            return _produce_cognito_identity(auth_header_token)

        if auth_header_type == 'SECRET':
            if auth_header_token == current_app.config['M3_SECRET']:
                identity = Identity(id=None, auth_type='SECRET')
                identity.provides.add(anonymous_user_role_need)
                return identity

            if auth_header_token == current_app.config['M3_SYSTEM_SECRET']:
                identity = Identity(id=None, auth_type='SECRET')
                identity.provides.add(system_user_role_need)
                identity.provides.add(anonymous_user_role_need)
                return identity

            raise ValueError('Wrong SECRET')

        raise ValueError('Unsupported HTTP Authorization: ' + auth_header_type)

    except (KeyError, ValueError, jwt.PyJWTError):
        current_app.logger.debug('Invalid credentials', exc_info=True)
    return None


def download_jwks():
    with requests.get(current_app.config['COGNITO_JWKS_URL']) as resp:
        return resp.json()


def transform_jwks(jwks):
    return {k['kid']: k for k in jwks['keys']}


def populate_jwk_dict():
    current_app.config['COGNITO_JWK_DICT'] = transform_jwks(download_jwks())


def decode_verify_jwt(token_encoded, token_uses):
    token_header = jwt.get_unverified_header(token_encoded)

    if current_app.logger.isEnabledFor(logging.DEBUG):
        # logger level checking is needed here because we don't want to invoke
        # jwt.decode(..., verify=False) when debug level is disabled
        current_app.logger.debug(
            'JWT HEADER: %s | JWT PAYLOAD: %s',
            token_header,
            jwt.decode(token_encoded, verify=False)
        )

    jwk = current_app.config['COGNITO_JWK_DICT'][token_header['kid']]
    public_key = current_app.config['PYJWT_SIGN_ALG_CLASS'].from_jwk(json.dumps(jwk))
    token_decoded = jwt.decode(
        token_encoded, public_key, verify=True,
        algorithms=current_app.config['JWT_SIGN_ALG_NAME'],
        # audience=current_app.config['COGNITO_APP_CLIENT_ID'],
        # (not present in access token generated by cognito)
        issuer=current_app.config['COGNITO_USER_POOL_URL']
    )
    if token_decoded['token_use'] not in token_uses:
        raise jwt.InvalidTokenError('Invalid token_use')

    # https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
    return token_decoded


def update_user_from_cognito(
        cognito_sub=None, cognito_user_sync=None, user=None, clear_missing_data=True
):
    if not cognito_user_sync:
        cognito_user_sync = CognitoUserSync(username=cognito_sub)
    cognito_user = cognito_user_sync.get_cognito_user()
    if not user:
        user = get_or_create_user(cognito_sub)

    populate_most_of_cognito_fields(
        user,
        cognito_sub,
        cognito_user,
        attributes_key='UserAttributes',
        clear_missing_data=clear_missing_data,
    )
    populate_cognito_display_status(user)
    db.session.commit()


# The following helps checking Cognito integration without the client app
# (not needed otherwise).


def exchange_auth_code_for_jwts(auth_code):
    with requests.post(
            current_app.config['COGNITO_TOKEN_API_URL'],
            data={
                'grant_type': 'authorization_code',
                'client_id': current_app.config['COGNITO_APP_CLIENT_ID'],
                'redirect_uri': current_app.config['COGNITO_REDIRECT_URI'],
                'code': auth_code,
            },
            auth=HTTPBasicAuth(
                current_app.config['COGNITO_APP_CLIENT_ID'],
                current_app.config['COGNITO_APP_CLIENT_SECRET']
            )
    ) as resp:
        if not resp.ok:
            raise ValueError(f'{resp.status_code} - {resp.reason}: {resp.text}')
    return resp.json()
