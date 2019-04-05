# pylint: disable=invalid-name,unused-argument
from unittest.mock import MagicMock


def patch_boto_for_save_user_mutation(boto_m=None, boto_client_m=None, boto_user_dict=None):
    if not boto_client_m:
        boto_client_m = MagicMock()
    if boto_m:
        boto_m.client.return_value = boto_client_m

    if boto_user_dict is None:
        boto_user_dict = {}
    else:
        for cognito_user in boto_user_dict.values():
            user_attrs = cognito_user.get('UserAttributes', [])
            if isinstance(user_attrs, dict):
                cognito_user['UserAttributes'] = [
                    {
                        'Name': k,
                        'Value': v,
                    } for k, v in user_attrs.items()
                ]

    def _update_attrs_in_boto_dict(key, new_attrs):
        c_user = boto_user_dict.setdefault(key, {})
        existing_attrs = c_user.get('UserAttributes', [])

        attr_dict = {}

        def update_attr_dict(attrs):
            for attr in attrs:
                attr_dict[attr['Name']] = attr

        update_attr_dict(existing_attrs)
        update_attr_dict(new_attrs)

        c_user['UserAttributes'] = [attr for attr in attr_dict.values()]

    def boto_update_user_attributes_m(*args, AccessToken=None, UserAttributes=None, **kwargs):
        _update_attrs_in_boto_dict(AccessToken, UserAttributes)

    def boto_admin_update_user_attributes_m(*args, Username=None, UserAttributes=None, **kwargs):
        _update_attrs_in_boto_dict(Username, UserAttributes)

    def boto_admin_enable_user_m(*args, Username=None, **kwargs):
        cognito_user = boto_user_dict.setdefault(Username, {})
        cognito_user['Enabled'] = True

    def boto_admin_disable_user_m(*args, Username=None, **kwargs):
        cognito_user = boto_user_dict.setdefault(Username, {})
        cognito_user['Enabled'] = False

    def boto_get_user_m(*args, AccessToken=None, **kwargs):
        return boto_user_dict.get(AccessToken, {'UserAttributes': []})

    def boto_admin_get_user_m(*args, Username=None, **kwargs):
        return boto_user_dict.get(Username, {'UserAttributes': []})

    boto_client_m.update_user_attributes.side_effect = boto_update_user_attributes_m
    boto_client_m.admin_update_user_attributes.side_effect = boto_admin_update_user_attributes_m
    boto_client_m.admin_enable_user.side_effect = boto_admin_enable_user_m
    boto_client_m.admin_disable_user.side_effect = boto_admin_disable_user_m
    boto_client_m.get_user.side_effect = boto_get_user_m
    boto_client_m.admin_get_user.side_effect = boto_admin_get_user_m

    return boto_client_m


do_full_cognito_user_sync_query = '''
mutation($input: DoFullCognitoUserSyncInput!) {
  doFullCognitoUserSync(input: $input) {
    successfullyUpdatedCount
    successfullyAddedCount
    exceptionsCount
    notConnectedToCognitoCount
    notFoundInCognitoCount
    cognitoListComplete
    clientMutationId}}
'''


def do_full_cognito_user_sync(
        boto_m,
        cognito_list_users_page_token_1,
        cognito_list_users_page_token_2,
        cognito_list_users_page_1,
        cognito_list_users_page_2,
        cognito_list_users_page_3,
        graphql_client,
):
    boto_client_m = MagicMock()
    boto_m.client.return_value = boto_client_m

    def list_users_mock(*args, **kwargs):
        pagination_token = kwargs.get('PaginationToken')
        if pagination_token == cognito_list_users_page_token_1:
            return cognito_list_users_page_2
        if pagination_token == cognito_list_users_page_token_2:
            return cognito_list_users_page_3
        if pagination_token:
            raise ValueError('unknown pagination token')
        return cognito_list_users_page_1

    boto_client_m.list_users.side_effect = list_users_mock

    return graphql_client.post(do_full_cognito_user_sync_query, variables={
        'input': {
            'clientMutationId': 'some mutation'
        }
    }), boto_client_m
