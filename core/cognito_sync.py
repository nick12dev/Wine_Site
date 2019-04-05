import logging

import base64
import boto3
import hmac

import hashlib

from core import config
from core.db.models import db
from core.db.models.user import User
from core.dbmethods.user import (
    populate_most_of_cognito_fields,
    populate_cognito_display_status,
    create_user,
)
from core.order import celery_app

DISABLE_COGNITO_ACTION = 'disable'
ENABLE_COGNITO_ACTION = 'enable'


@celery_app.task
def run_full_cognito_user_sync():
    logging.info('Started full Cognito user synchronization (scheduled)...')
    full_user_sync = FullCognitoUserSync()
    full_user_sync()
    logging.info('Finished full Cognito user synchronization')
    full_user_sync.stats_to_dict()


def _get_secret_hash(username):
    # A keyed-hash message authentication code (HMAC) calculated using
    # the secret key of a user pool client and username plus the client
    # ID in the message.
    # https://stackoverflow.com/a/44245099
    message = username + config.COGNITO_APP_CLIENT_ID
    dig = hmac.new(
        config.COGNITO_APP_CLIENT_SECRET.encode('utf8'),
        msg=message.encode('utf8'),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()


class CognitoUserSync:
    def __init__(self, access_token=None, username=None):
        self._access_token = access_token
        self._username = username

        self._client = boto3.client(
            'cognito-idp',
            region_name=config.COGNITO_AWS_REGION,
        )

    def get_cognito_user(self):
        if self._username is not None:
            return self._client.admin_get_user(
                UserPoolId=config.COGNITO_USER_POOL_ID,
                Username=self._username,
            )
        return self._client.get_user(
            AccessToken=self._access_token
        )

    def sign_up(self, email, phone, password):
        res = self._client.sign_up(
            ClientId=config.COGNITO_APP_CLIENT_ID,
            SecretHash=_get_secret_hash(email),
            Username=email,
            Password=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email,
                },
                {
                    'Name': 'phone_number',
                    'Value': phone,
                },
            ],
        )
        return res.get('UserSub')

    def delete_cognito_user(self):
        return self._client.admin_delete_user(
            UserPoolId=config.COGNITO_USER_POOL_ID,
            Username=self._username,
        )

    def update_cognito_user(
            self,
            attributes=(),
            old_password=None,
            new_password=None,
            cognito_action=None
    ):
        cognito_updated = False

        if not (cognito_action is not None or attributes or (old_password and new_password)):
            return cognito_updated

        if cognito_action is not None:
            if self._username is None:
                raise ValueError(
                    'Cognito username (subject) was not provided '
                    '(admin user\'s privilege is required)'
                )

            if cognito_action == ENABLE_COGNITO_ACTION:
                self._client.admin_enable_user(
                    UserPoolId=config.COGNITO_USER_POOL_ID,
                    Username=self._username,
                )
                cognito_updated = True
            elif cognito_action == DISABLE_COGNITO_ACTION:
                self._client.admin_disable_user(
                    UserPoolId=config.COGNITO_USER_POOL_ID,
                    Username=self._username,
                )
                cognito_updated = True

        if attributes:
            if self._username is not None:
                try:
                    self._client.admin_update_user_attributes(
                        UserPoolId=config.COGNITO_USER_POOL_ID,
                        Username=self._username,
                        UserAttributes=attributes
                    )
                    cognito_updated = True
                except self._client.exceptions.UserNotFoundException:
                    # do not fail saveUser mutation for users that are not in Cognito
                    # (some users may have been deleted from Cognito manually)
                    logging.exception(
                        'Failed to update user attributes in cognito for user %s', self._username
                    )
            else:
                self._client.update_user_attributes(
                    UserAttributes=attributes,
                    AccessToken=self._access_token
                )
                cognito_updated = True

        if old_password and new_password:
            if self._username is not None:
                raise ValueError('Explicitly setting passwords for users by admin is not supported')
            else:
                self._client.change_password(
                    PreviousPassword=old_password,
                    ProposedPassword=new_password,
                    AccessToken=self._access_token
                )
                cognito_updated = True

        return cognito_updated


