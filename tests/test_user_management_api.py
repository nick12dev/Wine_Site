#
# pylint: disable=unused-argument,invalid-name
from unittest.mock import (
    patch,
    call,
)

import graphene
from graphene import Node

from core.db.models import db
from core.db.models.user import User
from tests import (
    patch_boto_for_save_user_mutation,
    do_full_cognito_user_sync,
)

user_list_query = '''
    query ($offset: Int, $first: Int, $sort: [UserSortEnum], $listFilter: UserFilter) {
        userManagement {
          users(offset: $offset, first: $first, sort: $sort, listFilter: $listFilter) {
            totalCount
            edges {
              node {
                existsInCognito
                allowedCognitoActions
                cognitoEnabled
                cognitoStatus
                cognitoDisplayStatus
                cognitoPhoneVerified
                cognitoEmailVerified
                firstName
                lastName
                email
                phone
                avatar
                userAddress {
                  country
                  stateRegion
                  city
                  street1
                  street2
                  postcode
                }
                userSubscription {
                  type
                  budget
                  bottleQty
                }
                userCards {
                  totalCount
                  edges {
                    node {
                      preference
                      displayOrder}}}}}}}}
'''


@patch('core.cognito_sync.boto3')
def test_bulk_load_cognito_user_attributes_nonadmin(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client,
        user,
        user_no_stripe,
        wine_expert,
):
    res, boto_client_m = do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client,
    )
    assert res['data']['doFullCognitoUserSync'] is None
    assert '401 Unauthorized' in res['errors'][0]['message']

    boto_client_m.list_users.assert_not_called()


@patch('core.cognito_sync.boto3')
def test_bulk_load_cognito_user_attributes(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user,
        user2,
        user_no_stripe,
        user4,
        wine_expert,
):
    res, boto_client_m = do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )
    expected = {'data': {'doFullCognitoUserSync': {'clientMutationId': 'some mutation',
                                                   'cognitoListComplete': True,
                                                   'exceptionsCount': 4,
                                                   'notConnectedToCognitoCount': 1,
                                                   'notFoundInCognitoCount': 1,
                                                   'successfullyUpdatedCount': 2,
                                                   'successfullyAddedCount': 3}}}
    assert res == expected

    res = graphql_client_admin.post(user_list_query, variables={
        'sort': 'user_number_asc'
    })

    boto_client_m.list_users.assert_has_calls([
        call(
            UserPoolId='eu-central-1_s8K8ZDg8T',
            AttributesToGet=['email', 'phone_number', 'email_verified', 'phone_number_verified'],
        ),
        call(
            PaginationToken=cognito_list_users_page_token_1,
            UserPoolId='eu-central-1_s8K8ZDg8T',
            AttributesToGet=['email', 'phone_number', 'email_verified', 'phone_number_verified'],
        ),
        call(
            PaginationToken=cognito_list_users_page_token_2,
            UserPoolId='eu-central-1_s8K8ZDg8T',
            AttributesToGet=['email', 'phone_number', 'email_verified', 'phone_number_verified'],
        ),
    ])
    assert boto_client_m.list_users.call_count == 3

    expected = {'data': {'userManagement': {'users': {'edges': [
        {'node': {'allowedCognitoActions': ['enable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Disabled / NOT_CONNECTED_TO_COGNITO',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': False,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'NOT_CONNECTED_TO_COGNITO',
                  'email': 'wine_expert@mail.com',
                  'existsInCognito': False,
                  'firstName': 'wine_expert',
                  'lastName': None,
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': True,
                  'cognitoStatus': 'CONFIRMED',
                  'email': 'oiyoyiyoy@gmail.com',
                  'existsInCognito': True,
                  'firstName': 'tuser',
                  'lastName': None,
                  'phone': '+444444444444',
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['enable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Disabled / UNCONFIRMED',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': False,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'UNCONFIRMED',
                  'email': 'fdsafads@gmail.com',
                  'existsInCognito': True,
                  'firstName': 'tuser2',
                  'lastName': None,
                  'phone': '+11111111111',
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'UNKNOWN',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'email': None,
                  'existsInCognito': True,
                  'firstName': 'tuser_no_stripe',
                  'lastName': None,
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['enable'],
                  'avatar': 'https://some.pic/url/4/',
                  'cognitoDisplayStatus': 'Disabled / NOT_FOUND_IN_COGNITO',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': False,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'NOT_FOUND_IN_COGNITO',
                  'email': None,
                  'existsInCognito': False,
                  'firstName': 'tuser4',
                  'lastName': 'tlastname4',
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'email': None,
                  'existsInCognito': True,
                  'firstName': None,
                  'lastName': None,
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'email': 'vzcx.zcvx@gmail.com',
                  'existsInCognito': True,
                  'firstName': None,
                  'lastName': None,
                  'phone': '+33333333333',
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': None,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': None,
                  'cognitoStatus': 'CONFIRMED',
                  'email': 'v1143522@gmail.com',
                  'existsInCognito': True,
                  'firstName': None,
                  'lastName': None,
                  'phone': '+33344333333',
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'UNKNOWN',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'email': None,
                  'existsInCognito': True,
                  'firstName': None,
                  'lastName': None,
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}}],
        'totalCount': 9}}}}
    assert res == expected


def test_user_list_nonadmin(graphql_client, user, user_no_stripe, wine_expert):
    res = graphql_client.post(user_list_query)
    assert res['data']['userManagement'] is None
    assert '401 Unauthorized' in res['errors'][0]['message']


@patch('core.cognito_sync.boto3')
def test_user_list_filter_by_number(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user,
        user_no_stripe,
        wine_expert,
):
    wine_expert_user_number = wine_expert.user_number

    do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )

    res = graphql_client_admin.post(user_list_query, variables={
        'offset': 0,
        'first': 2,
        'sort': 'first_name_desc',
        'listFilter': {
            'userNumber': wine_expert_user_number,
        },
    })
    expected = {'data': {'userManagement': {'users': {'edges': [
        {'node': {'allowedCognitoActions': ['enable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Disabled / NOT_CONNECTED_TO_COGNITO',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': False,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'NOT_CONNECTED_TO_COGNITO',
                  'email': 'wine_expert@mail.com',
                  'existsInCognito': False,
                  'firstName': 'wine_expert',
                  'lastName': None,
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}}
    ], 'totalCount': 1}}}}
    assert res == expected


@patch('core.cognito_sync.boto3')
def test_user_list_filter_by_display_name(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user,
        user_no_stripe,
        wine_expert,
):
    do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )

    res = graphql_client_admin.post(user_list_query, variables={
        'offset': 0,
        'first': 2,
        'sort': 'first_name_desc',
        'listFilter': {
            'userNumber': None,
            'displayName': 'uSe',
            'cognitoDisplayStatus': '',
        },
    })
    expected = {'data': {'userManagement': {'users': {'edges': [
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'UNKNOWN',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'email': None,
                  'existsInCognito': True,
                  'firstName': 'tuser_no_stripe',
                  'lastName': None,
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': True,
                  'cognitoStatus': 'CONFIRMED',
                  'email': 'oiyoyiyoy@gmail.com',
                  'existsInCognito': True,
                  'firstName': 'tuser',
                  'lastName': None,
                  'phone': '+444444444444',
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}}
    ], 'totalCount': 2}}}}

    assert res == expected


