# pylint: disable=too-many-arguments,attribute-defined-outside-init,protected-access,no-member,too-many-instance-attributes,invalid-name
import json
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest

from core.db.models import (
    db,
    SUBSCRIPTION_SUSPENDED_STATE,
    SUBSCRIPTION_ACTIVE_STATE,
)
from core.db.models.common import STARTED_STATE
from core.db.models.device_token import DeviceToken
from core.db.models.offer_item import OfferItem
from core.db.models.order import Order
from core.db.models.product_offer import ProductOffer
from core.db.models.user import User
from core.dbmethods.user import populate_automatic_username
from tests import patch_boto_for_save_user_mutation

save_user_basic_info = '''
mutation saveUser($input: SaveUserInput!) {
  saveUser(input: $input) {
    user {
      firstName
      lastName
      username
      usernameSetManually}}}
'''

get_user_basic_info = '''
{user {
    firstName
    lastName
    username
    usernameSetManually}}
'''


def test_automatic_username_from_firstname(app, graphql_client, wine_expert):
    weird_firstname = '  This  Name   will   Become_username   '
    expected_basic_info = {'firstName': weird_firstname,
                           'lastName': None,
                           'username': 'this.name.will.become_username',
                           'usernameSetManually': False}

    result = graphql_client.post(save_user_basic_info, variables={
        'input': {
            'firstName': weird_firstname,
        }
    })
    assert result == {'data': {'saveUser': {'user': expected_basic_info}}}

    result = graphql_client.post(get_user_basic_info)
    assert result == {'data': {'user': expected_basic_info}}


def test_automatic_username_from_firstlastname(app, graphql_client, wine_expert):
    weird_firstname = '  This  Name   will   Become_username   '
    weird_lastname = '  wEird  lAStnamE  '
    expected_basic_info = {'firstName': weird_firstname,
                           'lastName': weird_lastname,
                           'username': 'this.name.will.become_username.weird.lastname',
                           'usernameSetManually': False}

    result = graphql_client.post(save_user_basic_info, variables={
        'input': {
            'firstName': weird_firstname,
            'lastName': weird_lastname,
        }
    })
    assert result == {'data': {'saveUser': {'user': expected_basic_info}}}

    result = graphql_client.post(get_user_basic_info)
    assert result == {'data': {'user': expected_basic_info}}


def test_automatic_username_conflict(app, graphql_client, graphql_client3, wine_expert):
    weird_firstname = '  É   Pierre-Richard . -_  Maurice Charles Léopold Defays ?/# & пРИВет  '
    weird_username = 'e.pierre-richard.-_.maurice.charles.leopold.defays.___._.priviet'
    expected_basic_info = {'firstName': weird_firstname,
                           'lastName': None,
                           'username': weird_username,
                           'usernameSetManually': False}

    result = graphql_client3.post(save_user_basic_info, variables={
        'input': {
            'firstName': weird_firstname,
        }
    })
    assert result == {'data': {'saveUser': {'user': expected_basic_info}}}

    result = graphql_client3.post(get_user_basic_info)
    assert result == {'data': {'user': expected_basic_info}}

    result = graphql_client.post(save_user_basic_info, variables={
        'input': {
            'firstName': weird_firstname,
        }
    })
    assert result['data']['saveUser']['user']['username'].startswith(weird_username)

    result = graphql_client.post(get_user_basic_info)
    assert result['data']['user']['username'].startswith(weird_username)


def test_automatic_username_changed(app, graphql_client, wine_expert):
    weird_firstname = '  This  Name   will   Become_username   '
    expected_basic_info = {'firstName': weird_firstname,
                           'lastName': None,
                           'username': 'this.name.will.become_username',
                           'usernameSetManually': False}

    result = graphql_client.post(save_user_basic_info, variables={
        'input': {
            'firstName': weird_firstname,
        }
    })
    assert result == {'data': {'saveUser': {'user': expected_basic_info}}}

    result = graphql_client.post(save_user_basic_info, variables={
        'input': {
            'firstName': weird_firstname + weird_firstname,
        }
    })
    expected_basic_info['firstName'] = weird_firstname + weird_firstname
    expected_basic_info['username'] = 'this.name.will.become_username.this.name.will.become_username'
    assert result == {'data': {'saveUser': {'user': expected_basic_info}}}

    result = graphql_client.post(get_user_basic_info)
    assert result == {'data': {'user': expected_basic_info}}


