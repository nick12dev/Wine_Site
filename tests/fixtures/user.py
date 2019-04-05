# pylint: disable=redefined-outer-name
import datetime
from pytest import fixture

from core.db.models import db
from core.dbmethods.user import create_user


@fixture
def wine_expert():
    expert = create_user(None, assign_wine_expert=False)

    expert.first_name = 'wine_expert'
    expert.email = 'wine_expert@mail.com'

    db.session.commit()

    yield expert


@fixture
def user(wine_expert, sample_jwt_payload):
    _user = create_user(sample_jwt_payload['sub'])

    _user.first_name = 'tuser'
    _user.wine_expert_id = wine_expert.id
    _user.stripe_customer_id = 'stripe_customer_id'
    _user.email = 'mail@user.com'
    _user.registration_finished = True

    db.session.commit()

    yield _user


@fixture
def user_hardcoded_sub(wine_expert, sample_jwt_payload_hardcoded_sub):
    _user = create_user(sample_jwt_payload_hardcoded_sub['sub'])

    _user.first_name = 'tuser'
    _user.wine_expert_id = wine_expert.id
    _user.stripe_customer_id = 'stripe_customer_id'
    _user.email = 'mail@user.com'

    db.session.commit()

    yield _user


@fixture
def user2(wine_expert, sample_jwt_payload2):
    _user = create_user(sample_jwt_payload2['sub'])

    _user.first_name = 'tuser2'
    _user.cognito_sub = sample_jwt_payload2['sub']
    _user.wine_expert_id = wine_expert.id
    _user.stripe_customer_id = 'stripe_customer_id'

    db.session.commit()

    yield _user


@fixture
def user_no_stripe(wine_expert, sample_jwt_payload3):
    _user = create_user(sample_jwt_payload3['sub'])

    _user.first_name = 'tuser_no_stripe'
    _user.cognito_sub = sample_jwt_payload3['sub']
    _user.wine_expert_id = wine_expert.id
    _user.registration_finished = True

    db.session.commit()

    yield _user


@fixture
def user4(wine_expert, sample_jwt_payload4):
    _user = create_user(sample_jwt_payload4['sub'])

    _user.first_name = 'tuser4'
    _user.last_name = 'tlastname4'
    _user.avatar = 'https://some.pic/url/4/'
    _user.bio = 'test bio 4'
    _user.cognito_sub = sample_jwt_payload4['sub']
    _user.wine_expert_id = wine_expert.id
    _user.stripe_customer_id = 'stripe_customer_id'

    db.session.commit()

    yield _user


class DictWithException(dict):
    def __getitem__(self, item):
        raise ValueError('some exception')

    def get(self, k, d=None):
        raise ValueError('some exception')


@fixture
def cognito_list_users_page_token_1():
    return 'CAISlAIIARLtAQgDEugBAKhbkODFYvh/W5iUgNIqvmLMzxERyTV+EGR1tC0hby40eyJAbiI6IlBh' \
           'Z2luYXRpb25Db250aW51YXRpb25EVE8iLCJuZXh0S2V5IjoiQUFBQUFBQUFEZExoQVFFQlJUZmFD' \
           'NStQUlQreGN2ZU1YWGZtaHVlaWpvdnZzVUhvclJlTE5heXBySE5sYm1ZN1lqZzVNREkzT1RVdE1U' \
           'VTFZeTAwTVRSaExXSmlaREl0Wm1ReVpUUmtaR1kzTVdRNU93PT0iLCJwcmV2aW91c1JlcXVlc3RU' \
           'aW1lIjoxNTQ0MDk5OTcxODIyfRog/Lig1jvbKnNEOY4SSdzhkNH5fGPt8Keo1rsdqCxdyeQ='


@fixture
def cognito_list_users_page_token_2():
    return 'VdRNU93PT0iLCJwcmV2aW91c1JlcXVlc3RUCAISlAIIARL2ZU1YWGZtaHVlaWpvdnZzVUhvclJlT' \
           'E5htAQgDEugBAKhbkODFYvh/W5iUgNIqvmLaW1lIjoxNTQ0MDk5OTcxODIyfRog/Lig1jvbKnZ2l' \
           'uYXRpb25Db250aW51YXRpb25EVE8iLCJuZXh0S2V5IjoiQUFBQUFBQUFEZExoQVFFQlJUZmFDdE1' \
           'UMzxERyTV+EGR1tC0hby40eyJAbiI6IlBhVTFZeTAwTVRSaExXSmlaREl0Wm1ReVpUUmtaR1kzTN' \
           'StQUlQT1RVNEOY4SSdzhkNHdyeQ5fGPt8KsdqCreGNeXBySE5sYm1ZN1lqZzVNREkzxeo1r='


