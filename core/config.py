# pylint: disable=no-name-in-module,import-error,invalid-name
from distutils.util import strtobool
from urllib.parse import urlencode
from os import (
    getenv,
    environ,
)
from pathlib import Path
import jwt

DEBUG = bool(strtobool(getenv('DEBUG', 'True')))  # set DEBUG=False in production
TESTING = bool(strtobool(getenv('TESTING', 'False')))
SQLALCHEMY_ECHO = bool(strtobool(getenv('SQLALCHEMY_ECHO', 'False')))
LOG_GQL = bool(strtobool(getenv('LOG_GQL', 'True')))

BASE_PATH = Path(__file__).parents[1]

SQLALCHEMY_DATABASE_URI = getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + str(
    BASE_PATH / 'temporary-m3-database.sqlite3'))  # switch to PostgreSQL
SQLALCHEMY_POOL_SIZE = 50
SQLALCHEMY_TRACK_MODIFICATIONS = False

COGNITO_AWS_REGION = environ['COGNITO_AWS_REGION']
COGNITO_USER_POOL_ID = environ['COGNITO_USER_POOL_ID']

COGNITO_USER_POOL_URL = f'https://cognito-idp.{COGNITO_AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'
COGNITO_JWKS_URL = COGNITO_USER_POOL_URL + '/.well-known/jwks.json'

JWT_SIGN_ALG_NAME = 'RS256'
PYJWT_SIGN_ALG_CLASS = jwt.algorithms.RSAAlgorithm

COGNITO_USER_SYNC_CRON_EXP = getenv('COGNITO_USER_SYNC_CRON_EXP', '0 11 * * *')

M3_SECRET = environ['M3_SECRET']
M3_SYSTEM_SECRET = environ['M3_SYSTEM_SECRET']

M3_DOMAIN_CATEGORY_NAME = getenv('M3_DOMAIN_CATEGORY_NAME', 'wine')

COGNITO_APP_CLIENT_ID = getenv('COGNITO_APP_CLIENT_ID')
COGNITO_APP_CLIENT_SECRET = getenv('COGNITO_APP_CLIENT_SECRET')

COGNITO_USER_POOL_NAME = getenv('COGNITO_USER_POOL_NAME')
COGNITO_API_BASE_URL = getenv(
    'COGNITO_API_BASE_URL',
    f'https://{COGNITO_USER_POOL_NAME}.auth.{COGNITO_AWS_REGION}.amazoncognito.com'
)

COGNITO_REDIRECT_URI = 'http://localhost:5000/'
COGNITO_LOGIN_PAGE_URL = COGNITO_API_BASE_URL + '/login?' + urlencode({
    'response_type': 'code',
    'client_id': COGNITO_APP_CLIENT_ID,
    'redirect_uri': COGNITO_REDIRECT_URI,
})
COGNITO_TOKEN_API_URL = COGNITO_API_BASE_URL + '/oauth2/token'

AWS_DEFAULT_REGION = getenv('AWS_DEFAULT_REGION', 'us-east-1')

SEARCH_API_URL = getenv('SEARCH_API_URL', '')
INTEGRATION_API_URL = getenv('INTEGRATION_API_URL', '')

EMAIL_SENDER = getenv('EMAIL_SENDER', 'Magia <support@magia.ai>')
SES_CONFIGURATION_SET_NAME = getenv('SES_CONFIGURATION_SET_NAME', 'send_mail_set')

# Celery
CELERY_BROKER_URL = getenv('CELERY_BROKER_URL', 'redis://redis')

# Stripe
STRIPE_SECRET_KEY = getenv('STRIPE_SECRET_KEY', 'sk_test_sGPjOMBUtH2YDEBEGji5C67j')

ADMIN_URL = getenv('ADMIN_URL', 'https://m3-admin.v2-dev.magia.ai')

# Number of days after which the Order's State is notified as timed out
ORDER_TIMEOUT_DAYS = getenv('ORDER_TIMEOUT_DAYS', 2)

PUSH_DOMAIN = getenv('PUSH_DOMAIN', 'magia.com')
PLATFORM_APP_ARN = getenv('PLATFORM_APP_ARN', 'arn:aws:sns:us-east-1:682989504111:app/APNS/magia3_prod')

# Deeplinks for emails
SERVER_DEEPLINK_URL = getenv('SERVER_DEEPLINK_URL', 'https://m3-core.v2-dev.magia.ai/deeplink')
SUBSCRIPTIONS_DEEPLINK = getenv('SUBSCRIPTIONS_DEEPLINK', 'magia://subscriptions')
SHIPMENTS_DEEPLINK_URL = getenv('SHIPMENTS_DEEPLINK_URL','https://magia.ai/account/shipments')

SKIP_PAYMENT = bool(strtobool(getenv('SKIP_PAYMENT', 'False')))
ENABLE_MAGIC_CREDIT_CARD = bool(strtobool(getenv('ENABLE_MAGIC_CREDIT_CARD', 'False')))
MAGIC_CREDIT_CARD_JSON = getenv('MAGIC_CREDIT_CARD_JSON')