def test_manual_username(app, graphql_client, graphql_client3, wine_expert):
    weird_firstname = '  This  Name   will   Become_username   '
    manual_username = 'some.manual.username'
    expected_basic_info = {'firstName': weird_firstname,
                           'lastName': None,
                           'username': manual_username,
                           'usernameSetManually': True}

    result = graphql_client.post(save_user_basic_info, variables={
        'input': {
            'firstName': weird_firstname,
            'username': manual_username,
        }
    })
    assert result == {'data': {'saveUser': {'user': expected_basic_info}}}

    result = graphql_client.post(save_user_basic_info, variables={
        'input': {
            'firstName': weird_firstname + weird_firstname,
        }
    })
    expected_basic_info['firstName'] = weird_firstname + weird_firstname
    assert result == {'data': {'saveUser': {'user': expected_basic_info}}}

    result = graphql_client.post(get_user_basic_info)
    assert result == {'data': {'user': expected_basic_info}}


@patch('core.cognito_sync.boto3')
class TestSaveUserMutation:
    @pytest.fixture(autouse=True)
    def init_fixture(
            self,
            client,
            wine_expert,
            api_url,
            save_user_mutation_query,
            save_user_input_dict,
            user_query,
            sample_jwt_payload,
            valid_jwt,
    ):
        self._client = client
        self._api_url = api_url
        self._save_user_mutation_query = save_user_mutation_query
        self._save_user_input_dict = save_user_input_dict
        self._user_query = user_query
        self._cognito_sub = sample_jwt_payload['sub']
        self._valid_jwt = valid_jwt
        self._wine_expert = wine_expert
        self._wine_expert_id = wine_expert.id

    def test_register_new_user(self, boto_m):
        boto_client_m = patch_boto_for_save_user_mutation(boto_m=boto_m, boto_user_dict={
            self._valid_jwt: {
                'UserAttributes': {
                    'email': 'john.doe@test.com',
                    'phone_number': '+123456789012',
                }
            }
        })

        assert not User.query.filter_by(cognito_sub=self._cognito_sub).count()

        result = self._call_save_user_mutation(self._save_user_input_dict)

        result_client_mutation_id = result['data']['saveUser']['clientMutationId']
        input_client_mutation_id = self._save_user_input_dict['input']['clientMutationId']
        assert result_client_mutation_id == input_client_mutation_id

        expected, result = self._produce_expected_and_result(self._save_user_input_dict)
        assert expected == result

        # Check wine expert was assigned
        user = db.session.query(User).filter_by(email=self._save_user_input_dict['input']['email']).first()
        assert user.wine_expert_id == self._wine_expert_id

        boto_client_m.admin_disable_user.assert_not_called()
        boto_client_m.admin_enable_user.assert_not_called()
        boto_client_m.admin_update_user_attributes.assert_not_called()
        boto_client_m.update_user_attributes.assert_not_called()
        boto_client_m.change_password.assert_not_called()
        boto_client_m.admin_get_user.assert_not_called()
        boto_client_m.get_user.assert_called_once_with(AccessToken=self._valid_jwt)

    @patch('core.graphql.schemas.user.send_template_email')
    def test_update_user_details(self, send_mail_m, boto_m):
        # TODO: Refactor all tests of this kind to use User fixture instead of calling 'save user mutation'
        boto_client_m = patch_boto_for_save_user_mutation(boto_m=boto_m)

        assert not User.query.filter_by(cognito_sub=self._cognito_sub).count()

        self._call_save_user_mutation(self._save_user_input_dict)

        update_input_dict = {
            'input': {
                'clientMutationId': 'test_mutation_id2',
                'firstName': 'John (updated)',
                'lastName': 'Doe (updated)',
                'email': 'john.doe.updated@test.com',
                'phone': '+111111111111',
                'oldPassword': '0ldpassword',
                'newPassword': 'n3wpassword',
                'avatar': 'https://test.com/updatedimage.png',
            },
        }
        self._call_save_user_mutation(update_input_dict)

        del update_input_dict['input']['oldPassword']
        del update_input_dict['input']['newPassword']
        self._save_user_input_dict['input'].update(update_input_dict['input'])

        expected, result = self._produce_expected_and_result(self._save_user_input_dict)
        assert expected == result

        boto_client_m.admin_disable_user.assert_not_called()
        boto_client_m.admin_enable_user.assert_not_called()
        boto_client_m.admin_update_user_attributes.assert_not_called()
        boto_client_m.update_user_attributes.assert_called_once_with(
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': 'john.doe.updated@test.com'
                },
                {
                    'Name': 'phone_number',
                    'Value': '+111111111111'
                },
            ],
            AccessToken=self._valid_jwt
        )
        boto_client_m.change_password.assert_called_once_with(
            PreviousPassword='0ldpassword',
            ProposedPassword='n3wpassword',
            AccessToken=self._valid_jwt
        )
        boto_client_m.admin_get_user.assert_not_called()
        boto_client_m.get_user.assert_called_with(AccessToken=self._valid_jwt)
        assert boto_client_m.get_user.call_count == 2

    def test_save_subscription_state(self, boto_m, user):
        boto_client_m = patch_boto_for_save_user_mutation(boto_m=boto_m)

        user_id = user.id

        self._call_save_user_mutation(self._save_user_input_dict)
        boto_client_m.get_user.assert_called_once_with(AccessToken=self._valid_jwt)

        update_input_dict = {
            'input': {
                'userSubscription': {
                    'state': 'suspended',
                },
            },
        }
        result = self._call_save_user_mutation(update_input_dict)
        assert result['data']['saveUser']['user']['userSubscription']['state'] == 'suspended'
        updated_user = User.query.get(user_id)
        assert updated_user.primary_user_subscription.state == SUBSCRIPTION_SUSPENDED_STATE

        update_input_dict['input']['userSubscription']['state'] = 'active'
        result = self._call_save_user_mutation(update_input_dict)
        assert result['data']['saveUser']['user']['userSubscription']['state'] == 'active'
        updated_user = User.query.get(user_id)
        assert updated_user.primary_user_subscription.state == SUBSCRIPTION_ACTIVE_STATE

        boto_client_m.admin_disable_user.assert_not_called()
        boto_client_m.admin_enable_user.assert_not_called()
        boto_client_m.admin_update_user_attributes.assert_not_called()
        boto_client_m.update_user_attributes.assert_called_once()
        boto_client_m.change_password.assert_not_called()
        boto_client_m.admin_get_user.assert_not_called()
        boto_client_m.get_user.assert_called_once()

    @patch('core.graphql.schemas.user.send_template_email')
    def test_update_user_subscription(self, send_mail_m, boto_m):
        boto_client_m = patch_boto_for_save_user_mutation(boto_m=boto_m, boto_user_dict={
            self._valid_jwt: {
                'UserAttributes': {
                    'email': 'john.doe@test.com',
                    'phone_number': '+123456789012',
                }
            }
        })

        assert not User.query.filter_by(cognito_sub=self._cognito_sub).count()

        self._call_save_user_mutation(self._save_user_input_dict)
        boto_client_m.get_user.assert_called_once_with(AccessToken=self._valid_jwt)

        update_input_dict = {
            'input': {
                'userSubscription': {
                    'type': 'white',
                    'bottleQty': 5,
                    'budget': '50.00',
                },
            },
        }
        self._call_save_user_mutation(update_input_dict)

        self._save_user_input_dict['input'].update(update_input_dict['input'])

        expected, result = self._produce_expected_and_result(self._save_user_input_dict)
        assert expected == result

        boto_client_m.admin_disable_user.assert_not_called()
        boto_client_m.admin_enable_user.assert_not_called()
        boto_client_m.admin_update_user_attributes.assert_not_called()
        boto_client_m.update_user_attributes.assert_not_called()
        boto_client_m.change_password.assert_not_called()
        boto_client_m.admin_get_user.assert_not_called()
        boto_client_m.get_user.assert_called_once()

    @patch('core.graphql.schemas.user.send_template_email')
    def test_update_user_address(self, send_mail_m, boto_m):
        boto_client_m = patch_boto_for_save_user_mutation(boto_m=boto_m, boto_user_dict={
            self._valid_jwt: {
                'UserAttributes': {
                    'email': 'john.doe@test.com',
                    'phone_number': '+123456789012',
                }
            }
        })

        assert not User.query.filter_by(cognito_sub=self._cognito_sub).count()

        self._call_save_user_mutation(self._save_user_input_dict)
        boto_client_m.get_user.assert_called_once_with(AccessToken=self._valid_jwt)

        update_input_dict = {
            'input': {
                'userAddress': {
                    'country': 'Ukraine',
                    'stateRegion': 'Lviv Region',
                    'city': "Lviv",
                    'street1': 'Shevchenka',
                    'street2': '',
                    'postcode': '11111',
                },
            },
        }
        self._call_save_user_mutation(update_input_dict)

        self._save_user_input_dict['input'].update(update_input_dict['input'])

        expected, result = self._produce_expected_and_result(self._save_user_input_dict)
        assert expected == result

        boto_client_m.admin_disable_user.assert_not_called()
        boto_client_m.admin_enable_user.assert_not_called()
        boto_client_m.admin_update_user_attributes.assert_not_called()
        boto_client_m.update_user_attributes.assert_not_called()
        boto_client_m.change_password.assert_not_called()
        boto_client_m.admin_get_user.assert_not_called()
        boto_client_m.get_user.assert_called_once()

    @patch('core.graphql.schemas.user.send_template_email')
    def test_update_user_card(self, send_mail_m, boto_m, domain_card_2, domain_card_3):
        boto_client_m = patch_boto_for_save_user_mutation(boto_m=boto_m, boto_user_dict={
            self._valid_jwt: {
                'UserAttributes': {
                    'email': 'john.doe@test.com',
                    'phone_number': '+123456789012',
                }
            }
        })

        assert not User.query.filter_by(cognito_sub=self._cognito_sub).count()

        self._call_save_user_mutation(self._save_user_input_dict)
        boto_client_m.get_user.assert_called_once_with(AccessToken=self._valid_jwt)

        update_input_dict = {
            'input': {
                'userCards': [
                    {
                        'domainCardId': graphene.Node.to_global_id('DomainCard', domain_card_2.id),
                        'preference': 'neutral',
                    },
                    {
                        'domainCardId': graphene.Node.to_global_id('DomainCard', domain_card_3.id),
                        'preference': 'dislike',
                    },
                ],
            },
        }
        self._call_save_user_mutation(update_input_dict)

        self._save_user_input_dict['input']['userCards'][1] = update_input_dict['input']['userCards'][0]
        self._save_user_input_dict['input']['userCards'][2] = update_input_dict['input']['userCards'][1]

        expected, result = self._produce_expected_and_result(self._save_user_input_dict)
        assert expected == result

        boto_client_m.admin_disable_user.assert_not_called()
        boto_client_m.admin_enable_user.assert_not_called()
        boto_client_m.admin_update_user_attributes.assert_not_called()
        boto_client_m.update_user_attributes.assert_not_called()
        boto_client_m.change_password.assert_not_called()
        boto_client_m.admin_get_user.assert_not_called()
        boto_client_m.get_user.assert_called_once()

    @patch('core.graphql.schemas.user.send_template_email')
    def test_update_with_nulls_1(self, send_mail_m, boto_m):
        boto_client_m = patch_boto_for_save_user_mutation(boto_m=boto_m, boto_user_dict={
            self._valid_jwt: {
                'UserAttributes': {
                    'email': 'john.doe@test.com',
                    'phone_number': '+123456789012',
                }
            }
        })

        assert not User.query.filter_by(cognito_sub=self._cognito_sub).count()

        self._call_save_user_mutation(self._save_user_input_dict)
        boto_client_m.get_user.assert_called_once_with(AccessToken=self._valid_jwt)

        update_input_dict = {
            'input': {
                'clientMutationId': None,
                'firstName': None,
                'lastName': None,
                'email': None,
                'phone': None,
                'oldPassword': None,
                'newPassword': None,
                'avatar': None,
                'userAddress': {
                    'country': None,
                    'stateRegion': None,
                    'city': None,
                    'street1': None,
                    'street2': None,
                    'postcode': None,
                },
                'userSubscription': {
                    'type': None,
                    'bottleQty': None,
                    'budget': None,
                },
                'userCards': [],
            },
        }
        self._call_save_user_mutation(update_input_dict)

        expected, result = self._produce_expected_and_result(self._save_user_input_dict)
        assert expected == result

        boto_client_m.admin_disable_user.assert_not_called()
        boto_client_m.admin_enable_user.assert_not_called()
        boto_client_m.admin_update_user_attributes.assert_not_called()
        boto_client_m.update_user_attributes.assert_not_called()
        boto_client_m.change_password.assert_not_called()
        boto_client_m.admin_get_user.assert_not_called()
        boto_client_m.get_user.assert_called_once()

    @patch('core.graphql.schemas.user.send_template_email')
    def test_update_subscription_apply_now(
            self, send_mail_m, boto_m,
            user,
            proposed_to_user_order,
            proposed_to_user_product_offer,
            proposed_to_user_product_offer_2,
            proposed_to_user_offer_item,
            graphql_client
    ):
        patch_boto_for_save_user_mutation(boto_m=boto_m)

        old_order_id = proposed_to_user_order.id
        old_product_offer_id_1 = proposed_to_user_product_offer.id
        old_product_offer_id_2 = proposed_to_user_product_offer_2.id
        old_offer_item_id = proposed_to_user_offer_item.id

        query = '''
        mutation saveUser($input: SaveUserInput!) {
          saveUser(input: $input) {
            clientMutationId
            user {
              userSubscription {
                type
                state
              }
            }
          }
        }'''

        variables = {
            'input': {
                'userSubscription': {
                    'type': 'red',
                    'applyForCurrentOrder': True,
                },
            },
        }

        # Test
        graphql_client.post(query, variables)

        # Check old order and offers are deleted
        assert db.session.query(Order).filter_by(id=old_order_id).first() is None
        assert db.session.query(ProductOffer).filter_by(id=old_product_offer_id_1).first() is None
        assert db.session.query(ProductOffer).filter_by(id=old_product_offer_id_2).first() is None
        assert db.session.query(OfferItem).filter_by(id=old_offer_item_id).first() is None

        orders = db.session.query(Order).all()
        assert len(orders) == 1
        new_order = orders[0]

        assert new_order.state == STARTED_STATE

    @patch('core.graphql.schemas.user.send_template_email')
    def test_update_subscription_apply_for_next_order(
            self, send_mail_m, boto_m,
            user,
            proposed_to_user_order,
            proposed_to_user_product_offer,
            proposed_to_user_product_offer_2,
            proposed_to_user_offer_item,
            graphql_client
    ):
        patch_boto_for_save_user_mutation(boto_m=boto_m)

        old_order_id = proposed_to_user_order.id
        old_product_offer_id_1 = proposed_to_user_product_offer.id
        old_product_offer_id_2 = proposed_to_user_product_offer_2.id
        old_offer_item_id = proposed_to_user_offer_item.id

        query = '''
        mutation saveUser($input: SaveUserInput!) {
          saveUser(input: $input) {
            clientMutationId
            user {
              userSubscription {
                type
                state
              }
            }
          }
        }'''

        variables = {
            'input': {
                'userSubscription': {
                    'type': 'red',
                },
            },
        }

        # Test
        graphql_client.post(query, variables)

        # Check old order and offers are present
        order = db.session.query(Order).filter_by(id=old_order_id).first()
        assert order is not None
        assert db.session.query(ProductOffer).filter_by(id=old_product_offer_id_1).first() is not None
        assert db.session.query(ProductOffer).filter_by(id=old_product_offer_id_2).first() is not None
        assert db.session.query(OfferItem).filter_by(id=old_offer_item_id).first() is not None

        assert order.subscription.type == 'red'

    @patch('core.graphql.schemas.user.send_template_email')
    def test_update_with_nulls_2(self, send_mail_m, boto_m):
        boto_client_m = patch_boto_for_save_user_mutation(boto_m=boto_m, boto_user_dict={
            self._valid_jwt: {
                'UserAttributes': {
                    'email': 'john.doe@test.com',
                    'phone_number': '+123456789012',
                }
            }
        })

        assert not User.query.filter_by(cognito_sub=self._cognito_sub).count()

        self._call_save_user_mutation(self._save_user_input_dict)
        boto_client_m.get_user.assert_called_once_with(AccessToken=self._valid_jwt)

        update_input_dict = {
            'input': {
                'clientMutationId': None,
                'firstName': None,
                'lastName': None,
                'email': None,
                'phone': None,
                'avatar': None,
                'userAddress': None,
                'userSubscription': None,
                'userCards': None,
            },
        }
        self._call_save_user_mutation(update_input_dict)

        expected, result = self._produce_expected_and_result(self._save_user_input_dict)
        assert expected == result

        boto_client_m.admin_disable_user.assert_not_called()
        boto_client_m.admin_enable_user.assert_not_called()
        boto_client_m.admin_update_user_attributes.assert_not_called()
        boto_client_m.update_user_attributes.assert_not_called()
        boto_client_m.change_password.assert_not_called()
        boto_client_m.admin_get_user.assert_not_called()
        boto_client_m.get_user.assert_called_once()

    @patch('core.graphql.schemas.user.send_template_email')
    def test_save_device_token(self, send_mail_m, boto_m):
        boto_client_m = patch_boto_for_save_user_mutation(boto_m=boto_m)

        assert not User.query.filter_by(cognito_sub=self._cognito_sub).count()

        inp = self._save_user_input_dict.copy()
        inp['input']['deviceToken'] = 'device_token'

        # Test
        self._call_save_user_mutation(inp)

        # Check
        token = db.session.query(DeviceToken).first()
        assert token.token == 'device_token'

        boto_client_m.admin_disable_user.assert_not_called()
        boto_client_m.admin_enable_user.assert_not_called()
        boto_client_m.admin_update_user_attributes.assert_not_called()
        boto_client_m.update_user_attributes.assert_not_called()
        boto_client_m.change_password.assert_not_called()
        boto_client_m.admin_get_user.assert_not_called()
        boto_client_m.get_user.assert_called_once_with(AccessToken=self._valid_jwt)

    @patch('core.graphql.schemas.user.send_template_email')
    def test_save_device_token_duplicate(self, send_mail_m, boto_m):
        boto_client_m = patch_boto_for_save_user_mutation(boto_m=boto_m)

        assert not User.query.filter_by(cognito_sub=self._cognito_sub).count()

        inp = self._save_user_input_dict.copy()
        inp['input']['deviceToken'] = 'device_token'

        self._call_save_user_mutation(inp)
        boto_client_m.get_user.assert_called_once_with(AccessToken=self._valid_jwt)

        # Test
        self._call_save_user_mutation({'input': {'deviceToken': 'device_token'}})
        self._call_save_user_mutation({'input': {'deviceToken': 'device_token2'}})

        # Check
        tokens = db.session.query(DeviceToken).all()
        assert [t.token for t in tokens] == ['device_token', 'device_token2']

        boto_client_m.admin_disable_user.assert_not_called()
        boto_client_m.admin_enable_user.assert_not_called()
        boto_client_m.admin_update_user_attributes.assert_not_called()
        boto_client_m.update_user_attributes.assert_not_called()
        boto_client_m.change_password.assert_not_called()
        boto_client_m.admin_get_user.assert_not_called()
        boto_client_m.get_user.assert_called_once()

    def _call_save_user_mutation(self, save_user_input_dict):
        result = self._request_api('application/json', json={
            'query': self._save_user_mutation_query,
            'variables': save_user_input_dict,
        })

        assert 'errors' not in result

        return result

    def _produce_expected_and_result(self, save_user_input_dict):
        saved_result = self._request_api('application/graphql', data=self._user_query)

        save_user_input_dict['input']['registrationFinished'] = True

        save_user_input_dict['input'].pop('clientMutationId', None)
        save_user_input_dict['input']['userSubscription'].pop('state', None)
        save_user_input_dict['input']['userSubscription']['budget'] = Decimal(
            save_user_input_dict['input']['userSubscription']['budget']
        )
        saved_result['data']['user']['userSubscription']['budget'] = Decimal(
            saved_result['data']['user']['userSubscription']['budget']
        )
        saved_result['data']['user']['userCards'] = [
            card['node'] for card in saved_result['data']['user']['userCards']['edges']
        ]
        return save_user_input_dict['input'], saved_result['data']['user']

    def _request_api(self, content_type, **kwargs):
        result = self._client.post(
            self._api_url,
            headers={
                'Authorization': 'JWT ' + self._valid_jwt,
                'Content-Type': content_type,
            },
            **kwargs
        )
        return json.loads(result.data.decode('utf8'))