@patch('core.cognito_sync.boto3')
def test_user_list_filter_by_cognito_status(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user,
        user_no_stripe,
        wine_expert,
):
    do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )

    res = graphql_client_admin.post(user_list_query, variables={
        'offset': 0,
        'first': 4,
        'sort': 'email_asc',
        'listFilter': {
            'userNumber': '',
            'cognitoDisplayStatus': 'Enabled / CONFIRMED',
        },
    })
    expected = {'data': {'userManagement': {'users': {'edges': [
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': True,
                  'cognitoStatus': 'CONFIRMED',
                  'email': 'oiyoyiyoy@gmail.com',
                  'existsInCognito': True,
                  'firstName': 'tuser',
                  'lastName': None,
                  'phone': '+444444444444',
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': None,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': None,
                  'cognitoStatus': 'CONFIRMED',
                  'email': 'v1143522@gmail.com',
                  'existsInCognito': True,
                  'firstName': None,
                  'lastName': None,
                  'phone': '+33344333333',
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'email': 'vzcx.zcvx@gmail.com',
                  'existsInCognito': True,
                  'firstName': None,
                  'lastName': None,
                  'phone': '+33333333333',
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'email': None,
                  'existsInCognito': True,
                  'firstName': None,
                  'lastName': None,
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
    ], 'totalCount': 4}}}}
    assert res == expected


@patch('core.cognito_sync.boto3')
def test_user_list_filter_for_unknown_status(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user,
        user_no_stripe,
        wine_expert,
):
    do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )

    res = graphql_client_admin.post(user_list_query, variables={
        'offset': 0,
        'first': 2,
        'sort': 'first_name_desc',
        'listFilter': {
            'userNumber': '',
            'cognitoDisplayStatus': 'UNKNOWN',
        },
    })
    expected = {'data': {'userManagement': {'users': {'edges': [
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'UNKNOWN',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'email': None,
                  'existsInCognito': True,
                  'firstName': None,
                  'lastName': None,
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'UNKNOWN',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'email': None,
                  'existsInCognito': True,
                  'firstName': 'tuser_no_stripe',
                  'lastName': None,
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
    ], 'totalCount': 2}}}}
    assert res == expected


