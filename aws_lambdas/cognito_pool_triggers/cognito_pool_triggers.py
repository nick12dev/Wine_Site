# pylint: disable=invalid-name
import os
import json
import logging
from urllib import request as urllib_request


def try_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


logger = logging.getLogger()
logger.setLevel(try_int(os.getenv('LOG_LEVEL', logging.WARNING)))

M3_CORE_ENDPOINT_URL = os.getenv('M3_CORE_ENDPOINT_URL')
M3_SYSTEM_SECRET = os.getenv('M3_SYSTEM_SECRET')


def lambda_handler(event, context):
    try:
        logger.debug('EVENT: %r', event)
        mutation_query = {
            'query': 'mutation updateUserFromCognito($input: UpdateUserFromCognitoInput!) '
                     '{updateUserFromCognito(input: $input) {clientMutationId}}',
            'variables': {
                'input': {
                    'lambdaEvent': json.dumps(event),
                },
            },
        }
        req = urllib_request.Request(
            M3_CORE_ENDPOINT_URL,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'SECRET ' + M3_SYSTEM_SECRET,
            },
            data=json.dumps(mutation_query).encode('utf8'),
        )
        with urllib_request.urlopen(req) as resp:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('M3-CORE RESPONSE: %r', json.load(resp, encoding='utf8'))
    except:
        logger.exception('FAILED TO UPDATE USER IN M3-CORE. EVENT: %r', event)
    return None
