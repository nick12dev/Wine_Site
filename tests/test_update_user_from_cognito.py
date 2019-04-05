# pylint: disable=invalid-name,unused-argument
import datetime
from unittest.mock import patch, MagicMock

from core.db.models.user import User

update_user_from_cognito_query = '''
    mutation updateUserFromCognito($input: UpdateUserFromCognitoInput!)
    {updateUserFromCognito(input: $input) {clientMutationId}}
'''

presignup_signup_event = '{"version": "1", ' \
                         '"region": "us-east-1", ' \
                         '"userPoolId": "us-east-1_nyoFFfn5v", ' \
                         '"userName": "69de7e78-1bf6-4175-bbf8-3a29834d1bc0", ' \
                         '"callerContext": ' \
                         '{"awsSdkVersion": "aws-sdk-ios-2.6.29", ' \
                         '"clientId": "ftooh8142vs9731uj99llrgdl"}, ' \
                         '"triggerSource": "PreSignUp_SignUp", ' \
                         '"request": ' \
                         '{"userAttributes": ' \
                         '{"phone_number": "+113311122289", ' \
                         '"email": "update-from-cognito@test.com"}, ' \
                         '"validationData": ' \
                         '{"cognito:iOSVersion": "11.0", ' \
                         '"cognito:bundleShortV": "1.0", ' \
                         '"cognito:idForVendor": "D73839AF-9D60-463C-9563-FBEC91A541DD", ' \
                         '"cognito:bundleVersion": "47", ' \
                         '"cognito:systemName": "iOS", ' \
                         '"cognito:bundleId": "com.magia.ai", ' \
                         '"cognito:deviceName": "iPhone", ' \
                         '"cognito:model": "iPhone"}}, ' \
                         '"response": {"autoConfirmUser": false, ' \
                         '"autoVerifyEmail": false, ' \
                         '"autoVerifyPhone": false}}'

postconfirmation_confirmsignup = '{"version": "1", ' \
                                 '"region": "us-east-1", ' \
                                 '"userPoolId": "us-east-1_nyoFFfn5v", ' \
                                 '"userName": "69de7e78-1bf6-4175-bbf8-3a29834d1bc0", ' \
                                 '"callerContext": ' \
                                 '{"awsSdkVersion": "aws-sdk-unknown-unknown", ' \
                                 '"clientId": "ftooh8142vs9731uj99llrgdl"}, ' \
                                 '"triggerSource": "PostConfirmation_ConfirmSignUp", ' \
                                 '"request": ' \
                                 '{"userAttributes": ' \
                                 '{"sub": "69de7e78-1bf6-4175-bbf8-3a29834d1bc0", ' \
                                 '"cognito:email_alias": "update-from-cognito@test.com", ' \
                                 '"cognito:user_status": "CONFIRMED", ' \
                                 '"email_verified": "false", ' \
                                 '"phone_number_verified": "true", ' \
                                 '"phone_number": "+113311122289", ' \
                                 '"email": "update-from-cognito@test.com"}}, ' \
                                 '"response": {}}'

unconfirmed_cognito_user_response = {
    'Enabled': True,
    'ResponseMetadata': {'HTTPHeaders': {'connection': 'keep-alive',
                                         'content-length': '430',
                                         'content-type': 'application/x-amz-json-1.1',
                                         'date': 'Fri, 30 Nov 2018 14:43:13 GMT',
                                         'x-amzn-requestid': '43e8b0d8-f4ae-11e8-acc3-f50b8cef0d4b'},
                         'HTTPStatusCode': 200,
                         'RequestId': '43e8b0d8-f4ae-11e8-acc3-f50b8cef0d4b',
                         'RetryAttempts': 0},
    'UserAttributes': [{'Name': 'sub', 'Value': '69de7e78-1bf6-4175-bbf8-3a29834d1bc0'},
                       {'Name': 'email_verified', 'Value': 'false'},
                       {'Name': 'phone_number_verified', 'Value': 'false'},
                       {'Name': 'phone_number', 'Value': '+113311122289'},
                       {'Name': 'email', 'Value': 'update-from-cognito@test.com'}],
    'UserCreateDate': datetime.datetime(2018, 11, 30, 15, 7, 14, 242000),
    'UserLastModifiedDate': datetime.datetime(2018, 11, 30, 15, 8, 8, 858000),
    'UserStatus': 'UNCONFIRMED',
    'Username': '69de7e78-1bf6-4175-bbf8-3a29834d1bc0'}

confirmed_cognito_user_response = {
    'Enabled': True,
    'ResponseMetadata': {'HTTPHeaders': {'connection': 'keep-alive',
                                         'content-length': '430',
                                         'content-type': 'application/x-amz-json-1.1',
                                         'date': 'Fri, 30 Nov 2018 14:43:13 GMT',
                                         'x-amzn-requestid': '43e8b0d8-f4ae-11e8-acc3-f50b8cef0d4b'},
                         'HTTPStatusCode': 200,
                         'RequestId': '43e8b0d8-f4ae-11e8-acc3-f50b8cef0d4b',
                         'RetryAttempts': 0},
    'UserAttributes': [{'Name': 'sub', 'Value': '69de7e78-1bf6-4175-bbf8-3a29834d1bc0'},
                       {'Name': 'email_verified', 'Value': 'true'},
                       {'Name': 'phone_number_verified', 'Value': 'true'},
                       {'Name': 'phone_number', 'Value': '+113311122289'},
                       {'Name': 'email', 'Value': 'update-from-cognito@test.com'}],
    'UserCreateDate': datetime.datetime(2018, 11, 30, 15, 7, 14, 242000),
    'UserLastModifiedDate': datetime.datetime(2018, 11, 30, 15, 8, 8, 858000),
    'UserStatus': 'CONFIRMED',
    'Username': '69de7e78-1bf6-4175-bbf8-3a29834d1bc0'}