@patch('core.cognito_sync.boto3')
def test_user_list_sort_by_first_name_desc(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user,
        user_no_stripe,
        wine_expert,
):
    do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )

    res = graphql_client_admin.post(user_list_query, variables={
        'offset': 5,
        'first': 3,
        'sort': 'first_name_desc',
    })

    expected = {'data': {'userManagement': {'users': {'edges': [
        {'node': {'allowedCognitoActions': ['enable'],
                  'avatar': None,
                  'cognitoDisplayStatus': 'Disabled / NOT_CONNECTED_TO_COGNITO',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': False,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'NOT_CONNECTED_TO_COGNITO',
                  'email': 'wine_expert@mail.com',
                  'existsInCognito': False,
                  'firstName': 'wine_expert',
                  'lastName': None,
                  'phone': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'email': None,
                  'firstName': 'tuser_no_stripe',
                  'lastName': None,
                  'phone': None,
                  'existsInCognito': True,
                  'cognitoEnabled': True,
                  'cognitoStatus': 'CONFIRMED',
                  'cognitoDisplayStatus': 'UNKNOWN',
                  'cognitoPhoneVerified': False,
                  'cognitoEmailVerified': False,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'email': 'oiyoyiyoy@gmail.com',
                  'firstName': 'tuser',
                  'lastName': None,
                  'phone': '+444444444444',
                  'existsInCognito': True,
                  'cognitoEnabled': True,
                  'cognitoStatus': 'CONFIRMED',
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoPhoneVerified': True,
                  'cognitoEmailVerified': False,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
    ], 'totalCount': 8}}}}

    assert res == expected


@patch('core.cognito_sync.boto3')
def test_user_list_sort_by_number_desc(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user,
        user_no_stripe,
        wine_expert,
):
    do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )

    res = graphql_client_admin.post(user_list_query, variables={
        'offset': 5,
        'first': 2,
        'sort': 'user_number_desc'
    })

    expected = {'data': {'userManagement': {'users': {'edges': [
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'email': None,
                  'firstName': 'tuser_no_stripe',
                  'lastName': None,
                  'phone': None,
                  'existsInCognito': True,
                  'cognitoEnabled': True,
                  'cognitoStatus': 'CONFIRMED',
                  'cognitoDisplayStatus': 'UNKNOWN',
                  'cognitoPhoneVerified': False,
                  'cognitoEmailVerified': False,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'allowedCognitoActions': ['disable'],
                  'avatar': None,
                  'email': 'oiyoyiyoy@gmail.com',
                  'firstName': 'tuser',
                  'lastName': None,
                  'phone': '+444444444444',
                  'existsInCognito': True,
                  'cognitoEnabled': True,
                  'cognitoStatus': 'CONFIRMED',
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoPhoneVerified': True,
                  'cognitoEmailVerified': False,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}}
    ], 'totalCount': 8}}}}

    assert res == expected


@patch('core.cognito_sync.boto3')
def test_cognito_display_statuses_for_filtering(
        boto_m,
        graphql_client_admin,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        user,
        user2,
        user_no_stripe,
        user4,
        wine_expert,
):
    do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )

    res = graphql_client_admin.post(
        '{ userManagement { cognitoDisplayStatuses } }'
    )
    expected = {'data': {'userManagement': {'cognitoDisplayStatuses': [
        'Disabled / NOT_CONNECTED_TO_COGNITO',
        'Disabled / NOT_FOUND_IN_COGNITO',
        'Disabled / UNCONFIRMED',
        'Enabled / CONFIRMED',
        'UNKNOWN',
    ]}}}
    assert res == expected


user_details_query = '''
query ($id: ID!) {
  node(id: $id) {
    ... on User {
      existsInCognito
      cognitoEnabled
      cognitoStatus
      cognitoDisplayStatus
      cognitoPhoneVerified
      cognitoEmailVerified
      firstName
      lastName
      username
      email
      phone
      avatar
      selectedThemes {
        edges {
          node {
            title
            image
            shortDescription
            sortOrder
            themeGroup {
              title
              description
              isActive
              isPromoted
              sortOrder
              user {
                firstName
                lastName
              }
            }
          }
        }
      }
      followedCreators {
        edges {
          node {
            firstName
            lastName
            avatar
            isCreator
            bio
          }
        }
      }
      userAddress {
        country
        stateRegion
        city
        street1
        street2
        postcode
      }
      userSubscription {
        type
        budget
        bottleQty
      }
      userCards {
        totalCount
        edges {
          node {
            preference
            displayOrder}}}}}}
'''


def test_user_details_nonadmin(
        graphql_client, user, user_no_stripe, wine_expert, user2
):
    res = graphql_client.post(user_details_query, variables={
        'id': Node.to_global_id('User', user2.id)
    })
    expected = {'data': {'node': {'avatar': None,
                                  'cognitoDisplayStatus': 'UNKNOWN',
                                  'cognitoEmailVerified': False,
                                  'cognitoEnabled': False,
                                  'cognitoPhoneVerified': False,
                                  'cognitoStatus': 'UNKNOWN',
                                  'email': None,
                                  'existsInCognito': None,
                                  'firstName': 'tuser2',
                                  'lastName': None,
                                  'username': None,
                                  'followedCreators': {'edges': []},
                                  'phone': None,
                                  'selectedThemes': {'edges': []},
                                  'userAddress': None,
                                  'userCards': {'edges': [], 'totalCount': 0},
                                  'userSubscription': None}}}
    assert res == expected