class FullCognitoUserSync:
    def __init__(self):
        self.successfully_updated_count = 0
        self.successfully_added_count = 0
        self.exceptions_count = 0
        self.not_connected_to_cognito_count = 0
        self.not_found_in_cognito_count = 0
        self.cognito_list_complete = False

        self._client = boto3.client(
            'cognito-idp',
            region_name=config.COGNITO_AWS_REGION,
        )

        self._cognito_user_dict = {}

    def stats_to_dict(self):
        stats = {
            'successfully_updated_count': self.successfully_updated_count,
            'successfully_added_count': self.successfully_added_count,
            'not_connected_to_cognito_count': self.not_connected_to_cognito_count,
            'not_found_in_cognito_count': self.not_found_in_cognito_count,
            'exceptions_count': self.exceptions_count,
            'cognito_list_complete': self.cognito_list_complete,
        }
        logging.info(
            'Full Cognito user sync results: '
            'successfully_updated_count=%(successfully_updated_count)r; '
            'successfully_added_count=%(successfully_added_count)r; '
            'not_connected_to_cognito_count=%(not_connected_to_cognito_count)r; '
            'not_found_in_cognito_count=%(not_found_in_cognito_count)r; '
            'exceptions_count=%(exceptions_count)r; '
            'cognito_list_complete=%(cognito_list_complete)r',
            stats
        )
        return stats

    def __call__(self):
        list_users_parameters = {
            'UserPoolId': config.COGNITO_USER_POOL_ID,
            'AttributesToGet': ['email', 'phone_number', 'email_verified', 'phone_number_verified'],
        }

        cognito_list_users_resp = self._client.list_users(
            **list_users_parameters
        )
        self._populate_cognito_user_dict(cognito_list_users_resp)
        pagination_token = cognito_list_users_resp.get('PaginationToken')
        while pagination_token:
            cognito_list_users_resp = self._client.list_users(
                PaginationToken=pagination_token,
                **list_users_parameters
            )
            self._populate_cognito_user_dict(cognito_list_users_resp)
            pagination_token = cognito_list_users_resp.get('PaginationToken')

        self.cognito_list_complete = True

        self._process_cognito_user_dict()
        self._process_absent_cognito_users()

        db.session.commit()

        return self

    def _populate_cognito_user_dict(self, cognito_list_users_resp):
        for cognito_user in cognito_list_users_resp['Users']:
            cognito_sub = cognito_user.get('Username')
            if cognito_sub:
                self._cognito_user_dict[cognito_sub] = cognito_user
            else:
                self.exceptions_count += 1
                logging.warning(
                    "Failed to load cognito user ('Username' is blank): %s",
                    cognito_user
                )

    def _process_cognito_user_dict(self):
        for user in User.query.all():
            try:
                if user.cognito_sub:
                    self._sync_user_with_cognito(user)
                else:
                    self._mark_user_as_not_connected(user)
            except:
                self.exceptions_count += 1
                logging.exception(
                    'Exception while processing user with id=%s and cognito_sub=%s',
                    user.id, user.cognito_sub
                )

    def _process_absent_cognito_users(self):
        for absent_user_subject, absent_user in self._cognito_user_dict.items():
            try:
                logging.warning(
                    "Cognito user with subject=%s is not present in the database - inserting...",
                    absent_user_subject,
                )
                user = create_user(absent_user_subject)
                populate_most_of_cognito_fields(user, absent_user_subject, absent_user)
                populate_cognito_display_status(user)
                self.successfully_added_count += 1
            except:
                self.exceptions_count += 1
                logging.exception(
                    'Exception while adding user with cognito_sub=%s to the database',
                    absent_user_subject
                )

    def _sync_user_with_cognito(self, user):
        cognito_user = self._cognito_user_dict.pop(user.cognito_sub, None)
        if cognito_user:
            populate_most_of_cognito_fields(user, user.cognito_sub, cognito_user)
            populate_cognito_display_status(user)
            self.successfully_updated_count += 1
        else:
            logging.warning(
                "Database user with id=%s and cognito_sub=%s was not found in Cognito",
                user.id, user.cognito_sub,
            )
            if self.cognito_list_complete:
                user.exists_in_cognito = False
                user.cognito_enabled = False
                user.cognito_status = 'NOT_FOUND_IN_COGNITO'

                populate_cognito_display_status(user)
                self.not_found_in_cognito_count += 1

    def _mark_user_as_not_connected(self, user):
        logging.warning(
            "Database user with id=%s doesn't have cognito_sub assigned",
            user.id,
        )
        user.exists_in_cognito = False
        user.cognito_enabled = False
        user.cognito_status = 'NOT_CONNECTED_TO_COGNITO'
        populate_cognito_display_status(user)
        self.not_connected_to_cognito_count += 1