@patch('core.cognito_sync.boto3')
def test_create_user_from_cognito(boto_m, graphql_client_system, wine_expert):
    boto_client_m = MagicMock()
    boto_m.client.return_value = boto_client_m

    boto_client_m.admin_get_user.return_value = unconfirmed_cognito_user_response

    assert User.query.filter(
        User.cognito_sub == '69de7e78-1bf6-4175-bbf8-3a29834d1bc0'
    ).first() is None

    res = graphql_client_system.post(update_user_from_cognito_query, variables={
        'input': {
            'clientMutationId': 'triggertest',
            'lambdaEvent': presignup_signup_event,
        },
    })
    expected = {'data': {'updateUserFromCognito': {'clientMutationId': 'triggertest'}}}
    assert res == expected

    user = User.query.filter(
        User.cognito_sub == '69de7e78-1bf6-4175-bbf8-3a29834d1bc0'
    ).one()
    assert user.exists_in_cognito is True
    assert user.cognito_enabled is True
    assert user.cognito_status == 'UNCONFIRMED'
    assert user.cognito_display_status == 'Enabled / UNCONFIRMED'
    assert user.phone == '+113311122289'
    assert user.cognito_phone_verified is False
    assert user.email == 'update-from-cognito@test.com'
    assert user.cognito_email_verified is False


@patch('core.cognito_sync.boto3')
def test_update_user_from_cognito(boto_m, graphql_client_system, user_hardcoded_sub):
    boto_client_m = MagicMock()
    boto_m.client.return_value = boto_client_m

    boto_client_m.admin_get_user.return_value = confirmed_cognito_user_response

    existing_user = User.query.filter(
        User.cognito_sub == '69de7e78-1bf6-4175-bbf8-3a29834d1bc0'
    ).one()
    assert existing_user.exists_in_cognito is None
    assert existing_user.cognito_enabled is False
    assert existing_user.cognito_status == 'UNKNOWN'
    assert existing_user.cognito_display_status == 'UNKNOWN'
    assert existing_user.phone is None
    assert existing_user.cognito_phone_verified is False
    assert existing_user.email == 'mail@user.com'
    assert existing_user.cognito_email_verified is False

    res = graphql_client_system.post(update_user_from_cognito_query, variables={
        'input': {
            'clientMutationId': 'triggertest',
            'lambdaEvent': postconfirmation_confirmsignup,
        },
    })

    expected = {'data': {'updateUserFromCognito': {'clientMutationId': 'triggertest'}}}
    assert res == expected

    updated_user = User.query.filter(
        User.cognito_sub == '69de7e78-1bf6-4175-bbf8-3a29834d1bc0'
    ).one()
    assert updated_user.exists_in_cognito is True
    assert updated_user.cognito_enabled is True
    assert updated_user.cognito_status == 'CONFIRMED'
    assert updated_user.cognito_display_status == 'Enabled / CONFIRMED'
    assert updated_user.phone == '+113311122289'
    assert updated_user.cognito_phone_verified is True
    assert updated_user.email == 'update-from-cognito@test.com'
    assert updated_user.cognito_email_verified is True


@patch('core.cognito_sync.boto3')
def test_update_user_from_cognito_anonymous(boto_m, graphql_client_anonymous, user):
    res = graphql_client_anonymous.post(update_user_from_cognito_query, variables={
        'input': {
            'clientMutationId': 'triggertest',
            'lambdaEvent': presignup_signup_event,
        },
    })
    expected = {
        'data': {'updateUserFromCognito': None},
        'errors': [{'locations': [{'column': 6, 'line': 3}],
                    'message': '401 Unauthorized: <Permission '
                               "needs={Need(method='role', value='system_user')} "
                               'excludes=set()>',
                    'path': ['updateUserFromCognito']}]
    }
    assert res == expected


@patch('core.cognito_sync.boto3')
def test_update_user_from_cognito_registered(boto_m, graphql_client, user):
    res = graphql_client.post(update_user_from_cognito_query, variables={
        'input': {
            'clientMutationId': 'triggertest',
            'lambdaEvent': presignup_signup_event,
        },
    })
    expected = {
        'data': {'updateUserFromCognito': None},
        'errors': [{'locations': [{'column': 6, 'line': 3}],
                    'message': '401 Unauthorized: <Permission '
                               "needs={Need(method='role', value='system_user')} "
                               'excludes=set()>',
                    'path': ['updateUserFromCognito']}]
    }
    assert res == expected


@patch('core.cognito_sync.boto3')
def test_update_user_from_cognito_admin(boto_m, graphql_client_admin, user):
    boto_client_m = MagicMock()
    boto_m.client.return_value = boto_client_m

    boto_client_m.admin_get_user.return_value = confirmed_cognito_user_response

    res = graphql_client_admin.post(update_user_from_cognito_query, variables={
        'input': {
            'clientMutationId': 'triggertest',
            'lambdaEvent': presignup_signup_event,
        },
    })
    expected = {'data': {'updateUserFromCognito': {'clientMutationId': 'triggertest'}}}
    assert res == expected