def test_user_details_anonymous(
        graphql_client_anonymous, user, user_no_stripe, wine_expert, user2
):
    res = graphql_client_anonymous.post(user_details_query, variables={
        'id': Node.to_global_id('User', user2.id)
    })
    assert res['data']['node'] is None


@patch('core.cognito_sync.boto3')
def test_user_details(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user_no_stripe,
        wine_expert,
        user,
        user2,
        user4,
        theme_1,
        theme_2,
        theme_3,
        theme_4,
        theme_5,
        theme_6,
        theme_7,
        theme_8,
        theme_9,
        theme_10,
        empty_theme_group,
        user_subscription,
        user_address,
        user_card_1,
        user_card_2,
):
    user_id = user.id

    user.selected_themes.extend([theme_1, theme_2, theme_5, theme_6, theme_9])
    user.followed_creators.extend([user, user2, user4])
    db.session.commit()

    do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )

    res = graphql_client_admin.post(user_details_query, variables={
        'id': Node.to_global_id('User', user_id)
    })

    expected = {'data': {'node': {
        'avatar': None,
        'email': 'oiyoyiyoy@gmail.com',
        'firstName': 'tuser',
        'lastName': None,
        'username': 'tuser',
        'phone': '+444444444444',
        'existsInCognito': True,
        'cognitoEnabled': True,
        'cognitoStatus': 'CONFIRMED',
        'cognitoDisplayStatus': 'Enabled / CONFIRMED',
        'cognitoPhoneVerified': True,
        'cognitoEmailVerified': False,
        'followedCreators': {'edges': [
            {'node': {'avatar': None,
                      'bio': None,
                      'firstName': 'tuser',
                      'isCreator': True,
                      'lastName': None}},
            {'node': {'avatar': None,
                      'bio': None,
                      'firstName': 'tuser2',
                      'isCreator': True,
                      'lastName': None}},
            {'node': {'avatar': 'https://some.pic/url/4/',
                      'bio': 'test bio 4',
                      'firstName': 'tuser4',
                      'isCreator': True,
                      'lastName': 'tlastname4'}}]},
        'selectedThemes': {'edges': [
            {'node': {'title': 'theme 6',
                      'shortDescription': 'theme short desc 6',
                      'image': 'https://someimage6.url',
                      'sortOrder': 200,
                      'themeGroup': {'description': 'theme group desc 3',
                                     'isActive': True,
                                     'isPromoted': True,
                                     'sortOrder': 40,
                                     'title': 'theme group 3',
                                     'user': {'firstName': 'tuser4',
                                              'lastName': 'tlastname4'}}, }},
            {'node': {'title': 'theme 5',
                      'shortDescription': 'theme short desc 5',
                      'image': 'https://someimage5.url',
                      'sortOrder': 300,
                      'themeGroup': {'title': 'theme group 3',
                                     'description': 'theme group desc 3',
                                     'isActive': True,
                                     'isPromoted': True,
                                     'sortOrder': 40,
                                     'user': {'firstName': 'tuser4',
                                              'lastName': 'tlastname4'}}, }},
            {'node': {'title': 'theme 9',
                      'shortDescription': 'theme short desc 9',
                      'image': 'https://someimage9.url',
                      'sortOrder': 1000,
                      'themeGroup': {'description': 'theme group desc 4',
                                     'isActive': True,
                                     'isPromoted': False,
                                     'sortOrder': 20,
                                     'title': 'theme group 4',
                                     'user': {'firstName': 'tuser4',
                                              'lastName': 'tlastname4'}}, }},
            {'node': {'title': 'theme 2',
                      'shortDescription': 'theme short desc 2',
                      'image': 'https://someimage2.url',
                      'sortOrder': 20,
                      'themeGroup': {'title': 'theme group 2',
                                     'description': 'theme group desc 2',
                                     'isActive': True,
                                     'isPromoted': False,
                                     'sortOrder': 30,
                                     'user': {'firstName': 'tuser2',
                                              'lastName': None}}, }}]},
        'userAddress': {'city': 'New York',
                        'country': 'US',
                        'postcode': '1234',
                        'stateRegion': 'New York',
                        'street1': 'street 1',
                        'street2': None},
        'userCards': {'edges': [{'node': {'displayOrder': None,
                                          'preference': 'like'}},
                                {'node': {'displayOrder': None,
                                          'preference': 'dislike'}}],
                      'totalCount': 2},
        'userSubscription': {'bottleQty': 2,
                             'budget': '100.00',
                             'type': 'mixed'}}}}

    assert res == expected


def test_user_number(graphql_client_admin, user):
    query = '''
        query ($id: ID!) {
          node(id: $id) {
            ... on User {
              userNumber}}}
    '''

    res = graphql_client_admin.post(query, variables={
        'id': Node.to_global_id('User', user.id)
    })

    assert res['data']['node']['userNumber'] == f'{user.id:07}'


