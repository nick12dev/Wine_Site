import json

import logging

import graphene
import boto3
from botocore.exceptions import ClientError

from core import config

CHARSET = 'UTF-8'


class Action:

    def run(self, order_id):
        raise NotImplementedError


def send_mail(mail_to, subject, message):
    client = boto3.client('ses', config.AWS_DEFAULT_REGION)
    msg = {
        'Subject': {
            'Charset': CHARSET,
            'Data': subject,
        },
        'Body': {
            'Text': {
                'Charset': CHARSET,
                'Data': message
            }

        }
    }
    try:
        client.send_email(
            Destination={'ToAddresses': [mail_to]},
            Message=msg,
            Source=config.EMAIL_SENDER
        )
    except ClientError as e:
        logging.error(
            'Error when sending email to: %s; Error: %s',
            mail_to, e.response['Error']['Message']
        )
        raise


def send_template_email(mail_to, template_name, template_data):
    client = boto3.client('ses', config.AWS_DEFAULT_REGION)

    try:
        client.send_templated_email(
            Source=config.EMAIL_SENDER,
            Destination={'ToAddresses': [mail_to]},
            ConfigurationSetName=config.SES_CONFIGURATION_SET_NAME,
            Template=template_name,
            TemplateData=json.dumps(template_data)
        )
    except ClientError as e:
        logging.error(
            'Error when sending email to: %s, template: %s, template_data: %s, Error: %s.',
            mail_to, template_name, template_data, e.response['Error']['Message']
        )


def get_admin_order_url(order_id):
    return config.ADMIN_URL + '/orders/order/%s' % \
           graphene.Node.to_global_id('Order', order_id)