@fixture
def cognito_list_users_page_1(
        cognito_list_users_page_token_1, sample_jwt_payload2, sample_jwt_payload3
):
    return {
        'ResponseMetadata': {'HTTPHeaders': {'connection': 'keep-alive',
                                             'content-length': '13531',
                                             'content-type': 'application/x-amz-json-1.1',
                                             'date': 'Sat, 10 Nov 2018 09:56:44 GMT',
                                             'x-amzn-requestid': 'ee22e445-e4ce-11e8-aaed-cb05632366d1'},
                             'HTTPStatusCode': 200,
                             'RequestId': 'ee22e445-e4ce-11e8-aaed-cb05632366d1',
                             'RetryAttempts': 0},
        'PaginationToken': cognito_list_users_page_token_1,
        'Users': [
            {'Attributes': [{'Name': 'email_verified', 'Value': 'false'},
                            {'Name': 'phone_number_verified', 'Value': 'false'}],
             'Enabled': True,
             'UserCreateDate': datetime.datetime(2018, 10, 29, 19, 54, 0, 337000),
             'UserLastModifiedDate': datetime.datetime(2018, 11, 7, 16, 36, 29,
                                                       234000),
             'UserStatus': 'CONFIRMED',
             'Username': 'onemorefakesubject'},
            {'Attributes': [DictWithException()],
             'Enabled': True,
             'UserCreateDate': datetime.datetime(1918, 10, 29, 19, 54, 0, 337000),
             'UserLastModifiedDate': datetime.datetime(2018, 11, 7, 16, 36, 29,
                                                       234000),
             'UserStatus': 'CONFIRMED',
             'Username': sample_jwt_payload3['sub']},
            {'Attributes': [{'Name': 'email_verified', 'Value': 'false'},
                            {'Name': 'phone_number_verified', 'Value': 'false'},
                            {'Name': 'phone_number', 'Value': '+11111111111'},
                            {'Name': 'email', 'Value': 'fdsafads@gmail.com'}],
             'Enabled': False,
             'UserCreateDate': datetime.datetime(2018, 11, 2, 18, 43, 31, 778000),
             'UserLastModifiedDate': datetime.datetime(2018, 11, 2, 18, 43, 31,
                                                       778000),
             'UserStatus': 'UNCONFIRMED',
             'Username': sample_jwt_payload2['sub']},
            {'Attributes': [{'Name': 'email_verified', 'Value': 'false'},
                            {'Name': 'phone_number_verified', 'Value': 'false'},
                            {'Name': 'phone_number', 'Value': '+33333333333'},
                            {'Name': 'email', 'Value': 'vzcx.zcvx@gmail.com'}],
             'Enabled': True,
             'UserCreateDate': datetime.datetime(2018, 10, 29, 18, 24, 58, 534000),
             'UserLastModifiedDate': datetime.datetime(2018, 11, 2, 19, 45, 0,
                                                       57000),
             'UserStatus': 'CONFIRMED',
             'Username': 'fakesubject1'}]}


@fixture
def cognito_list_users_page_2(cognito_list_users_page_token_2):
    return {
        'ResponseMetadata': {'HTTPHeaders': {'connection': 'keep-alive',
                                             'content-length': '13531',
                                             'content-type': 'application/x-amz-json-1.1',
                                             'date': 'Sat, 10 Nov 2018 09:56:44 GMT',
                                             'x-amzn-requestid': 'ee22e445-e4ce-11e8-aaed-cb05632366d1'},
                             'HTTPStatusCode': 200,
                             'RequestId': 'ee22e445-e4ce-11e8-aaed-cb05632366d1',
                             'RetryAttempts': 0},
        'PaginationToken': cognito_list_users_page_token_2,
        'Users': [
            {'Attributes': [{'Name': 'phone_number', 'Value': '+33344333333'},
                            {'Name': 'email', 'Value': 'v1143522@gmail.com'}],
             'Enabled': True,
             'UserCreateDate': datetime.datetime(2018, 10, 29, 18, 24, 58, 534000),
             'UserLastModifiedDate': datetime.datetime(2018, 11, 2, 19, 45, 0,
                                                       57000),
             'UserStatus': 'CONFIRMED',
             'Username': 'yetanotherfakesubject'},
            {'Attributes': [DictWithException()],
             'Enabled': True,
             'UserCreateDate': datetime.datetime(2018, 12, 19, 18, 24, 58, 534000),
             'UserLastModifiedDate': datetime.datetime(2018, 11, 2, 19, 45, 0,
                                                       57000),
             'UserStatus': 'CONFIRMED',
             'Username': 'afakesubjectwithexception'}]}


@fixture
def cognito_list_users_page_3(sample_jwt_payload):
    return {
        'ResponseMetadata': {'HTTPHeaders': {'connection': 'keep-alive',
                                             'content-length': '13531',
                                             'content-type': 'application/x-amz-json-1.1',
                                             'date': 'Sat, 10 Nov 2018 09:56:44 GMT',
                                             'x-amzn-requestid': 'ee22e445-e4ce-11e8-aaed-cb05632366d1'},
                             'HTTPStatusCode': 200,
                             'RequestId': 'ee22e445-e4ce-11e8-aaed-cb05632366d1',
                             'RetryAttempts': 0},
        'Users': [
            {'Attributes': [],
             'Enabled': True,
             'UserCreateDate': datetime.datetime(1998, 10, 29, 18, 24, 58, 534000),
             'UserLastModifiedDate': datetime.datetime(2018, 11, 2, 19, 45, 0,
                                                       57000),
             'UserStatus': 'CONFIRMED'},
            {'IsntReallyAUser': 'noitisnt'},
            {'Attributes': [{'Name': 'email_verified', 'Value': 'false'},
                            {'Name': 'phone_number_verified', 'Value': 'true'},
                            {'Name': 'phone_number', 'Value': '+444444444444'},
                            {'Name': 'email', 'Value': 'oiyoyiyoy@gmail.com'}],
             'Enabled': True,
             'UserCreateDate': datetime.datetime(2018, 10, 29, 19, 21, 7, 400000),
             'UserLastModifiedDate': datetime.datetime(2018, 10, 29, 19, 21, 21,
                                                       714000),
             'UserStatus': 'CONFIRMED',
             'Username': sample_jwt_payload['sub']}]}