@patch('core.cognito_sync.boto3')
def test_get_user_and_domain_cards_in_one_query(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user_card_1,
        user_card_2,
        user2,
        user_address,
        user_address2,
        user_subscription,
        user_subscription2,
):
    do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )

    query = '''
        {
            userManagement {
              users {
                totalCount
                edges {
                  node {
                    firstName
                    existsInCognito
                    cognitoEnabled
                    cognitoStatus
                    cognitoDisplayStatus
                    cognitoPhoneVerified
                    cognitoEmailVerified
                    userAddress {
                      country
                    }
                    userSubscription {
                      type
                    }
                    userCards {
                      totalCount
                      edges {
                        node {
                          displayOrder
                          preference
                          domainCard {
                            displayTitle
                            displayText
                            displayImage
                            displayOrder}}}}}}}}}
    '''

    res = graphql_client_admin.post(query)

    expected = {'data': {'userManagement': {'users': {'edges': [
        {'node': {'firstName': 'wine_expert',
                  'existsInCognito': False,
                  'cognitoEnabled': False,
                  'cognitoStatus': 'NOT_CONNECTED_TO_COGNITO',
                  'cognitoDisplayStatus': 'Disabled / NOT_CONNECTED_TO_COGNITO',
                  'cognitoPhoneVerified': False,
                  'cognitoEmailVerified': False,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'firstName': 'tuser',
                  'existsInCognito': True,
                  'cognitoEnabled': True,
                  'cognitoStatus': 'CONFIRMED',
                  'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoPhoneVerified': True,
                  'cognitoEmailVerified': False,
                  'userAddress': {'country': 'US'},
                  'userCards': {'edges': [
                      {'node': {'displayOrder': None,
                                'domainCard': {'displayImage': None,
                                               'displayOrder': 1,
                                               'displayText': 'text1',
                                               'displayTitle': None},
                                'preference': 'like'}},
                      {'node': {'displayOrder': None,
                                'domainCard': {'displayImage': None,
                                               'displayOrder': 2,
                                               'displayText': 'text2',
                                               'displayTitle': None},
                                'preference': 'dislike'}}],
                      'totalCount': 2},
                  'userSubscription': {'type': 'mixed'}}},
        {'node': {'firstName': 'tuser2',
                  'existsInCognito': True,
                  'cognitoEnabled': False,
                  'cognitoStatus': 'UNCONFIRMED',
                  'cognitoDisplayStatus': 'Disabled / UNCONFIRMED',
                  'cognitoPhoneVerified': False,
                  'cognitoEmailVerified': False,
                  'userAddress': {'country': None},
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': {'type': 'red'}}},
        {'node': {'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'existsInCognito': True,
                  'firstName': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'cognitoDisplayStatus': 'UNKNOWN',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'existsInCognito': True,
                  'firstName': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'existsInCognito': True,
                  'firstName': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'cognitoDisplayStatus': 'Enabled / CONFIRMED',
                  'cognitoEmailVerified': None,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': None,
                  'cognitoStatus': 'CONFIRMED',
                  'existsInCognito': True,
                  'firstName': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}},
        {'node': {'cognitoDisplayStatus': 'UNKNOWN',
                  'cognitoEmailVerified': False,
                  'cognitoEnabled': True,
                  'cognitoPhoneVerified': False,
                  'cognitoStatus': 'CONFIRMED',
                  'existsInCognito': True,
                  'firstName': None,
                  'userAddress': None,
                  'userCards': {'edges': [],
                                'totalCount': 0},
                  'userSubscription': None}}],
        'totalCount': 8}}}}

    assert res == expected


user_fields = '''
      existsInCognito
      allowedCognitoActions
      cognitoEnabled
      cognitoStatus
      cognitoDisplayStatus
      cognitoPhoneVerified
      cognitoEmailVerified
      firstName
      lastName
      email
      phone
      avatar
      userAddress {
        country
        stateRegion
        city
        street1
        street2
        postcode
      }
      userSubscription {
        bottleQty
        state
        type
        budget
      }
      userCards {
        totalCount
        edges {
          node {
            displayOrder
            preference
            domainCard {
              displayTitle
              displayText
              displayImage
              displayOrder
            }}}}
'''

save_user_query = '''
mutation saveUser($input: SaveUserInput!) {
  saveUser(input: $input) {
    clientMutationId
    user {
''' + user_fields + '''}}}
'''

get_user_query = '''
query($id: ID!) {
  user: node(id: $id) {
    ... on User {
''' + user_fields + '''}}}
'''


@patch('core.cognito_sync.boto3')
def test_save_user(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user,
        save_user_input_dict,
):
    user_id = user.id
    user_cognito_sub = user.cognito_sub
    _, boto_client_m = do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )
    boto_client_m = patch_boto_for_save_user_mutation(boto_client_m=boto_client_m, boto_user_dict={
        user_cognito_sub: {
            'Enabled': True,
            'UserStatus': 'CONFIRMED',
            'UserAttributes': {
                'email_verified': 'false',
                'phone_number_verified': 'true',
            },
        }
    })

    save_user_input_dict['input']['id'] = graphene.Node.to_global_id('User', user_id)
    res = graphql_client_admin.post(save_user_query, variables=save_user_input_dict)

    boto_client_m.change_password.assert_not_called()
    boto_client_m.update_user_attributes.assert_not_called()
    boto_client_m.admin_enable_user.assert_not_called()
    boto_client_m.admin_disable_user.assert_not_called()
    boto_client_m.admin_update_user_attributes.assert_called_once_with(
        UserPoolId='eu-central-1_s8K8ZDg8T',
        Username=user.cognito_sub,
        UserAttributes=[
            {
                'Name': 'email',
                'Value': 'john.doe@test.com'
            },
            {
                'Name': 'phone_number',
                'Value': '+123456789012'
            },
        ],
    )
    boto_client_m.admin_get_user.assert_called_once_with(
        UserPoolId='eu-central-1_s8K8ZDg8T', Username=user_cognito_sub
    )
    boto_client_m.get_user.assert_not_called()

    expected_fields = {
        'allowedCognitoActions': ['disable'],
        'avatar': 'https://test.com/someimage.png',
        'email': 'john.doe@test.com',
        'firstName': 'John',
        'lastName': 'Doe',
        'phone': '+123456789012',
        'existsInCognito': True,
        'cognitoEnabled': True,
        'cognitoStatus': 'CONFIRMED',
        'cognitoDisplayStatus': 'Enabled / CONFIRMED',
        'cognitoPhoneVerified': True,
        'cognitoEmailVerified': False,
        'userAddress': {'city': 'San Francisco',
                        'country': 'USA',
                        'postcode': '79024',
                        'stateRegion': 'California',
                        'street1': 'some street 1',
                        'street2': 'some street 2'},
        'userCards': {'edges': [
            {'node': {'displayOrder': 1,
                      'domainCard': {'displayImage': None,
                                     'displayOrder': 1,
                                     'displayText': 'text1',
                                     'displayTitle': None},
                      'preference': 'like'}},
            {'node': {'displayOrder': 2,
                      'domainCard': {'displayImage': None,
                                     'displayOrder': 2,
                                     'displayText': 'text2',
                                     'displayTitle': None},
                      'preference': 'dislike'}},
            {'node': {'displayOrder': 3,
                      'domainCard': {'displayImage': None,
                                     'displayOrder': 3,
                                     'displayText': 'text3',
                                     'displayTitle': None},
                      'preference': 'neutral'}}],
            'totalCount': 3},
        'userSubscription': {'bottleQty': 3,
                             'budget': '100.00',
                             'state': 'suspended',
                             'type': 'mixed'}}

    assert res == {'data': {'saveUser': {
        'clientMutationId': 'test_mutation_id',
        'user': expected_fields}}}

    updated_user = graphql_client_admin.post(get_user_query, variables={
        'id': save_user_input_dict['input']['id']
    })

    assert updated_user == {'data': {
        'user': expected_fields}}


@patch('core.cognito_sync.boto3')
def test_save_user_nonadmin(boto_m, graphql_client, user2, save_user_input_dict):
    save_user_input_dict['input']['id'] = graphene.Node.to_global_id('User', user2.id)
    res = graphql_client.post(save_user_query, variables=save_user_input_dict)

    assert res['data']['saveUser'] is None
    assert '401 Unauthorized' in res['errors'][0]['message']


@patch('core.cognito_sync.boto3')
def test_disable_cognito_user(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
        user,
        save_user_input_dict,
):
    user_id = user.id
    user_cognito_sub = user.cognito_sub
    _, boto_client_m = do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )
    boto_client_m = patch_boto_for_save_user_mutation(boto_client_m=boto_client_m, boto_user_dict={
        user_cognito_sub: {
            'Enabled': True,
            'UserStatus': 'CONFIRMED',
            'UserAttributes': {
                'email_verified': 'false',
                'phone_number_verified': 'true',
            },
        }
    })

    save_user_input_dict['input']['id'] = graphene.Node.to_global_id('User', user_id)
    save_user_input_dict['input']['cognitoAction'] = 'disable'
    save_user_input_dict['input']['cognitoPhoneVerified'] = False
    save_user_input_dict['input']['cognitoEmailVerified'] = False
    res = graphql_client_admin.post(save_user_query, variables=save_user_input_dict)

    boto_client_m.change_password.assert_not_called()
    boto_client_m.update_user_attributes.assert_not_called()
    boto_client_m.admin_enable_user.assert_not_called()
    boto_client_m.admin_disable_user.assert_called_once_with(
        UserPoolId='eu-central-1_s8K8ZDg8T',
        Username=user.cognito_sub,
    )
    boto_client_m.admin_update_user_attributes.assert_called_once_with(
        UserPoolId='eu-central-1_s8K8ZDg8T',
        Username=user.cognito_sub,
        UserAttributes=[
            {
                'Name': 'email',
                'Value': 'john.doe@test.com'
            },
            {
                'Name': 'phone_number',
                'Value': '+123456789012'
            },
            {
                'Name': 'email_verified',
                'Value': 'false'
            },
            {
                'Name': 'phone_number_verified',
                'Value': 'false'
            },
        ],
    )
    boto_client_m.admin_get_user.assert_called_once_with(
        UserPoolId='eu-central-1_s8K8ZDg8T', Username=user_cognito_sub
    )
    boto_client_m.get_user.assert_not_called()

    expected_fields = {
        'allowedCognitoActions': ['enable'],
        'avatar': 'https://test.com/someimage.png',
        'email': 'john.doe@test.com',
        'firstName': 'John',
        'lastName': 'Doe',
        'phone': '+123456789012',
        'existsInCognito': True,
        'cognitoEnabled': False,
        'cognitoStatus': 'CONFIRMED',
        'cognitoDisplayStatus': 'Disabled / CONFIRMED',
        'cognitoPhoneVerified': False,
        'cognitoEmailVerified': False,
        'userAddress': {'city': 'San Francisco',
                        'country': 'USA',
                        'postcode': '79024',
                        'stateRegion': 'California',
                        'street1': 'some street 1',
                        'street2': 'some street 2'},
        'userCards': {'edges': [
            {'node': {'displayOrder': 1,
                      'domainCard': {'displayImage': None,
                                     'displayOrder': 1,
                                     'displayText': 'text1',
                                     'displayTitle': None},
                      'preference': 'like'}},
            {'node': {'displayOrder': 2,
                      'domainCard': {'displayImage': None,
                                     'displayOrder': 2,
                                     'displayText': 'text2',
                                     'displayTitle': None},
                      'preference': 'dislike'}},
            {'node': {'displayOrder': 3,
                      'domainCard': {'displayImage': None,
                                     'displayOrder': 3,
                                     'displayText': 'text3',
                                     'displayTitle': None},
                      'preference': 'neutral'}}],
            'totalCount': 3},
        'userSubscription': {'bottleQty': 3,
                             'budget': '100.00',
                             'state': 'suspended',
                             'type': 'mixed'}}

    assert res == {'data': {'saveUser': {
        'clientMutationId': 'test_mutation_id',
        'user': expected_fields}}}

    updated_user = graphql_client_admin.post(get_user_query, variables={
        'id': save_user_input_dict['input']['id']
    })

    assert updated_user == {'data': {
        'user': expected_fields}}


