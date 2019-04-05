# pylint: disable=invalid-name
import os
import json
import logging

import boto3


def try_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


logger = logging.getLogger()
logger.setLevel(try_int(os.getenv('LOG_LEVEL', logging.WARNING)))

FUNCTION_NAME = os.getenv('FUNCTION_NAME')

lmbd = boto3.client('lambda')


def lambda_handler(event, context):
    try:
        logger.debug('EVENT: %r', event)
        logger.debug('ASYNCHRONOUS CALL FROM %s TO %s', context.function_name, FUNCTION_NAME)
        if FUNCTION_NAME == context.function_name:
            raise ValueError('ATTENTION! %s ATTEMPTED TO CALL ITSELF RECURSIVELY', context.function_name)
        resp = lmbd.invoke(
            FunctionName=FUNCTION_NAME,
            InvocationType='Event',
            Payload=json.dumps(event).encode('utf8'),
        )
        logger.debug('LAMBDA INVOKE EVENT RESPONSE: %r', resp)
    except:
        logger.exception('FAILED TO INVOKE %s. EVENT: %r', FUNCTION_NAME, event)
    logger.debug('RESPONSE: %r', event)
    return event
