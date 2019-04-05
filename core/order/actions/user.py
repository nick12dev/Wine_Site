import logging
# import json

# import boto3

from core.order.actions.base import (
    Action,
    send_template_email,
)
from core.db.models import (
    PROPOSED_TO_USER_STATE,
    NOTIFY_ACCEPTED_OFFER_ACTION,
    OFFER_ACCEPTED_STATE,
    USER_NOTIFIED_SHIPPED_STATE,
)
from core.dbmethods import (
    get_order,
    get_order_creation_month,
)
from core.dbmethods.user import (
    authorize_payment,
    get_user_order_data,
    payment_should_be_skipped,
)
from core import config


"""
def _send(sns_client, device_token, body):
    endpoint_response = sns_client.create_platform_endpoint(
        PlatformApplicationArn=config.PLATFORM_APP_ARN,
        Token=device_token,
        Attributes={'Enabled': 'true'}
    )
    endpoint_arn = endpoint_response['EndpointArn']

    response = sns_client.publish(
        TargetArn=endpoint_arn,
        MessageStructure='json',
        Message=body
    )
    logging.info('sns publish response: %s', response)


def _send_push_to_devices(device_tokens, body):
    sns = boto3.client('sns', config.AWS_DEFAULT_REGION)

    for token in device_tokens:
        try:
            _send(sns, token, body)
        except Exception as e:
            logging.exception('Error in sending push: %s', e)


def send_silent_push(device_tokens):
    apns_dct = {'aps': {'content-available': 1, 'domain': config.PUSH_DOMAIN, 'sound': ''}}

    body = json.dumps(
        {
            'APNS': json.dumps(apns_dct),
        }
    )

    _send_push_to_devices(device_tokens, body)


def send_push(device_tokens, msg, order_id=None):
    apns_dct = {'aps': {'alert': msg, 'badge': 1, 'domain': config.PUSH_DOMAIN}}
    if order_id:
        apns_dct['aps']['subscriptionId'] = order_id

    body = json.dumps(
        {
            'APNS': json.dumps(apns_dct),
            'default': msg
        }
    )
    _send_push_to_devices(device_tokens, body)

"""


class NotifyUserAction(Action):

    def run(self, order_id):
        logging.info('running NotifyUserAction for order: %s', order_id)
        order = get_order(order_id)
        # device_tokens = [t.token for t in order.user.device_tokens]
        month = get_order_creation_month(order)
        # msg = f'Your {month} wine selections are available! Please confirm quickly to ensure availability.'
        # send_push(device_tokens, msg)
        try:
            send_template_email(
                order.user.email,
                'search_completed',
                {
                    'month': month,
                    'deeplink': config.SHIPMENTS_DEEPLINK_URL   # Goes to webui
                    # 'deeplink': config.SERVER_DEEPLINK_URL + '/subscriptions/',
                }
            )
        except Exception as e:
            logging.exception('Error when sending search_completed mail: %s', e)

        return None, PROPOSED_TO_USER_STATE


class AcceptOfferAction(Action):

    def run(self, order_id):
        logging.info('running ApproveOfferAction order_id: %s', order_id)

        if payment_should_be_skipped(order_id):
            logging.info(f'Skipping payment for order: {order_id}')
        else:
            authorize_payment(order_id)

        return NOTIFY_ACCEPTED_OFFER_ACTION, OFFER_ACCEPTED_STATE


class NotifyUserShippedAction(Action):

    def _send_email(self, order_id):
        order_data = get_user_order_data(order_id)
        send_template_email(
            order_data['shipping_address']['email'], 'order_shipped',
            order_data
        )

    def run(self, order_id):
        logging.info('running NotifyUserShippedAction for order: %s', order_id)
        order = get_order(order_id)
        # device_tokens = [t.token for t in order.user.device_tokens]
        # msg = 'Your order is shipped!'
        # send_push(device_tokens, msg, order_id=order_id)

        try:
            self._send_email(order.id)
        except Exception as e:
            logging.exception('Error when sending shipping email: %s', e)

        return None, USER_NOTIFIED_SHIPPED_STATE