@patch('core.cognito_sync.boto3')
def test_enable_cognito_user(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        sample_jwt_payload2,
        graphql_client_admin,
        wine_expert,
        save_user_input_dict,
):
    _, boto_client_m = do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )
    boto_client_m = patch_boto_for_save_user_mutation(boto_client_m=boto_client_m, boto_user_dict={
        sample_jwt_payload2['sub']: {
            'Enabled': False,
            'UserStatus': 'UNCONFIRMED',
            'UserAttributes': {
                'email_verified': 'false',
                'phone_number_verified': 'false',
            },
        }
    })
    user_id = User.query.filter(User.cognito_sub == sample_jwt_payload2['sub']).one().id

    save_user_input_dict['input']['id'] = graphene.Node.to_global_id('User', user_id)
    save_user_input_dict['input']['cognitoAction'] = 'enable'
    save_user_input_dict['input']['cognitoPhoneVerified'] = True
    save_user_input_dict['input']['cognitoEmailVerified'] = True
    res = graphql_client_admin.post(save_user_query, variables=save_user_input_dict)

    boto_client_m.change_password.assert_not_called()
    boto_client_m.update_user_attributes.assert_not_called()
    boto_client_m.admin_disable_user.assert_not_called()
    boto_client_m.admin_enable_user.assert_called_once_with(
        UserPoolId='eu-central-1_s8K8ZDg8T',
        Username=sample_jwt_payload2['sub'],
    )
    boto_client_m.admin_update_user_attributes.assert_called_once_with(
        UserPoolId='eu-central-1_s8K8ZDg8T',
        Username=sample_jwt_payload2['sub'],
        UserAttributes=[
            {
                'Name': 'email',
                'Value': 'john.doe@test.com'
            },
            {
                'Name': 'phone_number',
                'Value': '+123456789012'
            },
            {
                'Name': 'email_verified',
                'Value': 'true'
            },
            {
                'Name': 'phone_number_verified',
                'Value': 'true'
            },
        ],
    )
    boto_client_m.admin_get_user.assert_called_once_with(
        UserPoolId='eu-central-1_s8K8ZDg8T', Username=sample_jwt_payload2['sub']
    )
    boto_client_m.get_user.assert_not_called()

    expected_fields = {
        'allowedCognitoActions': ['disable'],
        'avatar': 'https://test.com/someimage.png',
        'email': 'john.doe@test.com',
        'firstName': 'John',
        'lastName': 'Doe',
        'phone': '+123456789012',
        'existsInCognito': True,
        'cognitoEnabled': True,
        'cognitoStatus': 'UNCONFIRMED',
        'cognitoDisplayStatus': 'Enabled / UNCONFIRMED',
        'cognitoPhoneVerified': True,
        'cognitoEmailVerified': True,
        'userAddress': {'city': 'San Francisco',
                        'country': 'USA',
                        'postcode': '79024',
                        'stateRegion': 'California',
                        'street1': 'some street 1',
                        'street2': 'some street 2'},
        'userCards': {'edges': [
            {'node': {'displayOrder': 1,
                      'domainCard': {'displayImage': None,
                                     'displayOrder': 1,
                                     'displayText': 'text1',
                                     'displayTitle': None},
                      'preference': 'like'}},
            {'node': {'displayOrder': 2,
                      'domainCard': {'displayImage': None,
                                     'displayOrder': 2,
                                     'displayText': 'text2',
                                     'displayTitle': None},
                      'preference': 'dislike'}},
            {'node': {'displayOrder': 3,
                      'domainCard': {'displayImage': None,
                                     'displayOrder': 3,
                                     'displayText': 'text3',
                                     'displayTitle': None},
                      'preference': 'neutral'}}],
            'totalCount': 3},
        'userSubscription': {'bottleQty': 3,
                             'budget': '100.00',
                             'state': 'suspended',
                             'type': 'mixed'}}

    assert res == {'data': {'saveUser': {
        'clientMutationId': 'test_mutation_id',
        'user': expected_fields}}}

    updated_user = graphql_client_admin.post(get_user_query, variables={
        'id': save_user_input_dict['input']['id']
    })

    assert updated_user == {'data': {
        'user': expected_fields}}


@patch('core.cognito_sync.boto3')
def test_failure_updating_user_in_cognito(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        sample_jwt_payload2,
        graphql_client_admin,
        wine_expert,
        save_user_input_dict,
):
    _, boto_client_m = do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client_admin,
    )
    boto_client_m = patch_boto_for_save_user_mutation(boto_client_m=boto_client_m)

    def fail_updating_user_in_cognito(*args, **kwargs):
        raise ValueError('some cognito failure')

    boto_client_m.admin_update_user_attributes.side_effect = fail_updating_user_in_cognito
    boto_client_m.exceptions.UserNotFoundException = ZeroDivisionError

    user_id = User.query.filter(User.cognito_sub == sample_jwt_payload2['sub']).one().id

    save_user_input_dict['input']['id'] = graphene.Node.to_global_id('User', user_id)
    save_user_input_dict['input']['cognitoPhoneVerified'] = True
    save_user_input_dict['input']['cognitoEmailVerified'] = True

    res = graphql_client_admin.post(save_user_query, variables=save_user_input_dict)

    boto_client_m.change_password.assert_not_called()
    boto_client_m.update_user_attributes.assert_not_called()
    boto_client_m.admin_enable_user.assert_not_called()
    boto_client_m.admin_disable_user.assert_not_called()
    boto_client_m.admin_update_user_attributes.assert_called_once_with(
        UserPoolId='eu-central-1_s8K8ZDg8T',
        Username=sample_jwt_payload2['sub'],
        UserAttributes=[
            {
                'Name': 'email',
                'Value': 'john.doe@test.com'
            },
            {
                'Name': 'phone_number',
                'Value': '+123456789012'
            },
            {
                'Name': 'email_verified',
                'Value': 'true'
            },
            {
                'Name': 'phone_number_verified',
                'Value': 'true'
            },
        ],
    )
    boto_client_m.admin_get_user.assert_not_called()
    boto_client_m.get_user.assert_not_called()

    assert res == {'data': {'saveUser': None},
                   'errors': [{'locations': [{'column': 3, 'line': 3}],
                               'message': 'some cognito failure',
                               'path': ['saveUser']}]}

    updated_user = graphql_client_admin.post(get_user_query, variables={
        'id': save_user_input_dict['input']['id']
    })
    expected = {'data': {'user': {
        'allowedCognitoActions': ['enable'],
        'avatar': 'https://test.com/someimage.png',
        'cognitoDisplayStatus': 'Disabled / UNCONFIRMED',
        'cognitoEmailVerified': False,
        'cognitoEnabled': False,
        'cognitoPhoneVerified': False,
        'cognitoStatus': 'UNCONFIRMED',
        'email': 'fdsafads@gmail.com',
        'existsInCognito': True,
        'firstName': 'John',
        'lastName': 'Doe',
        'phone': '+11111111111',
        'userAddress': {'city': 'San Francisco',
                        'country': 'USA',
                        'postcode': '79024',
                        'stateRegion': 'California',
                        'street1': 'some street 1',
                        'street2': 'some street 2'},
        'userCards': {'edges': [], 'totalCount': 0},
        'userSubscription': None}}}
    assert updated_user == expected
